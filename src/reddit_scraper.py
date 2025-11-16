"""Reddit scraper for memecoin sentiment analysis using Browser Cash.
- Image analysis has been removed (no image-description agent calls).
- Keeps the same public API as before.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.agent_client import AgentClient
from src.browser_cash_client import BrowserCashClient
from src.config import MEMECOIN_SUBREDDITS
from src.models import Post

# Threading primitives
_json_file_lock = threading.Lock()
_post_id_lock = threading.Lock()
_agent_semaphore = threading.Semaphore(1)
_global_post_id_counter = 1


def _js_result(obj: Any, default: Any) -> Any:
    """Helper to unwrap results returned by execute_script that might be raw or a dict with `result` key."""
    if isinstance(obj, dict) and "result" in obj:
        return obj["result"]
    return obj if obj is not None else default


class RedditScraper:
    def __init__(self, screenshot_dir: str = "screenshots") -> None:
        self.client = BrowserCashClient()
        self.agent_client = AgentClient()
        self.subreddits = MEMECOIN_SUBREDDITS
        self.screenshot_dir = screenshot_dir
        os.makedirs(screenshot_dir, exist_ok=True)

        self.posts_dict: Dict[int, Post] = {}
        self.lock = threading.Lock()
        self.week_ago = datetime.now() - timedelta(days=7)

    # ----------------- small helpers -----------------
    def _parse_number(self, text: str) -> int:
        if not text:
            return 0
        t = text.strip().lower()
        m = re.search(r"([\d.]+)\s*([km]?)", t)
        if not m:
            m2 = re.search(r"\d+", t)
            return int(m2.group(0)) if m2 else 0
        num = float(m.group(1))
        sfx = m.group(2)
        if sfx == "k":
            return int(num * 1_000)
        if sfx == "m":
            return int(num * 1_000_000)
        return int(num)

    def _is_within_last_week(self, post_age: str) -> bool:
        if not post_age:
            return True
        s = post_age.lower().strip()
        # obvious exclusions
        if re.search(r"(month|months|mo\.?|year|years|yr\.?|y\.?)\s*ago", s):
            return False
        w = re.search(r"(\d+)\s*(week|weeks|wk\.?|w\.?)\s*ago", s)
        if w:
            return int(w.group(1)) <= 1
        d = re.search(r"(\d+)\s*(day|days|d\.?)\s*ago", s)
        if d:
            return int(d.group(1)) < 7
        # hours/minutes/just now
        return True

    # ----------------- navigation -----------------
    def navigate_to_subreddit(self, subreddit: str, sort: str = "new", refresh_on_first: bool = False) -> Dict[str, Any]:
        """Navigate to subreddit once - optionally refresh to bypass bot detection."""
        url = f"https://www.reddit.com/r/{subreddit}/{sort}/"
        print(f"  🌐 Navigating to r/{subreddit}...")
        result = self.client.navigate(url, wait_time=3) or {}
        time.sleep(1)

        # Refresh page on first visit to bypass bot detection
        if refresh_on_first:
            print(f"  Refreshing page to bypass bot detection...")
            self.client.navigate(url, wait_time=2)
            time.sleep(1)

        return result

    # ----------------- scraping posts -----------------
    def scrape_posts(self, subreddit: str, limit: int = 25) -> List[Post]:
        script = f"""
        (function() {{
            const posts = [];
            const els = document.querySelectorAll('shreddit-post');
            for (let i = 0; i < Math.min({limit}, els.length); i++) {{
                const p = els[i];
                const title = p.getAttribute('post-title') || '';
                const score = p.getAttribute('score') || '0';
                const commentCount = p.getAttribute('comment-count') || '0';
                const ts = p.getAttribute('created-timestamp') || '';
                const author = p.getAttribute('author') || '';
                const permalink = p.getAttribute('permalink') || '';
                const postType = p.getAttribute('post-type') || 'text';
                let url = '';
                if (permalink) url = permalink.startsWith('http') ? permalink : ('https://www.reddit.com' + permalink);
                let titleText = title;
                if (!titleText) {{
                    const t = p.querySelector('a[slot="title"]');
                    titleText = t ? t.textContent.trim() : '';
                }}
                let body = '';
                const tb = p.querySelector('shreddit-post-text-body');
                if (tb) {{
                    const d = tb.querySelector('.md, [class*="feed-card-text-preview"], p');
                    if (d) body = d.textContent.trim();
                }}
                let age = '';
                const tg = p.querySelector('faceplate-timeago time');
                if (tg) age = tg.textContent.trim();
                if (titleText && titleText.length > 3) {{
                    posts.push({{
                        title: titleText,
                        content: body,
                        score: score,
                        comments: commentCount,
                        timestamp: ts,
                        postAge: age,
                        author: author ? ('u/' + author) : '',
                        url: url,
                        postType: postType
                    }});
                }}
            }}
            return posts;
        }})();
        """
        try:
            res = self.client.execute_script(script, retries=2)
            raw_posts = _js_result(res, [])
            if not isinstance(raw_posts, list):
                raw_posts = []
            posts: List[Post] = []
            for rp in raw_posts:
                score_text = str(rp.get("score", "0"))
                upvotes = self._parse_number(score_text)
                comments_text = str(rp.get("comments", "0"))
                comment_count = self._parse_number(comments_text)
                global _global_post_id_counter
                with _post_id_lock:
                    pid = _global_post_id_counter
                    _global_post_id_counter += 1
                post = Post(
                    id=pid,
                    source=f"r/{subreddit}",
                    platform="reddit",
                    title=rp.get("title"),
                    content=rp.get("content"),
                    author=rp.get("author"),
                    timestamp=rp.get("timestamp"),
                    post_age=rp.get("postAge"),
                    upvotes_likes=upvotes,
                    comment_count=comment_count,
                    link=rp.get("url"),
                    post_type=rp.get("postType", "text"),
                )
                self.posts_dict[post.id] = post
                posts.append(post)
                # No image analysis here; only token identification
                if (post.title or post.content) and not post.token_name:
                    self._start_token_identification_async(post)
            print(f"Scraped {len(posts)} posts")
            return posts
        except Exception as e:
            print(f"ERROR: Error scraping posts: {e}")
            return []

    # ----------------- token detection -----------------
    def _extract_token_from_title(self, title: str) -> Optional[str]:
        if not title:
            return None
        m = re.search(r"\$([A-Z0-9]{2,5})\b", title)
        if m:
            token = m.group(1)
            if token not in {"THE", "THIS", "THAT", "WITH", "FROM", "HAVE", "HERE", "THERE"}:
                return token
        return None

    def _start_token_identification_async(self, post: Post) -> None:
        def run_agent() -> None:
            quick = self._extract_token_from_title(post.title or "")
            if quick:
                with self.lock:
                    post.token_name = quick
                    self._update_post_in_json(post)
                return
            _agent_semaphore.acquire()
            try:
                text = (post.title or "") + " " + (post.content or "")
                if post.comments:
                    text += " " + " ".join(post.comments[:5])
                try:
                    token_name = self.agent_client.identify_token_name(text)
                except Exception:
                    token_name = None
                if token_name and token_name.lower() != "unknown":
                    with self.lock:
                        post.token_name = token_name
                        self._update_post_in_json(post)
            finally:
                _agent_semaphore.release()
        threading.Thread(target=run_agent, daemon=True).start()

    # ----------------- comments -----------------
    def scrape_comments(self, post_url: str, limit: int = 50) -> List[str]:
        """Scrape comments from a post.
        
        Args:
            post_url: URL of the post
            limit: Maximum number of comments to scrape
            
        Returns:
            List of comment texts
        """
        try:
            self.client.navigate(post_url, wait_time=3)
            
            # Poll for comments: wait 1s, check, repeat until comments found or longer timeout
            # If we know the post has comments (comment_count >= 1), wait longer
            max_wait_time = 10  # Increased from 7 to 10 seconds for better reliability
            check_interval = 1  # Check every 1 second
            waited_so_far = 0
            comments_found = False
            
            while waited_so_far < max_wait_time and not comments_found:
                print(f"   Waiting {check_interval}s for comments to load... (total: {waited_so_far + check_interval}s)")
                time.sleep(check_interval)
                waited_so_far += check_interval
                
                # Check if comments are present
                try:
                    check_script = """
                    (function() {
                        const commentElements = document.querySelectorAll('shreddit-comment');
                        return commentElements.length > 0;
                    })();
                    """
                    result = self.client.execute_script(check_script, retries=1)
                    has_comments = result if isinstance(result, bool) else result.get("result", False) if isinstance(result, dict) else False
                    
                    if has_comments:
                        print(f"   Comments found after {waited_so_far}s")
                        comments_found = True
                        break
                except Exception:
                    # If check fails, continue waiting
                    pass
            
            if not comments_found:
                print(f"  WARNING: No comments found after {waited_so_far}s, proceeding anyway...")
            
            # Scroll to load more comments
            for i in range(6):  # Scroll 6 times to load more comments
                self.client.execute_script(
                    "window.scrollBy(0, 1000); return true;", retries=1
                )
                time.sleep(0.7)
            
            # Extract comments with improved selectors
            # Playwright's page.evaluate() wraps code in a function, so we need to return the value
            # Using function expression syntax that Playwright can handle
            extract = f"""
            (function() {{
                const comments = [];
                const commentElements = document.querySelectorAll('shreddit-comment');
                console.log('Found ' + commentElements.length + ' comment elements');
                
                for (let i = 0; i < Math.min({limit}, commentElements.length); i++) {{
                    const comment = commentElements[i];
                    let text = '';
                    
                    const selectors = [
                        'shreddit-comment-body',
                        '[slot="comment-body"]',
                        '[slot="comment"]',
                        '[id*="-comment-rtjson-content"]',
                        'faceplate-tracker[slot="comment-body"]',
                        '.md',
                        'p',
                        'div[data-testid="comment"]',
                        'article',
                        'div[class*="comment"]',
                        'div[class*="Comment"]'
                    ];
                    
                    for (const selector of selectors) {{
                        const content = comment.querySelector(selector);
                        if (content) {{
                            text = content.textContent.trim();
                            text = text.replace(/reply|share|report|give award|permalink|embed|save|parent|context|level \\d+/gi, '').trim();
                            if (text && text.length > 10) {{
                                break;
                            }}
                        }}
                    }}
                    
                    if (!text || text.length <= 10) {{
                        text = comment.textContent.trim();
                        text = text.replace(/reply|share|report|give award|permalink|embed|save|parent|context|level \\d+|\\d+ (points|point)|\\d+ (minutes|hours|days|weeks|months|years) ago/gi, '');
                        text = text.replace(/\\n\\s*\\n/g, ' ').replace(/\\s+/g, ' ').trim();
                    }}
                    
                    if (text && text.length > 10 && !text.match(/^(reply|share|report|permalink|embed|save)$/i)) {{
                        comments.push(text);
                    }}
                }}
                
                console.log('Extracted ' + comments.length + ' comments');
                return comments;
            }})()
            """
            
            # execute_script now has retry logic for execution context errors
            result = self.client.execute_script(extract, retries=2)
            comments = result if isinstance(result, list) else result.get("result", []) if isinstance(result, dict) else []
            
            if not comments:
                # Check how many comment elements exist on the page
                check_count_script = "document.querySelectorAll('shreddit-comment').length;"
                count_result = self.client.execute_script(check_count_script, retries=1)
                element_count = count_result if isinstance(count_result, int) else count_result.get("result", 0) if isinstance(count_result, dict) else 0
                print(f"  WARNING: No comments extracted despite {element_count} comment elements found on page")
            
            if comments:
                print(f"   Extracted {len(comments)} comments")
            
            return comments[:limit] if comments else []
        except Exception as e:
            error_msg = str(e)
            if "Execution context was destroyed" in error_msg:
                print(f"WARNING: Error scraping comments: Page navigated during execution. Skipping comments for this post.")
            else:
                print(f"WARNING: Error scraping comments: {e}")
            return []

    # ----------------- persistence -----------------
    def _update_post_in_json(self, post: Post) -> None:
        try:
            # Use the coin-ed/scrapper_and_analysis folder path
            output_file = os.path.join(os.getcwd(), "coin-ed", "scrapper_and_analysis", "scraped_posts.json")
            with _json_file_lock:
                data: List[Dict[str, Any]] = []
                if os.path.exists(output_file):
                    try:
                        with open(output_file, "r", encoding="utf-8") as f:
                            s = f.read().strip()
                            if s:
                                data = json.loads(s)
                    except Exception:
                        data = []
                updated = False
                for i, p in enumerate(data):
                    if p.get("id") == post.id:
                        data[i] = post.to_dict()
                        updated = True
                        break
                if not updated:
                    data.append(post.to_dict())

                # Ensure directory exists
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"  WARNING: Failed to update JSON for post {post.id}: {e}")

    def _save_json_incremental(self, posts: List[Post], output_file: str) -> None:
        try:
            # Ensure we use the coin-ed/scrapper_and_analysis folder
            if not os.path.isabs(output_file):
                output_file = os.path.join(os.getcwd(), "coin-ed", "scrapper_and_analysis", "scraped_posts.json")

            with _json_file_lock:
                existing: List[Dict[str, Any]] = []
                if os.path.exists(output_file):
                    try:
                        with open(output_file, "r", encoding="utf-8") as f:
                            s = f.read().strip()
                            if s:
                                existing = json.loads(s)
                    except Exception:
                        existing = []
                by_key: Dict[tuple, Dict[str, Any]] = {}
                for p in existing:
                    key = (p.get("source"), p.get("link"))
                    if key not in by_key:
                        by_key[key] = p
                for p in [po.to_dict() for po in posts]:
                    key = (p.get("source"), p.get("link"))
                    if key not in by_key:
                        by_key[key] = p
                    else:
                        by_key[key].update(p)
                out = list(by_key.values())
                out.sort(key=lambda x: (x.get("source", ""), x.get("id", 0)))

                # Ensure directory exists
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(out, f, indent=2, ensure_ascii=False)
                print(f"  💾 Saved {len(out)} total posts to {output_file}")
        except Exception as e:
            print(f"WARNING: Error saving JSON: {e}")

    def to_json(self, posts: List[Post], output_file: str = "scrapper_and_analysis/scraped_posts.json") -> str:
        # Ensure we use the coin-ed/scrapper_and_analysis folder
        if not os.path.isabs(output_file):
            output_file = os.path.join(os.getcwd(), "coin-ed", "scrapper_and_analysis", "scraped_posts.json")

        with _json_file_lock:
            existing: List[Dict[str, Any]] = []
            if os.path.exists(output_file):
                try:
                    with open(output_file, "r", encoding="utf-8") as f:
                        s = f.read().strip()
                        if s:
                            existing = json.loads(s)
                except Exception:
                    existing = []
            by_key: Dict[tuple, Dict[str, Any]] = {}
            for p in existing:
                key = (p.get("source"), p.get("link"))
                if key not in by_key:
                    by_key[key] = p
            for p in [po.to_dict() for po in posts]:
                key = (p.get("source"), p.get("link"))
                if key not in by_key:
                    by_key[key] = p
                else:
                    by_key[key].update(p)
            out = list(by_key.values())
            out.sort(key=lambda x: (x.get("source", ""), x.get("id", 0)))

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            s = json.dumps(out, indent=2, ensure_ascii=False)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(s)
        print(f"💾 Saved {len(out)} total posts to {output_file} (merged with existing)")
        return s

    # ----------------- high-level flows -----------------
    def take_screenshot(self, post: Post) -> Optional[str]:
        try:
            if not self.client.page:
                return None
            fp = os.path.join(self.screenshot_dir, f"post_{post.id}_{post.source.replace('/', '_')}.png")
            self.client.page.screenshot(path=fp, full_page=False)
            return fp
        except Exception:
            return None

    def scrape_subreddit(
        self,
        subreddit: str,
        limit: int = 25,
        scrape_comments: bool = True,
        take_screenshots: bool = False,
        is_first: bool = False,
        max_duration_seconds: int = 180,  # 3 minutes max

    ) -> List[Post]:
        """Scrape a subreddit with a time limit to avoid running indefinitely."""
        print(f"\n🔍 Scraping r/{subreddit} (max {max_duration_seconds}s)...")
        start_time = time.time()
        all_posts: List[Post] = []

        # Navigate once at the start - refresh on first subreddit to bypass bot detection
        self.navigate_to_subreddit(subreddit, sort="new", refresh_on_first=is_first)
        time.sleep(1)

        seen_links = set()
        min_posts_required = 5
        skip_threshold = 10
        page_num = 1

        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= max_duration_seconds:
                print(f"   Time limit reached ({elapsed:.1f}s), stopping scrape for r/{subreddit}")
                break

            print(f"  📄 Scraping page {page_num}... (elapsed: {elapsed:.1f}s)")
            page_posts = self.scrape_posts(subreddit, limit)

            if not page_posts and len(all_posts) >= min_posts_required:
                break

            consecutive_skips = 0
            new_posts_this_page = 0

            for post in page_posts:
                # Check timeout again
                if time.time() - start_time >= max_duration_seconds:
                    print(f"   Time limit reached during post processing")
                    break

                if post.link and post.link in seen_links:
                    consecutive_skips += 1
                    if consecutive_skips >= skip_threshold:
                        break
                    continue

                if post.post_age and not self._is_within_last_week(post.post_age):
                    consecutive_skips += 1
                    if consecutive_skips >= skip_threshold:
                        break
                    continue

                if scrape_comments and post.link:
                    # Always scrape comments if post has a link
                    # If comment_count >= 1, we know there are comments, so wait longer
                    has_comments_indicator = post.comment_count >= 1
                    if has_comments_indicator:
                        print(f"   Scraping comments for post {post.id} (has {post.comment_count} comments, will wait longer)...")
                    else:
                        print(f"   Scraping comments for post {post.id}...")
                    
                    comments = self.scrape_comments(post.link, limit=50)

                    # Always save the post, even if no comments found
                    post.comments = comments if comments else []
                    post.comment_count = len(comments) if comments else 0
                    seen_links.add(post.link)
                    all_posts.append(post)
                    new_posts_this_page += 1
                    self._update_post_in_json(post)
                    
                    # Log if we expected comments but didn't get them
                    if has_comments_indicator and not comments:
                        print(f"  WARNING: Post {post.id} had {post.comment_count} comments indicated but none were extracted")

                    # Retry token identification with comments if we didn't find token before
                    if not post.token_name and (post.title or post.content):
                        self._start_token_identification_async(post)

                    # Navigate back to listing after scraping comments
                    # This is needed because we navigated to the post detail page
                    try:
                        listing_url = f"https://www.reddit.com/r/{subreddit}/new/"
                        print(f"    Returning to listing...")
                        self.client.navigate(listing_url, wait_time=1)
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"  WARNING: Error navigating back: {e}")
                else:
                    # Post has no link or comments disabled, still add it
                    if post.link:
                        seen_links.add(post.link)
                    all_posts.append(post)
                    new_posts_this_page += 1
                    self._update_post_in_json(post)

            if len(all_posts) >= min_posts_required:
                print(f"   Reached minimum {min_posts_required} posts")
                break

            if new_posts_this_page == 0:
                # Scroll to get more posts
                try:
                    for _ in range(3):  # Reduced from 5 to 3
                        self.client.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1)
                except Exception:
                    break
                page_num += 1
            else:
                try:
                    for _ in range(3):
                        self.client.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1)
                except Exception:
                    break
                page_num += 1

        elapsed_total = time.time() - start_time
        print(f"   Scraped {len(all_posts)} posts from r/{subreddit} in {elapsed_total:.1f}s")

        if take_screenshots:
            for p in all_posts:
                self.take_screenshot(p)
        return all_posts

    def scrape_all_subreddits(
        self,
        limit_per_subreddit: int = 25,
        scrape_comments: bool = True,
        take_screenshots: bool = False,
        output_file: str = "scrapper_and_analysis/scraped_posts.json",
        max_total_duration: int = 180,  # 3 minutes global timeout
    ) -> List[Post]:
        """Scrape all subreddits with a global 3-minute timeout."""
        all_posts: List[Post] = []
        start_time = time.time()

        try:
            if self.client.session_id:
                try:
                    self.client.stop_session()
                except Exception:
                    pass
            self.client.start_session()

            for idx, subreddit in enumerate(self.subreddits):
                elapsed = time.time() - start_time
                remaining = max_total_duration - elapsed

                if remaining <= 10:  # Need at least 10s to scrape
                    print(f"\n Global timeout approaching ({elapsed:.1f}s elapsed), stopping")
                    break

                try:
                    # Give each subreddit a portion of remaining time
                    subreddit_timeout = min(remaining - 5, 60)  # Max 60s per subreddit

                    posts = self.scrape_subreddit(
                        subreddit,
                        limit_per_subreddit,
                        scrape_comments,
                        take_screenshots,
                        is_first=(idx == 0),
                        max_duration_seconds=int(subreddit_timeout),
                    )
                    all_posts.extend(posts)
                    self._save_json_incremental(all_posts, output_file)
                    time.sleep(1)
                except Exception as e:
                    print(f"ERROR: Error scraping r/{subreddit}: {e}")
                    continue

            total_elapsed = time.time() - start_time
            print(f"\n Total posts scraped: {len(all_posts)} in {total_elapsed:.1f}s")

            # Final save
            self._save_json_incremental(all_posts, output_file)

            # Trigger frontend update after scraping
            print("\n Triggering frontend update...")
            self._trigger_frontend_update()

        except Exception as e:
            print(f"ERROR: Error in scrape_all_subreddits: {e}")
        finally:
            try:
                if self.client.session_id:
                    self.client.stop_session()
                    print(" Browser session closed")
            except Exception as e:
                print(f"WARNING: Error closing session: {e}")
        return all_posts

    def _trigger_frontend_update(self) -> None:
        """Run sentiment analysis and trigger frontend data reload."""
        try:
            import subprocess
            import sys

            # Run sentiment analysis
            print("   Running sentiment analysis...")
            sentiment_script = os.path.join(os.getcwd(), "scrapper_and_analysis", "sentiment.py")
            if os.path.exists(sentiment_script):
                result = subprocess.run(
                    [sys.executable, sentiment_script],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    print("   Sentiment analysis complete")
                else:
                    print(f"  WARNING: Sentiment analysis failed: {result.stderr}")
            else:
                print(f"  WARNING: Sentiment script not found at {sentiment_script}")

            # Run convert script to update coin-data.json
            print("   Converting data for frontend...")
            convert_script = os.path.join(os.getcwd(), "scrapper_and_analysis", "convert_to_coin_data.py")
            if os.path.exists(convert_script):
                result = subprocess.run(
                    [sys.executable, convert_script],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    print("   Frontend data updated")
                else:
                    print(f"  WARNING: Convert script failed: {result.stderr}")
            else:
                print(f"  WARNING: Convert script not found at {convert_script}")

        except Exception as e:
            print(f"  WARNING: Error triggering frontend update: {e}")


def main() -> None:
    print(" Starting Reddit Memecoin Scraper...")
    print(f"📋 Monitoring {len(MEMECOIN_SUBREDDITS)} subreddits\n")
    scraper = RedditScraper()
    posts = scraper.scrape_all_subreddits(limit_per_subreddit=10, scrape_comments=True, take_screenshots=False)
    scraper.to_json(posts)
    print("\nSCRAPE COMPLETE")


if __name__ == "__main__":
    main()
