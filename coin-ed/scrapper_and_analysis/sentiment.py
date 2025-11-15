import json
from textblob import TextBlob
import math
import os

def analyze_sentiment(text):
    """
    Analyze sentiment of text using TextBlob.
    Returns a score between -1 (negative) and 1 (positive).
    """
    if not text or text.strip() == "":
        return 0.0
    
    blob = TextBlob(text)
    return round(blob.sentiment.polarity, 3)

def calculate_engagement_score(upvotes, comments, shares_or_awards):
    """
    Calculate engagement score using logarithmic scaling.
    Returns a score between 0 and 1.
    """
    # Use log scale to prevent extreme values from dominating
    upvote_score = math.log1p(upvotes) * 0.5
    comment_score = math.log1p(comments) * 0.3
    extra_score = math.log1p(shares_or_awards) * 0.2
    
    engagement = upvote_score + comment_score + extra_score
    
    # Normalize to 0-1 range using sigmoid-like function
    # Engagement of ~10 = 0.5, scales smoothly to approach 1.0
    normalized = engagement / (engagement + 10)
    
    return round(normalized, 3)

def calculate_aggregate_sentiment(raw_sentiment, comments_avg, platform, upvotes, shares_or_awards):
    """
    Calculate aggregate sentiment incorporating engagement metrics.
    Platform-specific weighting for Reddit vs Twitter.
    """
    # Base aggregate from raw sentiment and comments
    base_aggregate = (raw_sentiment * 0.4 + comments_avg * 0.6)
    
    # Platform-specific engagement boost/penalty
    if platform.lower() == "reddit":
        # Reddit: use upvotes and awards
        engagement_factor = (math.log1p(upvotes) * 0.02 + math.log1p(shares_or_awards) * 0.01)
    elif platform.lower() == "twitter":
        # Twitter: use upvotes (likes) and shares (retweets)
        engagement_factor = (math.log1p(upvotes) * 0.02 + math.log1p(shares_or_awards) * 0.015)
    else:
        # Default: just use upvotes
        engagement_factor = math.log1p(upvotes) * 0.02
    
    # Apply engagement factor (capped to prevent extreme values)
    engagement_factor = min(engagement_factor, 0.3)
    aggregate = base_aggregate + (engagement_factor if base_aggregate > 0 else -engagement_factor)
    
    # Clamp to [-1, 1] range
    aggregate = max(-1.0, min(1.0, aggregate))
    
    return round(aggregate, 3)

def process_posts(input_file, output_file):
    """
    Process scraped_posts.json and add sentiment scores.
    Skips posts where token_name is null.
    """
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, input_file)
    output_path = os.path.join(script_dir, output_file)
    
    # Read input JSON
    with open(input_path, 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    processed_posts = []
    skipped_count = 0
    
    for post in posts:
        # Skip posts where token_name is null
        if post.get('token_name') is None or post.get('token_name') == 'null':
            skipped_count += 1
            print(f"Skipping post ID {post.get('id')} - token_name is null")
            continue
        
        # Analyze title sentiment
        title_sentiment = analyze_sentiment(post.get('title', ''))
        
        # Analyze content sentiment
        content_sentiment = analyze_sentiment(post.get('content', ''))
        
        # Calculate raw_sentiment_score (title + content only)
        if post.get('content', '').strip():
            raw_sentiment = (title_sentiment * 0.6 + content_sentiment * 0.4)
        else:
            raw_sentiment = title_sentiment
        
        post['raw_sentiment_score'] = round(raw_sentiment, 3)
        
        # Analyze each comment and calculate average
        comment_sentiments = []
        if 'comments' in post and post['comments']:
            for comment in post['comments']:
                sentiment = analyze_sentiment(comment)
                comment_sentiments.append(sentiment)
        
        comments_avg = sum(comment_sentiments) / len(comment_sentiments) if comment_sentiments else 0
        
        # Get engagement metrics
        platform = post.get('platform', '')
        upvotes = post.get('upvotes_likes', 0)
        comment_count = post.get('comment_count', 0)
        
        # Platform-specific: use award_count for Reddit, share_count for Twitter
        if platform.lower() == "reddit":
            shares_or_awards = post.get('award_count', 0)
        elif platform.lower() == "twitter":
            shares_or_awards = post.get('share_count', 0)
        else:
            shares_or_awards = post.get('share_count', 0) or post.get('award_count', 0)
        
        # Calculate aggregate_sentiment_score
        post['aggregate_sentiment_score'] = calculate_aggregate_sentiment(
            raw_sentiment, comments_avg, platform, upvotes, shares_or_awards
        )
        
        # Calculate engagement_score
        post['engagement_score'] = calculate_engagement_score(
            upvotes, comment_count, shares_or_awards
        )
        
        processed_posts.append(post)
    
    # Write output JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_posts, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Sentiment Analysis Complete ===")
    print(f"Total posts processed: {len(processed_posts)}")
    print(f"Posts skipped (null token_name): {skipped_count}")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    input_file = "scraped_posts.json"
    output_file = "sentiment.json"
    
    process_posts(input_file, output_file)
