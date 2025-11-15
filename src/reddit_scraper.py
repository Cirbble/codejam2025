"""Reddit scraper for memecoin sentiment analysis using Browser Cash."""
import time
import json
import os
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.browser_cash_client import BrowserCashClient
from src.agent_client import AgentClient
from src.config import REDDIT_SUBREDDITS
from src.models import Post

# Global lock for thread-safe JSON file updates across all scraper instances
_json_file_lock = threading.Lock()


class RedditScraper:
    """Scraper for Reddit subreddits using Browser Cash automation."""
    
    def __init__(self):
        """Initialize the Reddit scraper."""
        self.client = BrowserCashClient()
        self.agent_client = AgentClient()
        self.subreddits = REDDIT_SUBREDDITS
        self.post_id_counter = 1
        
        # Store posts by ID for async updates
        self.posts_dict: Dict[int, Post] = {}
        self.lock = threading.Lock()  # For thread-safe updates
        
        # Calculate cutoff time (1 week ago)
        self.week_ago = datetime.now() - timedelta(days=7)
        self.week_ago_timestamp = int(self.week_ago.timestamp() * 1000)  # Unix timestamp in milliseconds
    
    def navigate_to_subreddit(self, subreddit: str, sort: str = "hot") -> None:
        """Navigate to a Reddit subreddit.
        
        Args:
            subreddit: Name of the subreddit (without r/)
            sort: Sort order - "hot", "new", "top", "rising"
        """
        url = f"https://www.reddit.com/r/{subreddit}/{sort}/"
        # Add delay before navigation to avoid rate limiting
        time.sleep(1)
        self.client.navigate(url, wait_time=5, retries=3)
    
    def navigate_to_subreddit_new(self, subreddit: str) -> None:
        """Navigate to a Reddit subreddit's /new page.
        
        Args:
            subreddit: Name of the subreddit (without r/)
        """
        self.navigate_to_subreddit(subreddit, sort="new")
    
    def scroll_to_load_more(self) -> None:
        """Scroll down to load more posts."""
        script = """
        window.scrollTo(0, document.body.scrollHeight);
        """
        self.client.execute_script(script)
        time.sleep(2)  # Wait for content to load
    
    def is_within_last_week(self, timestamp_str: Optional[str]) -> bool:
        """Check if a post timestamp is within the last week.
        
        Args:
            timestamp_str: Timestamp string from Reddit (Unix timestamp in milliseconds)
            
        Returns:
            True if post is within last week, False otherwise
        """
        if not timestamp_str:
            return True  # If no timestamp, assume it's recent
        
        try:
            # Reddit timestamps are Unix timestamps in milliseconds
            post_timestamp = int(timestamp_str)
            return post_timestamp >= self.week_ago_timestamp
        except (ValueError, TypeError):
            # If we can't parse, assume it's recent to be safe
            return True
    
    def scrape_posts(self, subreddit: str, limit: int = 25) -> List[Post]:
        """Scrape posts from the current Reddit page.
        
        Args:
            subreddit: Name of the subreddit
            limit: Maximum number of posts to scrape
            
        Returns:
            List of Post objects
        """
        script = f"""
        (function() {{
            const posts = [];
            const postElements = document.querySelectorAll('shreddit-post');
            
            console.log('Found ' + postElements.length + ' shreddit-post elements');
            
            for (let i = 0; i < Math.min({limit}, postElements.length); i++) {{
                const post = postElements[i];
                
                // Get data from attributes (most reliable)
                const title = post.getAttribute('post-title') || '';
                const score = post.getAttribute('score') || '0';
                const commentCount = post.getAttribute('comment-count') || '0';
                const timestamp = post.getAttribute('created-timestamp') || '';
                const author = post.getAttribute('author') || '';
                const permalink = post.getAttribute('permalink') || '';
                const postType = post.getAttribute('post-type') || 'text';
                
                // Build full URL
                let postUrl = '';
                if (permalink) {{
                    postUrl = permalink.startsWith('http') ? permalink : 'https://www.reddit.com' + permalink;
                }}
                
                // Get title from slot if attribute missing
                let titleText = title;
                if (!titleText) {{
                    const titleSlot = post.querySelector('a[slot="title"]');
                    titleText = titleSlot ? titleSlot.textContent.trim() : '';
                }}
                
                // Get post content from text-body slot
                let content = '';
                const textBody = post.querySelector('shreddit-post-text-body');
                if (textBody) {{
                    const contentDiv = textBody.querySelector('.md, [class*="feed-card-text-preview"], p');
                    if (contentDiv) {{
                        content = contentDiv.textContent.trim();
                    }}
                }}
                
                // Extract post age (e.g., "2 hours ago", "3 days ago")
                let postAge = '';
                // Try faceplate-timeago element (Reddit's time component)
                const timeago = post.querySelector('faceplate-timeago');
                if (timeago) {{
                    postAge = timeago.getAttribute('title') || timeago.textContent.trim();
                }}
                // Fallback: look for time element
                if (!postAge) {{
                    const timeEl = post.querySelector('time');
                    if (timeEl) {{
                        postAge = timeEl.getAttribute('title') || timeEl.textContent.trim();
                    }}
                }}
                // Fallback: look for relative time text in common locations
                if (!postAge) {{
                    const metadata = post.querySelector('[slot="meta"], .metadata, [class*="metadata"]');
                    if (metadata) {{
                        const timeText = metadata.textContent || '';
                        // Look for patterns like "2h", "3d", "2 hours ago", etc.
                        const ageMatch = timeText.match(/(\d+\s*(?:second|minute|hour|day|week|month|year)s?\s*ago|\d+[hdwmy])/i);
                        if (ageMatch) {{
                            postAge = ageMatch[0];
                        }}
                    }}
                }}
                
                // Parse numbers
                const upvotes = parseInt(score) || 0;
                const comments = parseInt(commentCount) || 0;
                
                if (titleText) {{
                    posts.push({{
                        title: titleText,
                        content: content,
                        author: author,
                        timestamp: timestamp,
                        postAge: postAge,
                        upvotes: upvotes,
                        commentCount: comments,
                        url: postUrl,
                        postType: postType
                    }});
                }}
            }}
            
            return posts;
        }})();
        """
        
        try:
            result = self.client.execute_script(script, retries=2)
            if not result:
                print(f"  ⚠️ No posts scraped from r/{subreddit}")
                return []
            
            posts = []
            for raw_post in result:
                try:
                    upvotes = raw_post.get("upvotes", 0)
                    comment_count = raw_post.get("commentCount", 0)
                    
                    post = Post(
                        id=self.post_id_counter,
                        source=f"r/{subreddit}",
                        platform="reddit",
                        title=raw_post.get("title"),
                        content=raw_post.get("content"),
                        author=raw_post.get("author"),
                        timestamp=raw_post.get("timestamp"),
                        post_age=raw_post.get("postAge") or None,
                        upvotes_likes=upvotes,
                        comment_count=comment_count,
                        link=raw_post.get("url"),
                        post_type=raw_post.get("postType", "text"),
                    )
                    
                    # Store post in dict
                    self.posts_dict[post.id] = post
                    posts.append(post)
                    self.post_id_counter += 1
                    
                except Exception as e:
                    print(f"  ⚠️ Error creating post: {e}")
                    continue
            
            print(f"📊 Scraped {len(posts)} posts from r/{subreddit}")
            return posts
            
        except Exception as e:
            error_msg = str(e)
            if "Execution context was destroyed" in error_msg:
                print(f"❌ Error scraping posts: Page navigated during execution.")
            else:
                print(f"❌ Error scraping posts: {e}")
            return []
    
    def scrape_comments(self, post_url: str, limit: int = 10) -> List[str]:
        """Scrape comments from a Reddit post.
        
        Args:
            post_url: URL of the post
            limit: Maximum number of comments to scrape
            
        Returns:
            List of comment texts
        """
        try:
            self.client.navigate(post_url, wait_time=2)
            time.sleep(2)  # Reduced wait time for comments to load
            
            script = f"""
            (function() {{
                const comments = [];
                // Try multiple selectors for Reddit comments
                let commentElements = document.querySelectorAll('shreddit-comment');
                
                // If no shreddit-comment found, try other selectors
                if (commentElements.length === 0) {{
                    commentElements = document.querySelectorAll('[data-testid="comment"], .Comment, .comment');
                }}
                
                console.log('Found ' + commentElements.length + ' comment elements');
                
                for (let i = 0; i < Math.min({limit}, commentElements.length); i++) {{
                    const comment = commentElements[i];
                    let text = '';
                    
                    // Try multiple ways to extract comment text
                    // Method 1: slot="comment" or rtjson content
                    let commentContent = comment.querySelector('[slot="comment"], [id*="-comment-rtjson-content"]');
                    if (commentContent) {{
                        text = commentContent.textContent.trim();
                    }}
                    
                    // Method 2: .md class (markdown content)
                    if (!text || text.length < 3) {{
                        commentContent = comment.querySelector('.md, [class*="md"]');
                        if (commentContent) {{
                            text = commentContent.textContent.trim();
                        }}
                    }}
                    
                    // Method 3: Direct textContent if it's substantial
                    if (!text || text.length < 3) {{
                        text = comment.textContent.trim();
                        // Filter out very short or navigation text
                        if (text.length < 10 || text.includes('permalink') || text.includes('reply')) {{
                            text = '';
                        }}
                    }}
                    
                    if (text && text.length > 3) {{
                        comments.push(text);
                    }}
                }}
                
                console.log('Extracted ' + comments.length + ' comments');
                return comments;
            }})();
            """
            
            result = self.client.execute_script(script, retries=2)
            comments = result if isinstance(result, list) else result.get("result", []) if isinstance(result, dict) else []
            
            if comments:
                print(f"    💬 Scraped {len(comments)} comments")
            return comments if isinstance(comments, list) else []
            
        except Exception as e:
            print(f"    ⚠️ Error scraping comments: {e}")
            return []
    
    def monitor_subreddit(self, subreddit: str, output_file: str = "scraped_posts.json", check_interval: int = 30):
        """Continuously monitor a subreddit's /new page for new posts.
        
        Args:
            subreddit: Subreddit to monitor (without r/)
            output_file: JSON file to save posts to
            check_interval: Seconds between checks for new posts
        """
        print(f"🔍 Starting monitoring for r/{subreddit}")
        
        # Navigate to /new page
        self.navigate_to_subreddit_new(subreddit)
        
        seen_links = set()  # Track seen post links to avoid duplicates
        
        try:
            while True:
                # Scrape new posts
                posts = self.scrape_posts(subreddit, limit=20)
                
                new_count = 0
                for post in posts:
                    # Check if we've seen this post before
                    if post.link and post.link in seen_links:
                        continue
                    
                    # Mark as seen
                    if post.link:
                        seen_links.add(post.link)
                    
                    # Save to JSON immediately (latest first)
                    self._update_post_in_json(post, output_file)
                    new_count += 1
                
                if new_count > 0:
                    print(f"  📝 Added {new_count} new posts from r/{subreddit}")
                
                # Refresh page to get latest posts
                self.navigate_to_subreddit_new(subreddit)
                
                # Wait before next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print(f"\n⚠️ Stopping monitoring for r/{subreddit}")
        except Exception as e:
            print(f"  ❌ Error monitoring r/{subreddit}: {e}")
            import traceback
            traceback.print_exc()
    
    def scrape_subreddit_historical(self, subreddit: str, pages: int = 5, posts_per_page: int = 25, output_file: str = "scraped_posts.json") -> List[Post]:
        """Scrape historical posts from a subreddit (only last week, stops when older posts found).
        
        Args:
            subreddit: Subreddit to scrape (without r/)
            pages: Maximum number of pages to scrape (will stop early if old posts found)
            posts_per_page: Posts to scrape per page
            output_file: JSON file to save posts to
            
        Returns:
            List of all Post objects scraped
        """
        print(f"\n📊 Scraping r/{subreddit} (last week only)...")
        all_posts = []
        seen_links = set()
        
        # Navigate to subreddit /new page
        self.navigate_to_subreddit(subreddit, sort="new")
        time.sleep(1)  # Reduced wait time
        
        page_num = 0
        while page_num < pages:
            page_num += 1
            print(f"  📄 Page {page_num}...")
            
            # Scrape posts from current page
            posts = self.scrape_posts(subreddit, limit=posts_per_page)
            
            if not posts:
                print(f"    ⚠️ No more posts found, stopping")
                break
            
            # Filter duplicates and check timestamps
            new_posts = []
            found_old_post = False
            
            # First pass: filter posts by timestamp and duplicates
            valid_posts = []
            for post in posts:
                # Check if post is within last week
                if not self.is_within_last_week(post.timestamp):
                    print(f"    ⏹️ Found post older than 1 week, stopping scraping")
                    found_old_post = True
                    break
                
                # Check for duplicates
                if post.link and post.link not in seen_links:
                    seen_links.add(post.link)
                    valid_posts.append(post)
            
            # Second pass: scrape comments (synchronous, fast)
            for post in valid_posts:
                # Scrape comments for this post
                if post.link:
                    print(f"    💬 Scraping comments for: {post.title[:50] if post.title else 'post'}...")
                    comments = self.scrape_comments(post.link, limit=10)
                    post.comments = comments
                    post.comment_count = len(comments)
                    
                    # Navigate back to subreddit /new listing
                    self.navigate_to_subreddit(subreddit, sort="new")
                    time.sleep(1)  # Reduced wait time
                
                new_posts.append(post)
                all_posts.append(post)
                
                # Save immediately (without token - will be added async later)
                self._update_post_in_json(post, output_file)
                
                # Start token identification in background (async)
                self._identify_token_async(post, output_file)
            
            if new_posts:
                print(f"    ✅ Found {len(new_posts)} new posts (total: {len(all_posts)})")
            
            # Stop if we found an old post
            if found_old_post:
                break
            
            # If not last page, scroll to load more
            if page_num < pages:
                self.scroll_to_load_more()
                time.sleep(1)  # Reduced wait time
        
        print(f"  ✅ Scraped {len(all_posts)} total posts from r/{subreddit} (last week)")
        return all_posts
    
    def _identify_token_async(self, post: Post, output_file: str) -> None:
        """Identify token name in background (async) and update JSON when done.
        
        Args:
            post: Post object to identify token for
            output_file: JSON file to update
        """
        def run_token_id():
            try:
                # Combine all text sources for token detection
                post_text_parts = []
                if post.title:
                    post_text_parts.append(post.title)
                if post.content:
                    post_text_parts.append(post.content)
                if post.comments:
                    # Include first few comments (they often mention tokens)
                    comments_text = " ".join(post.comments[:5])  # First 5 comments
                    post_text_parts.append(comments_text)
                
                post_text = " ".join(post_text_parts).strip()
                
                if post_text:
                    token_name = self.agent_client.identify_token_name(post_text)
                    if token_name and token_name.upper() != "UNKNOWN":
                        post.token_name = token_name.upper()
                        print(f"    ✅ Token identified for post {post.id}: {post.token_name}")
                        # Update JSON with token name
                        self._update_post_in_json(post, output_file)
            except Exception as e:
                error_msg = str(e).lower()
                if "limit" not in error_msg and "session" not in error_msg:
                    print(f"    ⚠️ Token identification failed for post {post.id}: {e}")
        
        # Start token identification in background thread
        thread = threading.Thread(target=run_token_id, daemon=True)
        thread.start()
    
    def _update_post_in_json(self, post: Post, output_file: str) -> None:
        """Update JSON file with a new post (thread-safe, appends for oldest first).
        
        Args:
            post: Post object to add/update
            output_file: Path to JSON file
        """
        # Use global lock for file operations across all scraper instances
        with _json_file_lock:
            try:
                # Read existing posts
                all_posts = []
                if os.path.exists(output_file):
                    try:
                        with open(output_file, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                all_posts = json.loads(content)
                            else:
                                all_posts = []
                    except json.JSONDecodeError:
                        all_posts = []
                
                # Check if post already exists (by link)
                updated = False
                for i, p in enumerate(all_posts):
                    if p.get("link") == post.link and post.link:
                        all_posts[i] = post.to_dict()
                        updated = True
                        break
                
                if not updated:
                    # New post - append to end (oldest first, 1, 2, 3...)
                    all_posts.append(post.to_dict())
                
                # Save updated JSON
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_posts, f, indent=2, ensure_ascii=False)
                    
            except Exception as e:
                print(f"  ⚠️ Failed to update JSON for post {post.id}: {e}")
                import traceback
                traceback.print_exc()
