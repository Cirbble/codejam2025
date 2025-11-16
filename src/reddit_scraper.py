"""Reddit scraper for memecoin sentiment analysis using Browser Cash."""
import time
import json
import os
import threading
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.browser_cash_client import BrowserCashClient
from src.config import MEMECOIN_SUBREDDITS
from src.models import Post
from src.agent_client import AgentClient

# Global lock for JSON file operations across all scraper instances
_json_file_lock = threading.Lock()

# Global counter for unique post IDs across all scraper instances
_global_post_id_counter = 1
_post_id_lock = threading.Lock()

# Global semaphore to limit concurrent agent calls across ALL instances
# With 3 parallel scrapers, limit to 1 per instance = 3 total max
_agent_semaphore = threading.Semaphore(1)


class RedditScraper:
    """Scraper for Reddit subreddits using Browser Cash automation."""
    
    def __init__(self, screenshot_dir: str = "screenshots"):
        """Initialize the Reddit scraper.
        
        Args:
            screenshot_dir: Directory to save screenshots
        """
        self.client = BrowserCashClient()
        self.agent_client = AgentClient()
        self.subreddits = MEMECOIN_SUBREDDITS
        self.screenshot_dir = screenshot_dir
        
        # Store posts by ID for async updates
        self.posts_dict: Dict[int, Post] = {}
        self.pending_agents: Dict[int, Dict] = {}  # post_id -> {task_id, type, post}
        self.lock = threading.Lock()  # For thread-safe updates
        
        # Create screenshot directory if it doesn't exist
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Calculate timestamp for 1 week ago
        self.week_ago = datetime.now() - timedelta(days=7)
    
    def _is_within_last_week(self, post_age: str) -> bool:
        """Check if a post is within the last week based on its age string.
        
        Args:
            post_age: String like "2 hours ago", "3 days ago", "8 hr. ago", "20 days ago"
            
        Returns:
            True if post is within last week, False otherwise
        """
        if not post_age:
            return True  # If we can't determine, assume it's recent
        
        post_age_lower = post_age.lower().strip()
        
        # Parse patterns like "X hours ago", "X days ago", etc.
        hour_match = re.search(r'(\d+)\s*(?:hour|hr|h)\s*ago', post_age_lower)
        day_match = re.search(r'(\d+)\s*(?:day|days|d)\s*ago', post_age_lower)
        minute_match = re.search(r'(\d+)\s*(?:minute|min|m)\s*ago', post_age_lower)
        week_match = re.search(r'(\d+)\s*(?:week|weeks|w)\s*ago', post_age_lower)
        month_match = re.search(r'(\d+)\s*(?:month|months)\s*ago', post_age_lower)
        year_match = re.search(r'(\d+)\s*(?:year|years)\s*ago', post_age_lower)
        
        # If it's months or years old, definitely not within last week
        if month_match or year_match:
            return False
        
        # If it's weeks old, check if it's more than 1 week
        if week_match:
            weeks = int(week_match.group(1))
            return weeks == 0  # "0 weeks ago" or "1 week ago" is within last week
        
        # If it's days old, check if it's less than 7 days
        if day_match:
            days = int(day_match.group(1))
            return days < 7
        
        # If it's hours or minutes old, definitely within last week
        if hour_match or minute_match:
            return True
        
        # If we can't parse it, assume it's recent (better to scrape more than less)
        return True
    
    def navigate_to_subreddit(self, subreddit: str, sort: str = "new") -> Dict[str, Any]:
        """Navigate to a specific Reddit subreddit.
        
        Args:
            subreddit: Name of the subreddit (without r/)
            sort: Sort order ("new", "hot", "top")
            
        Returns:
            Navigation result
        """
        url = f"https://www.reddit.com/r/{subreddit}/{sort}/"
        return self.client.navigate(url, wait_time=5)
    
    def scrape_posts(self, subreddit: str, limit: int = 25) -> List[Post]:
        """Scrape posts from the current Reddit page with full details.
        
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
                
                // Get post age from faceplate-timeago
                let postAge = '';
                const timeAgo = post.querySelector('faceplate-timeago time');
                if (timeAgo) {{
                    postAge = timeAgo.textContent.trim();
                }}
                
                if (titleText && titleText.length > 3) {{
                    posts.push({{
                        title: titleText,
                        content: content,
                        score: score,
                        comments: commentCount,
                        timestamp: timestamp,
                        postAge: postAge,
                        author: author ? 'u/' + author : '',
                        url: postUrl,
                        postType: postType
                    }});
                }}
            }}
            
            return posts;
        }})();
        """
        
        try:
            # execute_script now has retry logic for execution context errors
            result = self.client.execute_script(script, retries=2)
            raw_posts = result if isinstance(result, list) else result.get("result", []) if isinstance(result, dict) else []
            
            if not raw_posts:
                print(f"⚠️ No posts found on page (may have navigated during scraping)")
                return []
            
            # Convert to Post objects
            posts = []
            for raw_post in raw_posts:
                # Parse score (handle "1.2k" format)
                score_text = str(raw_post.get("score", "0"))
                upvotes = self._parse_number(score_text)
                
                # Parse comments
                comments_text = str(raw_post.get("comments", "0"))
                comment_count = self._parse_number(comments_text)
                
                # Get unique ID from global counter
                global _global_post_id_counter, _post_id_lock
                with _post_id_lock:
                    post_id = _global_post_id_counter
                    _global_post_id_counter += 1
                
                post = Post(
                    id=post_id,
                    source=f"r/{subreddit}",
                    platform="reddit",
                    title=raw_post.get("title"),
                    content=raw_post.get("content"),
                    author=raw_post.get("author"),
                    timestamp=raw_post.get("timestamp"),
                    post_age=raw_post.get("postAge"),
                    upvotes_likes=upvotes,
                    comment_count=comment_count,
                    link=raw_post.get("url"),
                    post_type=raw_post.get("postType", "text"),
                )
                
                # Store post in dict for async updates
                self.posts_dict[post.id] = post
                posts.append(post)
                
                # Start agent tasks in background (non-blocking)
                if not post.content and post.post_type == "image" and post.link:
                    print(f"  🤖 Starting image description for post {post.id} (background)...")
                    self._start_image_description_async(post)
                
                # Start token identification in background (non-blocking)
                if (post.title or post.content) and not post.token_name:
                    print(f"  🤖 Starting token identification for post {post.id} (background)...")
                    self._start_token_identification_async(post)
            
            print(f"📊 Scraped {len(posts)} posts")
            return posts
        except Exception as e:
            error_msg = str(e)
            if "Execution context was destroyed" in error_msg:
                print(f"❌ Error scraping posts: Page navigated during execution. This can happen if Reddit redirects or the page refreshes.")
            else:
                print(f"❌ Error scraping posts: {e}")
            return []
    
    def _start_image_description_async(self, post: Post) -> None:
        """Start image description agent task in background with queuing."""
        global _agent_semaphore
        
        def run_agent():
            # Acquire semaphore to limit concurrent agent calls
            _agent_semaphore.acquire()
            try:
                image_description = self._extract_text_from_image(post.link)
                with self.lock:
                    if image_description:
                        post.content = image_description
                        print(f"  ✅ Image described for post {post.id}: {image_description[:80]}...")
                        # Update JSON file
                        self._update_post_in_json(post)
                    else:
                        print(f"  ⚠️ No description generated for post {post.id}")
            except Exception as e:
                print(f"  ⚠️ Failed to describe image for post {post.id}: {e}")
            finally:
                # Release semaphore so next queued call can proceed
                _agent_semaphore.release()
        
        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()
    
    def _extract_token_from_title(self, title: str) -> Optional[str]:
        """Extract token name from title if it contains $TOKEN pattern.
        
        Args:
            title: Post title
            
        Returns:
            Token name if found (2-5 uppercase letters after $), None otherwise
        """
        if not title:
            return None
        
        # Pattern: $ followed by 2-5 uppercase letters/numbers
        match = re.search(r'\$([A-Z0-9]{2,5})\b', title)
        if match:
            token = match.group(1)
            # Skip common words that aren't tokens
            skip_words = {"THE", "THIS", "THAT", "WITH", "FROM", "HAVE", "HERE", "THERE"}
            if token not in skip_words:
                return token
        
        return None
    
    def _start_token_identification_async(self, post: Post) -> None:
        """Start token identification agent task in background with queuing."""
        global _agent_semaphore
        
        def run_agent():
            # First, check if title has $TOKEN pattern (fast, no agent call needed)
            if post.title:
                quick_token = self._extract_token_from_title(post.title)
                if quick_token:
                    with self.lock:
                        post.token_name = quick_token
                        print(f"  ✅ Found token in title for post {post.id}: {quick_token}")
                        # Update JSON file
                        self._update_post_in_json(post)
                    return  # Skip agent call
            
            # No $TOKEN in title, use agent
            # Acquire semaphore to limit concurrent agent calls
            _agent_semaphore.acquire()
            try:
                # Combine title, content, and first few comments for better token detection
                post_text = (post.title or "") + " " + (post.content or "")
                if post.comments:
                    # Add first 5 comments to help identify tokens mentioned in comments
                    comments_text = " ".join(post.comments[:5])
                    post_text += " " + comments_text
                
                print(f"  🔍 Identifying token for post {post.id}: {post.title[:50]}...")
                
                # Retry logic for session limit errors
                max_retries = 3
                token_name = None
                for attempt in range(max_retries):
                    try:
                        token_name = self.agent_client.identify_token_name(post_text)
                        break  # Success, exit retry loop
                    except Exception as e:
                        error_str = str(e).lower()
                        if "session limit" in error_str or "limit reached" in error_str:
                            if attempt < max_retries - 1:
                                wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                                print(f"  ⏳ Session limit hit, waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                                time.sleep(wait_time)
                                continue
                            else:
                                print(f"  ⚠️ Session limit reached after {max_retries} attempts for post {post.id}")
                                return
                        else:
                            # Other error, don't retry
                            raise
                
                with self.lock:
                    if token_name and token_name.lower() != "unknown":
                        post.token_name = token_name
                        print(f"  ✅ Identified token for post {post.id}: {token_name}")
                        # Update JSON file
                        self._update_post_in_json(post)
                    else:
                        print(f"  ⚠️ No token identified for post {post.id} (agent returned: {token_name})")
            except Exception as e:
                print(f"  ⚠️ Failed to identify token for post {post.id}: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Release semaphore so next queued call can proceed
                _agent_semaphore.release()
        
        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()
    
    def _update_post_in_json(self, post: Post) -> None:
        """Update a single post in the JSON file (thread-safe)."""
        global _json_file_lock
        try:
            output_file = "scraped_posts.json"
            
            with _json_file_lock:
                all_posts = []
                
                # Try to read existing file
                if os.path.exists(output_file):
                    try:
                        with open(output_file, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                all_posts = json.loads(content)
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"  ⚠️ JSON file corrupted, starting fresh: {e}")
                        all_posts = []
                
                # Find and update the post
                updated = False
                for i, p in enumerate(all_posts):
                    if p.get("id") == post.id:
                        all_posts[i] = post.to_dict()
                        updated = True
                        break
                
                if not updated:
                    # Post not found, append it
                    all_posts.append(post.to_dict())
                
                # Save updated JSON
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_posts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"  ⚠️ Failed to update JSON for post {post.id}: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_text_from_image(self, post_url: str) -> str:
        """Use Agent API to describe what's in an image post.
        Uses the current browser session if available to avoid Reddit blocking.
        
        Args:
            post_url: URL of the post with image
            
        Returns:
            Description of the image content
        """
        try:
            # Try to use current browser session if available
            cdp_url = None
            if self.client.cdp_url:
                cdp_url = self.client.cdp_url
                # Use a prompt that works with the current page context
                prompt = f"On the current page (URL: {post_url}), describe what you see in the image. Focus on: what token/coin is mentioned, any prices or numbers, key text or information. Be concise - maximum 2-3 sentences."
                print(f"     Creating agent task with current session for image description...")
            else:
                # Fallback: navigate to URL (may get blocked)
                prompt = f"Navigate to {post_url} and describe what you see in the image. Focus on: what token/coin is mentioned, any prices or numbers, key text or information. Be concise - maximum 2-3 sentences. If you encounter any errors or cannot access the page, return 'ERROR: Could not access page'."
                print(f"     Creating agent task (new session) for image description...")
            
            try:
                task = self.agent_client.create_task(prompt, step_limit=10, cdp_url=cdp_url)  # Pass CDP URL if available
                print(f"     Task response: {task}")
            except Exception as e:
                print(f"     ❌ Failed to create agent task: {e}")
                return ""
            
            task_id = task.get("taskId") or task.get("id") or task.get("task_id")
            
            if not task_id:
                print(f"     ❌ No task ID found in response: {task}")
                return ""
            
            print(f"     Task ID: {task_id}, polling for status...")
            
            # Wait for completion - Agent tasks can take a while
            import time
            import json
            max_polls = 30  # Max 60 seconds (tasks navigating to URLs can be slow)
            for i in range(max_polls):
                task_status = self.agent_client.get_task(task_id)
                # API uses 'state' not 'status'
                state = task_status.get("state", "").lower() or task_status.get("status", "").lower()
                stopped_at = task_status.get("stoppedAt")
                result = task_status.get("result")
                attempts = task_status.get("attemptsMade", 0)
                
                # Print status every 5 polls to reduce spam
                if i % 5 == 0 or stopped_at or result:
                    print(f"     Poll {i+1}/{max_polls}: State = '{state}', Attempts = {attempts}, Stopped = {bool(stopped_at)}, Has result = {bool(result)}")
                
                # Debug: Print full response structure on first poll and if we see something unexpected
                if i == 0 or (i % 10 == 0 and not stopped_at and not result):
                    print(f"     🔍 Full response structure: {json.dumps(task_status, indent=2, default=str)[:500]}")
                
                # Task is complete if stoppedAt is set or state is completed/done
                # Also check if result exists even if state is still "active" (API might lag)
                if stopped_at or state in ["completed", "done", "success", "finished"] or result:
                    # Extract result - it's a string that may contain the answer at the end
                    final_result = (
                        result or
                        task_status.get("output", "") or 
                        task_status.get("data", {}).get("result", "") or
                        task_status.get("response", "") or
                        task_status.get("data", {}).get("output", "")
                    )
                    
                    if final_result:
                        # For image descriptions, keep the full description text (not just token name)
                        result_str = str(final_result).strip()
                        
                        # Remove JSON-like structures and clean up
                        result_str = re.sub(r"\{.*?'answer'\s*:\s*['\"]", "", result_str)
                        result_str = re.sub(r"['\"].*", "", result_str)
                        result_str = result_str.strip()
                        
                        # Filter out agent internal reasoning (common patterns)
                        # If it starts with "I have evaluated", "I have", "Step", etc., it's likely internal reasoning
                        if re.match(r'^(I have evaluated|I have|Step \d+|I can see that|The task is|I need to)', result_str, re.IGNORECASE):
                            print(f"     ⚠️ Got agent internal reasoning instead of description: {result_str[:100]}...")
                            # Try to extract the actual description after the reasoning
                            # Look for sentences that describe the image
                            sentences = re.split(r'[.!?]\s+', result_str)
                            # Find sentences that don't start with agent reasoning keywords
                            valid_sentences = []
                            skip_keywords = ['i have', 'step', 'the task', 'i need', 'i can see that', 'it appears']
                            for sent in sentences:
                                sent = sent.strip()
                                if len(sent) > 20:  # Must be substantial
                                    # Check if it's not agent reasoning
                                    is_reasoning = any(sent.lower().startswith(kw) for kw in skip_keywords)
                                    if not is_reasoning and not re.match(r'^[A-Z]{2,10}$', sent):  # Not just a token name
                                        valid_sentences.append(sent)
                            
                            if valid_sentences:
                                result_str = '. '.join(valid_sentences[:3])  # Take up to 3 sentences
                                print(f"     ✅ Extracted description from reasoning: {result_str[:100]}...")
                            else:
                                print(f"     ⚠️ Could not extract valid description from reasoning")
                                return ""
                        
                        # If result is just a single token name (like "HEGE"), it's probably wrong
                        # Image descriptions should be longer sentences
                        if len(result_str) < 20 and re.match(r'^[A-Z]{2,10}$', result_str):
                            print(f"     ⚠️ Got token name instead of description: {result_str}")
                            return ""  # Return empty if we only got a token name
                        
                        # Clean up common prefixes that agents add
                        result_str = re.sub(r'^(The image shows|The image contains|I can see|In the image|This image|Image description:)\s*', '', result_str, flags=re.IGNORECASE)
                        result_str = result_str.strip()
                        
                        # If result is too short or looks like just a token, skip it
                        if len(result_str) < 15:
                            print(f"     ⚠️ Description too short, likely invalid: {result_str}")
                            return ""
                        
                        print(f"     ✅ Task completed. Description: {result_str[:100]}...")
                        return result_str
                    
                    # If no result field, check if entire response is the result
                    if not final_result:
                        print(f"     Full task_status keys: {list(task_status.keys())}")
                        # Maybe result is nested deeper
                        if "data" in task_status:
                            print(f"     Data keys: {list(task_status.get('data', {}).keys())}")
                            print(f"     Full data: {json.dumps(task_status.get('data', {}), indent=2, default=str)[:500]}")
                        return ""
                elif state in ["failed", "error"]:
                    failed_reason = task_status.get("failedReason", "")
                    error_msg = task_status.get("error", "") or task_status.get("message", "")
                    
                    # Print failure reason prominently
                    if failed_reason:
                        print(f"     ❌ Task failed: {failed_reason}")
                    elif error_msg:
                        print(f"     ❌ Task failed: {error_msg}")
                    else:
                        print(f"     ❌ Task failed (no reason provided)")
                    
                    # Print full error details for debugging
                    if failed_reason and failed_reason != error_msg:
                        print(f"     🔍 Failed reason: {failed_reason}")
                    if error_msg and error_msg != failed_reason:
                        print(f"     🔍 Error details: {error_msg}")
                    
                    return ""
                elif state in ["active", "running", "pending", "in_progress"] or not stopped_at:
                    # Continue polling - task is still running
                    # But also check if result appeared even though state is active
                    if result:
                        print(f"     ⚠️ Found result but state is '{state}' - extracting anyway")
                        final_result = result or task_status.get("output", "")
                        if final_result:
                            return final_result.strip() if isinstance(final_result, str) else str(final_result).strip()
                    pass
                else:
                    print(f"     ⚠️ Unknown state: {state}, full response keys: {list(task_status.keys())}")
                
                time.sleep(2)
            
            # Check one more time before giving up
            final_check = self.agent_client.get_task(task_id)
            if final_check.get("stoppedAt") or final_check.get("result"):
                result = final_check.get("result") or final_check.get("output", "")
                if result:
                    print(f"     ✅ Task completed on final check. Result: {result[:100]}")
                    return result.strip() if isinstance(result, str) else str(result).strip()
            
            print(f"     ⏱️ Timeout after {max_polls * 2} seconds - task may still be running in background")
            print(f"     💡 Check Browser Cash dashboard for task status: {task_id}")
            return ""
        except Exception as e:
            print(f"  ⚠️ Agent error describing image: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _parse_number(self, text: str) -> int:
        """Parse number from text (handles '1.2k', '5.3m', etc.)."""
        if not text:
            return 0
        text = text.lower().strip()
        # Remove non-numeric except decimal point and k/m
        import re
        match = re.search(r'([\d.]+)\s*([km]?)', text)
        if match:
            num = float(match.group(1))
            suffix = match.group(2)
            if suffix == 'k':
                return int(num * 1000)
            elif suffix == 'm':
                return int(num * 1000000)
            return int(num)
        # Try to extract just numbers
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else 0
    
    def scrape_comments(self, post_url: str, limit: int = 10) -> List[str]:
        """Scrape comments from a post.
        
        Args:
            post_url: URL of the post
            limit: Maximum number of comments to scrape
            
        Returns:
            List of comment texts
        """
        try:
            self.client.navigate(post_url, wait_time=3)
            
            # Wait a bit more for comments to load
            import time
            time.sleep(2)
            
            script = f"""
            (function() {{
                const comments = [];
                // Reddit uses shreddit-comment elements
                const commentElements = document.querySelectorAll('shreddit-comment');
                
                for (let i = 0; i < Math.min({limit}, commentElements.length); i++) {{
                    const comment = commentElements[i];
                    // Comments are in div with slot="comment" or id ending in -comment-rtjson-content
                    const commentContent = comment.querySelector('[slot="comment"], [id*="-comment-rtjson-content"], .md');
                    if (commentContent) {{
                        const text = commentContent.textContent.trim();
                        if (text && text.length > 3) {{
                            comments.push(text);
                        }}
                    }}
                }}
                
                return comments;
            }})();
            """
            
            # execute_script now has retry logic for execution context errors
            result = self.client.execute_script(script, retries=2)
            comments = result if isinstance(result, list) else result.get("result", []) if isinstance(result, dict) else []
            return comments[:limit] if comments else []
        except Exception as e:
            error_msg = str(e)
            if "Execution context was destroyed" in error_msg:
                print(f"⚠️ Error scraping comments: Page navigated during execution. Skipping comments for this post.")
            else:
                print(f"⚠️ Error scraping comments: {e}")
            return []
    
    def take_screenshot(self, post: Post) -> str:
        """Take a screenshot of the current page.
        
        Args:
            post: Post object to associate screenshot with
            
        Returns:
            Path to screenshot file
        """
        try:
            if not self.client.page:
                return None
            
            filename = f"post_{post.id}_{post.source.replace('/', '_')}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            self.client.page.screenshot(path=filepath, full_page=False)
            return filepath
        except Exception as e:
            print(f"⚠️ Error taking screenshot: {e}")
            return None
    
    def scrape_subreddit(self, subreddit: str, limit: int = 25, scrape_comments: bool = True, take_screenshots: bool = False, is_first: bool = False) -> List[Post]:
        """Navigate to a subreddit and scrape posts from the past week.
        
        Args:
            subreddit: Name of the subreddit
            limit: Maximum number of posts per page (not total limit)
            scrape_comments: Whether to scrape comments for each post
            take_screenshots: Whether to take screenshots
            is_first: Whether this is the first subreddit (triggers refresh)
            
        Returns:
            List of Post objects from the past week
        """
        print(f"\n🔍 Scraping r/{subreddit} (past week)...")
        all_posts = []
        page_num = 1
        
        # Navigate to /new page
        self.navigate_to_subreddit(subreddit, sort="new")
        
        if is_first:
            print(f"  ⏳ Waiting 1 second...")
            time.sleep(1)
            print(f"  🔄 Refreshing page...")
            self.client.navigate(f"https://www.reddit.com/r/{subreddit}/new/", wait_time=0)
            print(f"  ⏳ Waiting 2 seconds after refresh...")
            time.sleep(2)
        else:
            time.sleep(3)  # Wait for page to fully load
        
        # Keep scraping pages until we find posts older than a week
        seen_links = set()  # Track seen post links to avoid duplicates
        
        while True:
            print(f"  📄 Scraping page {page_num}...")
            page_posts = self.scrape_posts(subreddit, limit)
            
            if not page_posts:
                print(f"  ⚠️ No posts found on page {page_num}, stopping")
                break
            
            # Check if any post is older than a week and filter duplicates
            found_old_post = False
            new_posts_this_page = 0
            for post in page_posts:
                # Skip duplicates
                if post.link and post.link in seen_links:
                    continue
                
                # Check age
                if post.post_age and not self._is_within_last_week(post.post_age):
                    print(f"  ⏹️ Found post older than 1 week: '{post.post_age}' - stopping")
                    found_old_post = True
                    break
                
                # Add to seen links and all_posts
                if post.link:
                    seen_links.add(post.link)
                all_posts.append(post)
                new_posts_this_page += 1
            
            if found_old_post:
                break
            
            # If no new posts this page, we've seen everything
            if new_posts_this_page == 0:
                print(f"  ✅ No new posts on page {page_num}, stopping")
                break
            
            # Navigate to next page by scrolling and loading more
            print(f"  ⏭️ Loading next page...")
            try:
                # Scroll multiple times to trigger infinite scroll loading
                # Reddit uses infinite scroll, so we need to scroll aggressively
                for scroll_attempt in range(5):
                    self.client.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)  # Wait for new posts to load
                
                # Wait a bit more for Reddit's infinite scroll to load
                time.sleep(3)
                
                # If we got fewer posts than expected, scroll even more aggressively
                if len(page_posts) < limit:
                    print(f"  ⚠️ Only got {len(page_posts)} posts (expected {limit}), scrolling more aggressively...")
                    # Try scrolling more aggressively
                    for _ in range(10):
                        self.client.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1)
                    time.sleep(4)  # Wait longer for more posts to load
            except Exception as e:
                print(f"  ⚠️ Error scrolling: {e}, stopping")
                break
            
            page_num += 1
            
            # Safety limit: don't scrape more than 50 pages
            if page_num > 50:
                print(f"  ⚠️ Reached page limit (50), stopping")
                break
        
        print(f"  ✅ Scraped {len(all_posts)} posts from past week")
        
        # Enhance posts with comments and screenshots
        for post in all_posts:
            # Scrape comments if requested
            if scrape_comments and post.link:
                print(f"  📝 Scraping comments for post {post.id}...")
                comments = self.scrape_comments(post.link, limit=10)
                post.comments = comments
                post.comment_count = len(comments)
                
                # Now that we have comments, try token identification again if it wasn't found
                if not post.token_name and (post.title or post.content):
                    print(f"  🤖 Retrying token identification for post {post.id} with comments...")
                    self._start_token_identification_async(post)
            
            # Take screenshot if requested
            if take_screenshots:
                print(f"  📸 Taking screenshot for post {post.id}...")
                screenshot_path = self.take_screenshot(post)
                if screenshot_path:
                    post.screenshot_path = screenshot_path
        
        return all_posts
    
    def scrape_all_subreddits(self, limit_per_subreddit: int = 25, scrape_comments: bool = True, take_screenshots: bool = False, output_file: str = "scraped_posts.json") -> List[Post]:
        """Scrape posts from all configured subreddits.
        
        Args:
            limit_per_subreddit: Maximum posts per subreddit
            scrape_comments: Whether to scrape comments
            take_screenshots: Whether to take screenshots
            output_file: File to save JSON output (saves in real-time)
            
        Returns:
            Combined list of all Post objects
        """
        all_posts = []
        
        try:
            # Ensure we don't have a stale session
            if self.client.session_id:
                try:
                    self.client.stop_session()
                except:
                    pass
            
            self.client.start_session()
            
            for idx, subreddit in enumerate(self.subreddits):
                try:
                    is_first = (idx == 0)
                    posts = self.scrape_subreddit(subreddit, limit_per_subreddit, scrape_comments, take_screenshots, is_first=is_first)
                    all_posts.extend(posts)
                    
                    # Save in real-time after each subreddit
                    self._save_json_incremental(all_posts, output_file)
                    # Note: The actual saved count includes merged posts from other instances
                    
                    # Give background agents a moment to start
                    time.sleep(1)
                    
                    time.sleep(2)  # Be nice to Reddit servers
                except Exception as e:
                    print(f"❌ Error scraping r/{subreddit}: {e}")
                    continue
            
            print(f"\n✅ Total posts scraped: {len(all_posts)}")
            
            # Wait for background agents to complete (with timeout)
            print("\n⏳ Waiting for background agent tasks to complete...")
            max_wait = 120  # Max 2 minutes
            waited = 0
            while waited < max_wait:
                # Check if any agents are still running
                active_threads = [t for t in threading.enumerate() if t != threading.current_thread() and t.is_alive() and t.daemon]
                if not active_threads:
                    break
                time.sleep(5)
                waited += 5
                if waited % 15 == 0:  # Print every 15 seconds
                    print(f"  ⏳ Still waiting for agent tasks... ({waited}s/{max_wait}s)")
            
            if waited >= max_wait:
                print(f"  ⚠️ Timeout waiting for agents - some may still be running")
            else:
                print(f"  ✅ All agent tasks completed")
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user. Cleaning up...")
            # Don't re-raise immediately - try to clean up first
            try:
                if self.client.session_id:
                    self.client.stop_session()
                    print("✅ Browser session closed")
            except Exception as e:
                print(f"⚠️ Error closing session during interrupt: {e}")
            raise  # Re-raise after cleanup attempt
        except Exception as e:
            print(f"❌ Error in scrape_all_subreddits: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up browser session (non-blocking, don't let errors stop exit)
            try:
                if self.client.session_id:
                    self.client.stop_session()
                    print("✅ Browser session closed")
            except KeyboardInterrupt:
                # If we get another interrupt during cleanup, just exit
                print("\n⚠️ Interrupted during cleanup. Exiting...")
                import sys
                sys.exit(0)
            except Exception as e:
                print(f"⚠️ Error closing session: {e}")
                # Don't raise - we want to exit cleanly even if cleanup fails
        
        return all_posts
    
    def _save_json_incremental(self, posts: List[Post], output_file: str) -> None:
        """Save posts to JSON file incrementally (thread-safe, merges with existing data)."""
        global _json_file_lock
        try:
            with _json_file_lock:
                # Read existing posts
                existing_posts = []
                if os.path.exists(output_file):
                    try:
                        with open(output_file, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                existing_posts = json.loads(content)
                    except (json.JSONDecodeError, ValueError):
                        existing_posts = []
                
                # Create a dict of existing posts by (source, link) to avoid duplicates
                existing_dict = {}
                for p in existing_posts:
                    key = (p.get("source"), p.get("link"))
                    if key not in existing_dict:
                        existing_dict[key] = p
                
                # Add new posts, avoiding duplicates
                new_posts_dict = [post.to_dict() for post in posts]
                for new_post in new_posts_dict:
                    key = (new_post.get("source"), new_post.get("link"))
                    if key not in existing_dict:
                        existing_dict[key] = new_post
                    else:
                        # Update existing post with new data (e.g., token_name, comments)
                        existing_dict[key].update(new_post)
                
                # Convert back to list
                all_posts = list(existing_dict.values())
                
                # Sort by ID if available, otherwise by source
                all_posts.sort(key=lambda x: (x.get("source", ""), x.get("id", 0)))
                
                # Write merged data
                json_str = json.dumps(all_posts, indent=2, ensure_ascii=False)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                
                # Print actual saved count (merged from all instances)
                print(f"  💾 Saved {len(all_posts)} total posts to {output_file} (merged from all instances)")
        except Exception as e:
            print(f"⚠️ Error saving JSON: {e}")
            import traceback
            traceback.print_exc()
    
    def to_json(self, posts: List[Post], output_file: str = "scraped_posts.json") -> str:
        """Convert posts to JSON format (thread-safe, merges with existing data).
        
        Args:
            posts: List of Post objects
            output_file: Output file path
            
        Returns:
            JSON string
        """
        global _json_file_lock
        
        with _json_file_lock:
            # Read existing posts
            existing_posts = []
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            existing_posts = json.loads(content)
                except (json.JSONDecodeError, ValueError):
                    existing_posts = []
            
            # Create a dict of existing posts by (source, link) to avoid duplicates
            existing_dict = {}
            for p in existing_posts:
                key = (p.get("source"), p.get("link"))
                if key not in existing_dict:
                    existing_dict[key] = p
            
            # Add new posts, avoiding duplicates
            new_posts_dict = [post.to_dict() for post in posts]
            for new_post in new_posts_dict:
                key = (new_post.get("source"), new_post.get("link"))
                if key not in existing_dict:
                    existing_dict[key] = new_post
                else:
                    # Update existing post with new data
                    existing_dict[key].update(new_post)
            
            # Convert back to list and sort
            all_posts = list(existing_dict.values())
            all_posts.sort(key=lambda x: (x.get("source", ""), x.get("id", 0)))
            
            # Save merged data
            json_str = json.dumps(all_posts, indent=2, ensure_ascii=False)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        print(f"💾 Saved {len(all_posts)} total posts to {output_file} (merged with existing)")
        return json_str


def main():
    """Main function to run the Reddit scraper."""
    print("🚀 Starting Reddit Memecoin Scraper...")
    print(f"📋 Monitoring {len(MEMECOIN_SUBREDDITS)} subreddits\n")
    
    scraper = RedditScraper()
    posts = scraper.scrape_all_subreddits(
        limit_per_subreddit=10,
        scrape_comments=True,
        take_screenshots=False  # Keep screenshots off for now - can use Agent API as fallback if scraping fails
    )
    
    # Convert to JSON
    json_output = scraper.to_json(posts)
    
    # Display summary
    print("\n" + "="*60)
    print("SCRAPED POSTS SUMMARY")
    print("="*60)
    
    for i, post in enumerate(posts[:10], 1):  # Show first 10
        print(f"\n{i}. [{post.source}] {post.title}")
        print(f"   ⬆️ {post.upvotes_likes} | 💬 {post.comment_count} | 👤 {post.author or 'unknown'}")
        if post.comments:
            print(f"   💬 Comments: {len(post.comments)}")
    
    if len(posts) > 10:
        print(f"\n... and {len(posts) - 10} more posts")
    
    print(f"\n📄 Full JSON saved to scraped_posts.json")


if __name__ == "__main__":
    main()

