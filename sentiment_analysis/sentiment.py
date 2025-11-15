import json
from textblob import TextBlob
import math

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

def process_json_file(input_file, output_file):
    """
    Process JSON file and add sentiment scores.
    """
    # Read input JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Analyze title sentiment
    title_sentiment = analyze_sentiment(data.get('title', ''))
    
    # Analyze content sentiment
    content_sentiment = analyze_sentiment(data.get('content', ''))
    
    # Calculate raw_sentiment_score (title + content only)
    if data.get('content', '').strip():
        raw_sentiment = (title_sentiment * 0.6 + content_sentiment * 0.4)
    else:
        raw_sentiment = title_sentiment
    
    data['raw_sentiment_score'] = round(raw_sentiment, 3)
    
    # Analyze each comment and calculate average
    comment_sentiments = []
    if 'comments' in data and data['comments']:
        for comment in data['comments']:
            sentiment = analyze_sentiment(comment)
            comment_sentiments.append(sentiment)
    
    comments_avg = sum(comment_sentiments) / len(comment_sentiments) if comment_sentiments else 0
    
    # Get engagement metrics
    platform = data.get('platform', '')
    upvotes = data.get('upvotes_likes', 0)
    comment_count = data.get('comment_count', 0)
    
    # Platform-specific: use award_count for Reddit, share_count for Twitter
    if platform.lower() == "reddit":
        shares_or_awards = data.get('award_count', 0)
    elif platform.lower() == "twitter":
        shares_or_awards = data.get('share_count', 0)
    else:
        shares_or_awards = data.get('share_count', 0) or data.get('award_count', 0)
    
    # Calculate aggregate_sentiment_score
    data['aggregate_sentiment_score'] = calculate_aggregate_sentiment(
        raw_sentiment, comments_avg, platform, upvotes, shares_or_awards
    )
    
    # Calculate engagement_score
    data['engagement_score'] = calculate_engagement_score(
        upvotes, comment_count, shares_or_awards
    )
    
    # Write output JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"Sentiment analysis complete!")
    print(f"Raw sentiment score: {data['raw_sentiment_score']}")
    print(f"Aggregate sentiment score: {data['aggregate_sentiment_score']}")
    print(f"Engagement score: {data['engagement_score']}")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    input_file = "sample.json"
    output_file = "sentiment.json"
    
    process_json_file(input_file, output_file)
