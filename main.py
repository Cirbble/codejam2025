"""Main script to run the memecoin sentiment scraper."""
from src.reddit_scraper import RedditScraper
from src.config import MEMECOIN_SUBREDDITS


def main():
    """Run the scraper."""
    scraper = None
    try:
        print("🚀 Starting Memecoin Sentiment Scraper...")
        print(f"📋 Monitoring {len(MEMECOIN_SUBREDDITS)} subreddits\n")
        
        scraper = RedditScraper()
        output_file = "scraped_posts.json"
        
        # Scrape all subreddits (saves in real-time)
        posts = scraper.scrape_all_subreddits(
            limit_per_subreddit=10,
            scrape_comments=True,
            take_screenshots=False,
            output_file=output_file
        )
        
        # Final save (already saved incrementally, but ensure it's up to date)
        scraper.to_json(posts, output_file)
        
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
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user. Exiting...")
        # Cleanup is handled in scrape_all_subreddits finally block
        import sys
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if scraper and scraper.client.session_id:
            try:
                scraper.client.stop_session()
            except:
                pass
        raise


if __name__ == "__main__":
    main()

