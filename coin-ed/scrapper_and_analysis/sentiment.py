import json
from textblob import TextBlob
import math
import os

def analyze_sentiment(text):
    """
    Analyze sentiment of text using TextBlob.
    Returns a score between -1 (negative) and 1 (positive).
    Applies amplification for higher variance.
    """
    if not text or text.strip() == "":
        return 0.0
    
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    # Amplify variance: make positive more positive, negative less negative
    if polarity >= 0:
        # Amplify positive scores with exponential curve
        # 0 -> 0.3, 0.3 -> 0.55, 0.5 -> 0.75, 0.8 -> 0.95, 1.0 -> 1.0
        boosted = 0.3 + (polarity ** 0.7) * 0.7
    else:
        # Soften negative scores but keep some variance
        # -1.0 -> -0.4, -0.5 -> -0.2, -0.2 -> -0.08
        boosted = polarity * 0.4
    
    return round(boosted, 3)

def calculate_engagement_score(upvotes, comments, shares_or_awards):
    """
    Calculate engagement score using logarithmic scaling with higher variance.
    Returns a score between 0 and 1.
    """
    # Use log scale with amplified weights for more variance
    upvote_score = math.log1p(upvotes) * 0.8
    comment_score = math.log1p(comments) * 0.5
    extra_score = math.log1p(shares_or_awards) * 0.3
    
    engagement = upvote_score + comment_score + extra_score
    
    # Normalize with lower denominator for higher variance
    # Low engagement (1-5) -> 0.1-0.3
    # Medium engagement (10-50) -> 0.4-0.7
    # High engagement (100+) -> 0.8-0.95
    normalized = engagement / (engagement + 5)
    
    # Apply power curve to increase variance
    normalized = normalized ** 0.85
    
    return round(normalized, 3)

def calculate_aggregate_sentiment(raw_sentiment, comments_avg, platform, upvotes, shares_or_awards):
    """
    Calculate aggregate sentiment incorporating engagement metrics.
    Platform-specific weighting with amplified variance.
    """
    # Base aggregate with higher weight on raw sentiment
    base_aggregate = (raw_sentiment * 0.75 + comments_avg * 0.25)
    
    # Platform-specific engagement boost with amplified multipliers
    if platform.lower() == "reddit":
        # Reddit: amplified boost based on upvotes and awards
        engagement_factor = (math.log1p(upvotes) * 0.06 + math.log1p(shares_or_awards) * 0.03)
    elif platform.lower() == "twitter":
        # Twitter: amplified boost for likes and retweets
        engagement_factor = (math.log1p(upvotes) * 0.06 + math.log1p(shares_or_awards) * 0.04)
    else:
        # Default: amplified upvote boost
        engagement_factor = math.log1p(upvotes) * 0.06
    
    # Higher cap for more dramatic differences
    engagement_factor = min(engagement_factor, 0.7)
    
    # Always add engagement boost
    aggregate = base_aggregate + engagement_factor
    
    # Amplify the aggregate with power curve for more variance
    if aggregate > 0:
        # Make positive scores more positive: 0.5 -> 0.65, 0.7 -> 0.85
        aggregate = aggregate ** 0.85
        # Add baseline boost
        aggregate = aggregate + 0.15
    else:
        # Keep negative scores softer
        aggregate = aggregate * 0.6
    
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
            raw_sentiment = (title_sentiment * 0.5 + content_sentiment * 0.5)
        else:
            raw_sentiment = title_sentiment
        
        # Amplify variance with power curve
        if raw_sentiment > 0:
            # Amplify positive: 0.3 -> 0.4, 0.5 -> 0.65, 0.7 -> 0.82
            raw_sentiment = raw_sentiment ** 0.8
            # Add baseline boost
            raw_sentiment = raw_sentiment + 0.1
        else:
            # Keep negative softer
            raw_sentiment = raw_sentiment * 0.5
        
        raw_sentiment = max(-1.0, min(1.0, raw_sentiment))
        
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
