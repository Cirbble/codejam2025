# Main.py Explanation

## Overview

`main.py` is the entry point for the memecoin sentiment scraper. It orchestrates **3 parallel scraper instances**, each dedicated to scraping a specific Reddit subreddit related to memecoins and pump.fun tokens.

## Architecture

The script uses **threading** to run 3 independent scraper instances simultaneously, one for each subreddit:
- `r/altcoin`
- `r/CryptoMoonShots`
- `r/pumpfun`

## How It Works

### 1. Parallel Execution (`main()` function)

```python
def main():
    # Creates 3 threads, one per subreddit
    threads = []
    for subreddit in SUBREDDITS:
        thread = threading.Thread(target=scrape_single_subreddit, args=(subreddit,))
        thread.start()
        threads.append(thread)
        time.sleep(0.5)  # Stagger starts by 0.5s
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
```

**Key Points:**
- Each subreddit gets its own thread
- Threads start with a 0.5s delay between them (staggered starts)
- `thread.join()` waits for all threads to finish before exiting

### 2. Single Subreddit Scraping (`scrape_single_subreddit()` function)

Each thread runs this function, which performs the **exact same scraping logic** for its assigned subreddit:

```python
def scrape_single_subreddit(subreddit: str):
    scraper = RedditScraper()
    scraper.subreddits = [subreddit]  # Override to only scrape this one
    
    posts = scraper.scrape_all_subreddits(
        limit_per_subreddit=25,  # Posts per page (not total limit)
        scrape_comments=True,
        take_screenshots=False,
        output_file="scraped_posts.json"
    )
    
    scraper.to_json(posts, output_file)  # Final save
```

**What Each Instance Does:**
1. Creates a new `RedditScraper()` instance
2. Overrides `scraper.subreddits` to only include its assigned subreddit
3. Calls `scrape_all_subreddits()` which:
   - Navigates to the subreddit's `/new` page
   - Scrapes posts page by page until it finds posts older than 1 week
   - Scrapes comments for each post
   - Identifies tokens using regex (`$TOKEN` pattern) or Agent API
   - Saves incrementally to `scraped_posts.json` (thread-safe)
4. Performs a final save with `to_json()`
5. Displays a summary of scraped posts

## Key Features

### Thread-Safe JSON Saving

All 3 instances write to the **same JSON file** (`scraped_posts.json`). The scraper uses:
- **Global file lock** (`_json_file_lock`) to prevent race conditions
- **Merge logic** that reads existing posts, adds new ones, and deduplicates by `(source, link)`
- **Incremental updates** - posts are saved as they're scraped, not just at the end

### Token Identification

Each post gets token identification via:
1. **Fast regex check** - If title contains `$TOKEN` (2-5 letters), extract it immediately
2. **Agent API fallback** - If no `$TOKEN` pattern, use Browser Cash Agent API to analyze text
3. **Queued execution** - Agent calls are queued with a semaphore (max 1 per instance = 3 total)

### Historical Scraping

The scraper:
- Navigates to `/new` pages (chronological order)
- Scrolls through pages until it finds posts older than 1 week
- Stops when it encounters a post with `post_age` indicating >7 days old

## Output

All scraped posts are saved to `scraped_posts.json` with the following structure:

```json
{
  "id": 1,
  "source": "r/pumpfun",
  "title": "What's really in your food? $THC is asking...",
  "token_name": "THC",  // Extracted from title or Agent API
  "comments": [...],
  "upvotes_likes": 2,
  "post_age": "4 hr. ago",
  ...
}
```

## Error Handling

- **KeyboardInterrupt (Ctrl+C)**: Each instance handles its own cleanup
- **Exceptions**: Errors in one instance don't stop the others
- **Session limits**: Agent API calls retry with exponential backoff

## Why 3 Parallel Instances?

Running 3 instances in parallel:
- **3x faster** - Scrapes all 3 subreddits simultaneously
- **Independent** - Each has its own browser session
- **Resilient** - If one fails, others continue
- **Shared output** - All results merge into one JSON file

## Usage

```bash
python main.py
```

This will:
1. Start 3 parallel scrapers
2. Scrape posts from the past week from each subreddit
3. Identify tokens (regex or Agent API)
4. Save everything to `scraped_posts.json`
5. Display summaries when complete

