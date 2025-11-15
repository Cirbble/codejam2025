"""Main script to run historical Reddit scraping."""
import signal
import sys
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.reddit_scraper import RedditScraper
from src.config import REDDIT_SUBREDDITS

# Track all active scrapers for cleanup
active_scrapers = []


def signal_handler(sig, frame):
    """Handle Ctrl+C to ensure all sessions are closed."""
    print("\n\n⚠️ Interrupted by user. Closing all sessions...")
    import requests
    from src.config import BROWSER_CASH_API_KEY, BROWSER_CASH_BASE_URL
    
    for scraper in active_scrapers:
        if scraper.client.session_id:
            session_id = scraper.client.session_id
            try:
                # Use the correct DELETE endpoint format
                url = f"{BROWSER_CASH_BASE_URL}/session?sessionId={session_id}"
                headers = {
                    "Authorization": f"Bearer {BROWSER_CASH_API_KEY}",
                    "Content-Type": "application/json"
                }
                response = requests.delete(url, headers=headers, timeout=5)
                if response.status_code in [200, 204]:
                    print(f"  🛑 Session {session_id[:20]}... stopped")
                scraper.client.stop_session(force=True)
            except Exception as e:
                print(f"  ⚠️ Error closing session: {e}")
    sys.exit(0)


def scrape_subreddit_worker(subreddit: str, output_file: str, pages: int = 5) -> int:
    """Worker function to scrape a single subreddit in parallel.
    
    Args:
        subreddit: Subreddit name to scrape
        output_file: JSON file to save posts to
        pages: Number of pages to scrape
        
    Returns:
        Number of posts scraped
    """
    scraper = None
    try:
        scraper = RedditScraper()
        active_scrapers.append(scraper)
        
        scraper.client.start_session()
        
        # Add a small delay before starting to stagger requests
        time.sleep(random.uniform(0.5, 2.0))
        
        print(f"🔵 Started scraping r/{subreddit}...")
        
        posts = scraper.scrape_subreddit_historical(
            subreddit,
            pages=pages,
            posts_per_page=25,
            output_file=output_file
        )
        
        print(f"✅ Finished scraping r/{subreddit}: {len(posts)} posts")
        return len(posts)
        
    except Exception as e:
        error_msg = str(e).lower()
        if "connection_reset" in error_msg or "err_connection" in error_msg:
            print(f"⚠️ Connection reset for r/{subreddit} (Reddit rate limiting). Skipping...")
        else:
            print(f"❌ Error scraping r/{subreddit}: {e}")
        return 0
    finally:
        if scraper and scraper.client.session_id:
            try:
                scraper.client.stop_session(force=True)
            except:
                pass


def main():
    """Run historical scraping for Reddit subreddits in parallel."""
    global active_scrapers
    output_file = "scraped_posts.json"
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("🚀 Starting Parallel Reddit Scraper...")
        print(f"📋 Scraping {len(REDDIT_SUBREDDITS)} subreddits simultaneously")
        print(f"📅 Only posts from the last week (will stop when older posts found)")
        print(f"⚡ Using parallel processing for faster scraping\n")
        
        # Use ThreadPoolExecutor to scrape subreddits in parallel
        # Run exactly 3 browsers simultaneously for top priority subreddits
        max_workers = 3
        
        # Prioritize: pumpfun, CryptoMoonShots, altcoin first (top 3)
        priority_subreddits = REDDIT_SUBREDDITS[:3]  # Top 3 priority
        remaining_subreddits = REDDIT_SUBREDDITS[3:]  # Rest
        
        total_posts = 0
        
        # First batch: Scrape top 3 priority subreddits simultaneously
        print(f"🚀 Batch 1: Scraping top 3 priority subreddits simultaneously...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_subreddit = {
                executor.submit(scrape_subreddit_worker, subreddit, output_file, 5): subreddit
                for subreddit in priority_subreddits
            }
            
            for future in as_completed(future_to_subreddit):
                subreddit = future_to_subreddit[future]
                try:
                    post_count = future.result()
                    total_posts += post_count
                except Exception as e:
                    print(f"❌ Subreddit r/{subreddit} failed: {e}")
        
        # Remaining batches: Scrape remaining subreddits in batches of 3
        if remaining_subreddits:
            print(f"\n🚀 Batch 2+: Scraping remaining {len(remaining_subreddits)} subreddits...")
            for i in range(0, len(remaining_subreddits), max_workers):
                batch = remaining_subreddits[i:i+max_workers]
                with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                    future_to_subreddit = {
                        executor.submit(scrape_subreddit_worker, subreddit, output_file, 5): subreddit
                        for subreddit in batch
                    }
                    
                    for future in as_completed(future_to_subreddit):
                        subreddit = future_to_subreddit[future]
                        try:
                            post_count = future.result()
                            total_posts += post_count
                        except Exception as e:
                            print(f"❌ Subreddit r/{subreddit} failed: {e}")
        
        print(f"\n✅ Parallel scraping complete!")
        print(f"📊 Total posts scraped: {total_posts}")
        print(f"📄 Posts saved to {output_file}")
            
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        # Ensure cleanup on error
        for scraper in active_scrapers:
            if scraper.client.session_id:
                try:
                    scraper.client.stop_session(force=True)
                except:
                    pass
        raise


if __name__ == "__main__":
    main()
