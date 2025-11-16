"""Main script to run the memecoin sentiment scraper."""
from src.reddit_scraper import RedditScraper
import threading
import time
import os
import subprocess
import json
import sys

# Fix Windows console encoding for emojis
def safe_print(*args, **kwargs):
    """Print function that handles Unicode encoding errors on Windows."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # If emoji encoding fails, try to print without emojis or use ASCII fallback
        try:
            # Try UTF-8 encoding
            message = ' '.join(str(arg) for arg in args)
            sys.stdout.buffer.write((message + '\n').encode('utf-8'))
            sys.stdout.buffer.flush()
        except:
            # Last resort: remove emojis and print ASCII
            message = ' '.join(str(arg) for arg in args)
            # Remove common emoji Unicode ranges
            import re
            message = re.sub(r'[\U0001F300-\U0001F9FF]', '', message)  # Remove emojis
            print(message, **kwargs)

if sys.platform == 'win32':
    try:
        # Try to set UTF-8 encoding for stdout/stderr
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        # If that fails, replace print with safe_print
        import builtins
        builtins.print = safe_print

# The 3 subreddits to scrape in parallel
SUBREDDITS = ["altcoin", "CryptoMoonShots", "pumpfun"]

# Output paths - save directly to processing folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LEGACY_ROOT_FILE = os.path.join(SCRIPT_DIR, 'scraped_posts.json')
# Remove legacy root file if present to enforce single source of truth
if os.path.exists(LEGACY_ROOT_FILE):
    try:
        os.remove(LEGACY_ROOT_FILE)
        print(" Removed legacy root scraped_posts.json to avoid ambiguity")
    except Exception:
        pass

OUTPUT_DIR = os.path.join(SCRIPT_DIR, "coin-ed", "scrapper_and_analysis")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "scraped_posts.json")

# Global flag to track completion
scraping_complete = threading.Event()
completed_count = 0
completed_lock = threading.Lock()


def scrape_single_subreddit(subreddit: str):
    """Run scraper for a single subreddit with its own dedicated Browser Cash session.
    Includes 3-minute timeout per subreddit.

    Each thread gets its own scraper instance and Browser Cash session.
    """
    global completed_count
    scraper = None
    timeout_occurred = False

    def timeout_handler():
        nonlocal timeout_occurred
        timeout_occurred = True
        print(f"\n TIMEOUT: r/{subreddit} exceeded 3 minutes, stopping...")

    # Set 3-minute timeout
    timeout_seconds = 180
    timer = threading.Timer(timeout_seconds, timeout_handler)

    try:
        print(f" Starting Memecoin Sentiment Scraper for r/{subreddit}...")
        print(f" Monitoring 1 subreddit")
        print(f" Timeout: 3 minutes (180 seconds)\n")

        # Start timeout timer
        timer.start()

        scraper = RedditScraper()
        output_file = OUTPUT_FILE

        # Override subreddits to just this one
        scraper.subreddits = [subreddit]

        # Start a dedicated Browser Cash session for this thread with retry
        print(f" Starting Browser Cash session for r/{subreddit}...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                scraper.client.start_session()
                print(f" Session started for r/{subreddit}: {scraper.client.session_id}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"WARNING:  Session start failed (attempt {attempt + 1}/{max_retries}), retrying in 3s...")
                    time.sleep(3)
                else:
                    raise Exception(f"Failed to start session after {max_retries} attempts: {e}")

        # Get CDP URL and connect Playwright
        print(f" Getting CDP URL for r/{subreddit}...")
        cdp_url = scraper.client.get_cdp_url()
        print(f" CDP URL obtained for r/{subreddit}")

        print(f" Connecting Playwright for r/{subreddit}...")
        scraper.client.connect_playwright(cdp_url)
        print(f" Playwright connected for r/{subreddit}")

        # Now scrape this single subreddit
        print(f" Starting to scrape r/{subreddit}...")

        # Check timeout before scraping
        if timeout_occurred:
            print(f" Timeout occurred before scraping started for r/{subreddit}")
            return

        posts = scraper.scrape_subreddit(
            subreddit=subreddit,
            limit=50,  # Check up to 50 posts to ensure we find at least 5 with comments
            scrape_comments=True,
            take_screenshots=False,
            is_first=True  # Trigger refresh for better loading
        )

        # Cancel timeout if we finished successfully
        timer.cancel()

        if timeout_occurred:
            print(f" r/{subreddit} was stopped due to 3-minute timeout")

        # Ensure we have at least 5 posts with comments
        if len(posts) < 5:
            print(f"WARNING:  Only got {len(posts)} posts with comments from r/{subreddit}")
            print(f"    (This is okay, but ideally we want at least 5)")
        else:
            print(f" Got {len(posts)} posts with comments from r/{subreddit}")

        print(f" Scraped {len(posts)} posts from r/{subreddit}")

        # Save to JSON (thread-safe)
        if posts:
            scraper._save_json_incremental(posts, output_file)
            print(f" Saved {len(posts)} posts from r/{subreddit} to {output_file}")

        # Display summary
        print(f"\n" + "="*60)
        print(f"SCRAPED POSTS SUMMARY for r/{subreddit}")
        print("="*60)

        for i, post in enumerate(posts[:10], 1):  # Show first 10
            print(f"\n{i}. [{post.source}] {post.title}")
            print(f"    {post.upvotes_likes} |  {post.comment_count} |  {post.author or 'unknown'}")
            if post.comments:
                print(f"    Comments: {len(post.comments)}")

        if len(posts) > 10:
            print(f"\n... and {len(posts) - 10} more posts")

        print(f"\n Scraping complete for r/{subreddit}")

        # Mark this thread as complete
        with completed_lock:
            completed_count += 1
            print(f" {completed_count}/{len(SUBREDDITS)} subreddits completed")

            # If all threads are done, trigger processing
            if completed_count == len(SUBREDDITS):
                scraping_complete.set()

    except KeyboardInterrupt:
        timer.cancel()
        print(f"\n\nWARNING: Interrupted by user for r/{subreddit}. Exiting...")
        import sys
        sys.exit(0)
    except Exception as e:
        timer.cancel()
        print(f"\nERROR: Fatal error for r/{subreddit}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cancel timeout timer
        timer.cancel()

        # Always clean up the session
        if scraper and scraper.client.session_id:
            try:
                print(f" Stopping Browser Cash session for r/{subreddit}...")
                scraper.client.stop_session()
                print(f" Session stopped for r/{subreddit}")
            except Exception as cleanup_error:
                print(f"WARNING: Error stopping session for r/{subreddit}: {cleanup_error}")


def main():
    """Run 3 parallel instances of the scraper, one for each subreddit."""
    global completed_count
    completed_count = 0
    scraping_complete.clear()

    print("\n" + "="*70)
    print(" HELLCOIN'ED - MEMECOIN SENTIMENT SCRAPER")
    print("="*70)
    print(f" Scraping: r/{SUBREDDITS[0]}, r/{SUBREDDITS[1]}, r/{SUBREDDITS[2]}")
    print(f" Output: {OUTPUT_FILE}")
    print(f" Filter: Posts from last 14 days only")
    print("="*70 + "\n")

    threads = []
    for subreddit in SUBREDDITS:
        thread = threading.Thread(
            target=scrape_single_subreddit,
            args=(subreddit,),
            daemon=False
        )
        thread.start()
        threads.append(thread)
        # Small delay to stagger starts
        time.sleep(0.5)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("\n" + "="*70)
    print(" ALL SCRAPERS COMPLETED!")
    print("="*70)

    # Wait for completion flag
    scraping_complete.wait()

    # Automatically process the data
    print("\n" + "="*70)
    print(" AUTO-PROCESSING SCRAPED DATA")
    print("="*70)

    try:
        # Show what was scraped
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, 'r') as f:
                posts = json.load(f)
                unique_tokens = set(p.get('token_name') for p in posts if p.get('token_name'))
                print(f"\n Scraping Results:")
                print(f"   • Total posts: {len(posts)}")
                print(f"   • Unique tokens: {len(unique_tokens)}")
                if unique_tokens:
                    print(f"   • Tokens found: {', '.join(sorted(unique_tokens)[:10])}")
                    if len(unique_tokens) > 10:
                        print(f"     ... and {len(unique_tokens) - 10} more")

        # Step 1: Run sentiment analysis
        print("\n" + "-"*70)
        print("1.  Running sentiment analysis...")
        print("-"*70)
        sentiment_script = os.path.join(OUTPUT_DIR, "sentiment.py")

        result = subprocess.run(
            ["python3", sentiment_script],
            cwd=OUTPUT_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("    Sentiment analysis complete")
            # Show summary from output
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines[-8:]:
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"   WARNING: Sentiment analysis completed with warnings")
            if result.stderr:
                for line in result.stderr.strip().split('\n')[-5:]:
                    print(f"   {line}")

        # Step 2: Convert to coin-data.json
        print("\n" + "-"*70)
        print("2.  Converting to coin-data.json with Moralis API...")
        print("-"*70)
        convert_script = os.path.join(OUTPUT_DIR, "convert_to_coin_data.py")

        result = subprocess.run(
            ["python3", convert_script],
            cwd=OUTPUT_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("    Conversion complete")
            # Show summary
            output_lines = result.stdout.strip().split('\n')
            # Show last 15 lines which include the summary
            for line in output_lines[-15:]:
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"   WARNING: Conversion completed with warnings")
            if result.stderr:
                for line in result.stderr.strip().split('\n')[-5:]:
                    print(f"   {line}")

        # Show final output location
        coin_data_file = os.path.join(SCRIPT_DIR, "coin-ed", "public", "coin-data.json")
        if os.path.exists(coin_data_file):
            with open(coin_data_file, 'r') as f:
                coins = json.load(f)
                print(f"\n📈 Final Output:")
                print(f"   • File: coin-ed/public/coin-data.json")
                print(f"   • Coins with complete data: {len(coins)}")
                print(f"\n   Top 5 coins:")
                for i, coin in enumerate(coins[:5], 1):
                    print(f"   {i}. {coin['symbol']} - {coin['name']} (${coin['price']:.8f})")

        print("\n" + "="*70)
        print("🎉 PROCESSING COMPLETE - FRONTEND UPDATED!")
        print("="*70)
        print("\n🌐 Your dashboard is now live with fresh data at:")
        print("   http://localhost:4200")
        print("\n Check the dashboard to see:")
        print("   • Real-time prices from Moralis/DexScreener")
        print("   • Coin logos from Jupiter/Moralis")
        print("   • Sentiment analysis scores")
        print("   • Buy/Hold/Sell recommendations")
        print("   • All from posts within the last 14 days!")
        print("\n" + "="*70 + "\n")

    except Exception as e:
        print(f"\nERROR: Error during auto-processing: {e}")
        import traceback
        traceback.print_exc()
        print("\nYou can manually run:")
        print(f"  cd {OUTPUT_DIR}")
        print("  python3 sentiment.py")
        print("  python3 convert_to_coin_data.py")


if __name__ == "__main__":
    main()
