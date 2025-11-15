"""Twitter scraper for memecoin sentiment analysis using Browser Cash."""
import time
import json
import os
import threading
from typing import List, Dict, Any, Optional
from src.browser_cash_client import BrowserCashClient
from src.models import Post


class TwitterScraper:
    """Scraper for Twitter/X hashtags using Browser Cash automation."""
    
    def __init__(self):
        """Initialize the Twitter scraper."""
        self.client = BrowserCashClient()
        self.post_id_counter = 1
        
        # Store posts by ID for async updates
        self.posts_dict: Dict[int, Post] = {}
        self.lock = threading.Lock()  # For thread-safe updates
    
    def navigate_to_hashtag(self, hashtag: str) -> None:
        """Navigate to a Twitter hashtag search (latest tweets).
        
        Args:
            hashtag: Hashtag without # (e.g., "SolanaMemeCoins")
        """
        # Twitter search URL for latest tweets with hashtag
        url = f"https://twitter.com/search?q=%23{hashtag}&src=hashtag_click&f=live"
        self.client.navigate(url, wait_time=10)  # Wait longer for Twitter to load
        # Additional wait for content to render
        time.sleep(5)
    
    def scrape_tweets(self, hashtag: str, limit: int = 25) -> List[Post]:
        """Scrape tweets from the current Twitter page.
        
        Args:
            hashtag: Hashtag being monitored
            limit: Maximum number of tweets to scrape
            
        Returns:
            List of Post objects
        """
        script = f"""
        (function() {{
            const tweets = [];
            const tweetElements = document.querySelectorAll('article[data-testid="tweet"]');
            
            console.log('Found ' + tweetElements.length + ' tweet elements');
            
            for (let i = 0; i < Math.min({limit}, tweetElements.length); i++) {{
                const tweet = tweetElements[i];
                
                try {{
                    // Get tweet text/content
                    const textElement = tweet.querySelector('[data-testid="tweetText"]');
                    const content = textElement ? textElement.textContent.trim() : '';
                    
                    // Get author/username
                    const authorLink = tweet.querySelector('a[href*="/"]');
                    const author = authorLink ? authorLink.getAttribute('href').replace('/', '') : '';
                    
                    // Get timestamp
                    const timeElement = tweet.querySelector('time');
                    const timestamp = timeElement ? timeElement.getAttribute('datetime') || '' : '';
                    const postAge = timeElement ? timeElement.getAttribute('title') || '' : '';
                    
                    // Get engagement metrics
                    const replyButton = tweet.querySelector('[data-testid="reply"]');
                    const retweetButton = tweet.querySelector('[data-testid="retweet"]');
                    const likeButton = tweet.querySelector('[data-testid="like"]');
                    
                    let replyCount = 0;
                    let retweetCount = 0;
                    let likeCount = 0;
                    
                    if (replyButton) {{
                        const replyText = replyButton.getAttribute('aria-label') || '';
                        const replyMatch = replyText.match(/(\\d+)/);
                        replyCount = replyMatch ? parseInt(replyMatch[1]) : 0;
                    }}
                    
                    if (retweetButton) {{
                        const retweetText = retweetButton.getAttribute('aria-label') || '';
                        const retweetMatch = retweetText.match(/(\\d+)/);
                        retweetCount = retweetMatch ? parseInt(retweetMatch[1]) : 0;
                    }}
                    
                    if (likeButton) {{
                        const likeText = likeButton.getAttribute('aria-label') || '';
                        const likeMatch = likeText.match(/(\\d+)/);
                        likeCount = likeMatch ? parseInt(likeMatch[1]) : 0;
                    }}
                    
                    // Get tweet link
                    const linkElement = tweet.querySelector('a[href*="/status/"]');
                    let tweetLink = '';
                    if (linkElement) {{
                        const href = linkElement.getAttribute('href');
                        tweetLink = href.startsWith('http') ? href : 'https://twitter.com' + href;
                    }}
                    
                    // Determine post type
                    let postType = 'text';
                    if (tweet.querySelector('img')) postType = 'image';
                    if (tweet.querySelector('video')) postType = 'video';
                    
                    if (content || author) {{
                        tweets.push({{
                            content: content,
                            author: author,
                            timestamp: timestamp,
                            postAge: postAge,
                            replyCount: replyCount,
                            retweetCount: retweetCount,
                            likeCount: likeCount,
                            link: tweetLink,
                            postType: postType
                        }});
                    }}
                }} catch (e) {{
                    console.error('Error parsing tweet:', e);
                }}
            }}
            
            return tweets;
        }})();
        """
        
        try:
            # Wait a bit more before scraping to ensure content is loaded
            time.sleep(3)
            
            result = self.client.execute_script(script)
            if not result or len(result) == 0:
                return []
            
            posts = []
            for i, tweet_data in enumerate(result):
                try:
                    post = Post(
                        id=self.post_id_counter,
                        source=f"#{hashtag}",
                        platform="twitter",
                        title=None,  # Twitter doesn't have titles
                        content=tweet_data.get("content", ""),
                        author=tweet_data.get("author", ""),
                        timestamp=tweet_data.get("timestamp"),
                        post_age=tweet_data.get("postAge"),
                        upvotes_likes=tweet_data.get("likeCount", 0),
                        comment_count=tweet_data.get("replyCount", 0),
                        award_count=tweet_data.get("retweetCount", 0),  # Using retweets as "awards"
                        comments=[],  # Twitter replies would need separate scraping
                        link=tweet_data.get("link"),
                        post_type=tweet_data.get("postType", "text")
                    )
                    posts.append(post)
                    self.post_id_counter += 1
                except Exception as e:
                    print(f"  ⚠️ Error creating post from tweet: {e}")
                    continue
            
            return posts
            
        except Exception as e:
            print(f"  ❌ Error scraping tweets from #{hashtag}: {e}")
            return []
    
    def scrape_hashtag_historical(self, hashtag: str, limit: int = 25, output_file: str = "scraped_posts.json") -> List[Post]:
        """Scrape historical tweets from a hashtag (like old Reddit scraper).
        
        Args:
            hashtag: Hashtag to scrape (without #)
            limit: Maximum number of tweets to scrape
            output_file: JSON file to save posts to
            
        Returns:
            List of Post objects
        """
        print(f"  🔍 Navigating to #{hashtag}...")
        self.navigate_to_hashtag(hashtag)
        
        # Scrape tweets from the page
        posts = self.scrape_tweets(hashtag, limit=limit)
        
        # Save posts incrementally
        for post in posts:
            self._update_post_in_json(post, output_file)
        
        return posts
    
    def monitor_hashtag(self, hashtag: str, output_file: str = "scraped_posts.json", check_interval: int = 30):
        """Continuously monitor a Twitter hashtag for new tweets (REALTIME - for later use).
        
        Args:
            hashtag: Hashtag to monitor (without #)
            output_file: JSON file to save posts to
            check_interval: Seconds between checks for new posts
        """
        print(f"🔍 Monitoring #{hashtag}")
        
        # Navigate to hashtag
        self.navigate_to_hashtag(hashtag)
        
        seen_links = set()  # Track seen tweet links to avoid duplicates
        consecutive_empty_scrapes = 0  # Track how many times we got no tweets
        
        try:
            while True:
                # Scrape new tweets
                tweets = self.scrape_tweets(hashtag, limit=20)
                
                if len(tweets) == 0:
                    consecutive_empty_scrapes += 1
                    # Only warn after multiple empty scrapes
                    if consecutive_empty_scrapes >= 3:
                        print(f"  ⚠️ No tweets found from #{hashtag} (still monitoring...)")
                        consecutive_empty_scrapes = 0  # Reset counter
                else:
                    consecutive_empty_scrapes = 0  # Reset on success
                
                new_count = 0
                for tweet in tweets:
                    # Check if we've seen this tweet before
                    if tweet.link and tweet.link in seen_links:
                        continue
                    
                    # Mark as seen
                    if tweet.link:
                        seen_links.add(tweet.link)
                    
                    # Save to JSON immediately
                    self._update_post_in_json(tweet, output_file)
                    new_count += 1
                
                if new_count > 0:
                    print(f"  📝 Added {new_count} new tweets from #{hashtag}")
                
                # Wait before next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print(f"\n⚠️ Stopping monitoring for #{hashtag}")
        except Exception as e:
            print(f"  ❌ Error monitoring #{hashtag}: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_post_in_json(self, post: Post, output_file: str) -> None:
        """Update JSON file with a new post (thread-safe, adds to beginning for latest first).
        
        Args:
            post: Post object to add/update
            output_file: Path to JSON file
        """
        with self.lock:
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
                    # New post - add to beginning (latest first)
                    all_posts.insert(0, post.to_dict())
                
                # Save updated JSON
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_posts, f, indent=2, ensure_ascii=False)
                    
            except Exception as e:
                print(f"  ⚠️ Failed to update JSON for post {post.id}: {e}")
