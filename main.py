"""Main script to run the memecoin sentiment scraper."""
from src.reddit_scraper import RedditScraper
import threading
import time

# The 3 subreddits to scrape in parallel
SUBREDDITS = ["altcoin", "CryptoMoonShots", "pumpfun"]


def scrape_single_subreddit(subreddit: str):
    """Run the EXACT scraper code for a single subreddit.
    
    This is IDENTICAL to the original main() function, just for one subreddit.
    """
    scraper = None
    try:
        print(f"🚀 Starting Memecoin Sentiment Scraper for r/{subreddit}...")
        print(f"📋 Monitoring 1 subreddit\n")
        
        scraper = RedditScraper()
        output_file = "scraped_posts.json"
        
        # Create a temporary config with just this subreddit
        original_subreddits = scraper.subreddits
        scraper.subreddits = [subreddit]
        
        # Scrape all subreddits (saves in real-time)
        # Note: limit_per_subreddit is now posts per page, not total limit
        # Scraper will continue until it finds posts older than 1 week
        posts = scraper.scrape_all_subreddits(
            limit_per_subreddit=25,  # Posts per page
            scrape_comments=True,
            take_screenshots=False,
            output_file=output_file
        )
        
        # Restore original subreddits
        scraper.subreddits = original_subreddits
        
        # Final save (already saved incrementally, but ensure it's up to date)
        scraper.to_json(posts, output_file)
        
        # Display summary
        print(f"\n" + "="*60)
        print(f"SCRAPED POSTS SUMMARY for r/{subreddit}")
        print("="*60)
        
        for i, post in enumerate(posts[:10], 1):  # Show first 10
            print(f"\n{i}. [{post.source}] {post.title}")
            print(f"   ⬆️ {post.upvotes_likes} | 💬 {post.comment_count} | 👤 {post.author or 'unknown'}")
            if post.comments:
                print(f"   💬 Comments: {len(post.comments)}")
        
        if len(posts) > 10:
            print(f"\n... and {len(posts) - 10} more posts")
        
        print(f"\n📄 Full JSON saved to scraped_posts.json")
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Interrupted by user for r/{subreddit}. Exiting...")
        # Cleanup is handled in scrape_all_subreddits finally block
        import sys
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error for r/{subreddit}: {e}")
        if scraper and scraper.client.session_id:
            try:
                scraper.client.stop_session()
            except:
                pass
        raise


def main():
    """Run 3 parallel instances of the scraper, one for each subreddit."""
    print("🚀 Starting 3 Parallel Memecoin Sentiment Scrapers...")
    print(f"📋 Scraping: r/{SUBREDDITS[0]}, r/{SUBREDDITS[1]}, r/{SUBREDDITS[2]}\n")
    
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
    
    print("\n✅ All scrapers completed!")


if __name__ == "__main__":
    main()

