import json
from textblob import TextBlob
import math
import os

def analyze_sentiment(text):
    """
    Analyze sentiment of text using TextBlob.
    Returns a score between 0 (negative) and 1 (positive).
    Creates variance with both high and low scores.
    """
    if not text or text.strip() == "":
        return 0.5  # Neutral = 0.5

    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1 to 1
    subjectivity = blob.sentiment.subjectivity  # 0 to 1

    # Convert polarity from -1,1 to 0,1 range
    normalized = (polarity + 1) / 2  # Now 0 to 1

    # Create variance based on normalized score
    if normalized >= 0.6:
        # Strong positive: amplify
        # 0.6 -> 0.7, 0.8 -> 0.9, 1.0 -> 1.0
        boosted = 0.4 + (normalized ** 0.8) * 0.6
    elif normalized >= 0.4:
        # Neutral: slight boost
        # 0.4 to 0.6 -> 0.45 to 0.65
        boosted = normalized + 0.05
    else:
        # Negative: keep lower
        # 0 -> 0.1, 0.2 -> 0.25, 0.4 -> 0.4
        boosted = normalized * 0.8 + 0.1

    # Slight penalty for low subjectivity (boring posts)
    if subjectivity < 0.3:
        boosted = boosted * 0.9

    # Ensure 0-1 range
    boosted = max(0.0, min(1.0, boosted))

    return round(boosted, 3)

def calculate_engagement_score(upvotes, comments, shares_or_awards):
    """
    Calculate engagement score with wider variance.
    Returns a score between 0 and 1.
    """
    # Use log scale with varied weights
    upvote_score = math.log1p(upvotes) * 0.7
    comment_score = math.log1p(comments) * 0.4
    extra_score = math.log1p(shares_or_awards) * 0.25

    engagement = upvote_score + comment_score + extra_score

    # Create wider variance in normalization
    # Very low engagement (0-2) -> 0.05-0.15
    # Low engagement (3-10) -> 0.2-0.4
    # Medium engagement (11-50) -> 0.45-0.7
    # High engagement (50+) -> 0.75-0.95
    if engagement < 2:
        normalized = engagement / 20
    elif engagement < 5:
        normalized = 0.15 + (engagement - 2) / 15
    else:
        normalized = engagement / (engagement + 6)

    # Apply power curve for more extreme values
    normalized = normalized ** 0.9

    return round(normalized, 3)

def calculate_aggregate_sentiment(raw_sentiment, comments_avg, platform, upvotes, shares_or_awards):
    """
    Calculate aggregate sentiment incorporating engagement metrics.
    Returns score between 0 and 1.
    """
    # Base aggregate with higher weight on raw sentiment
    base_aggregate = (raw_sentiment * 0.7 + comments_avg * 0.3)

    # Platform-specific engagement boost
    if platform.lower() == "reddit":
        engagement_factor = (math.log1p(upvotes) * 0.04 + math.log1p(shares_or_awards) * 0.02)
    elif platform.lower() == "twitter":
        engagement_factor = (math.log1p(upvotes) * 0.04 + math.log1p(shares_or_awards) * 0.025)
    else:
        engagement_factor = math.log1p(upvotes) * 0.04

    engagement_factor = min(engagement_factor, 0.4)

    # Add engagement boost (scales with base sentiment)
    if base_aggregate > 0.5 and upvotes > 3:
        # Good base + engagement = amplify
        aggregate = base_aggregate + engagement_factor
        if aggregate > 0.7:
            aggregate = aggregate ** 0.9 + 0.1
    elif base_aggregate > 0.4:
        # Neutral: moderate boost
        aggregate = base_aggregate + (engagement_factor * 0.5)
    else:
        # Low base: minimal boost
        aggregate = base_aggregate + (engagement_factor * 0.2)

    # Ensure 0-1 range
    aggregate = max(0.0, min(1.0, aggregate))

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

    print(f"\n{'='*60}")
    print(f"🧠 SENTIMENT ANALYSIS STARTING")
    print(f"{'='*60}")
    print(f"📂 Input file: {input_path}")
    print(f"📂 Output file: {output_path}")

    # Read input JSON
    with open(input_path, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    print(f"📊 Total posts loaded: {len(posts)}")

    processed_posts = []
    skipped_count = 0
    tokens_found = set()

    for idx, post in enumerate(posts, 1):
        # Skip posts where token_name is null
        if post.get('token_name') is None or post.get('token_name') == 'null':
            skipped_count += 1
            print(f"⏭️  Skipping post {idx}/{len(posts)} (ID: {post.get('id')}) - No token name")
            continue

        token_name = post.get('token_name', 'UNKNOWN')
        tokens_found.add(token_name)

        print(f"🔍 Processing post {idx}/{len(posts)} - Token: {token_name}")

        # Analyze title sentiment
        title_sentiment = analyze_sentiment(post.get('title', ''))

        # Analyze content sentiment
        content_sentiment = analyze_sentiment(post.get('content', ''))

        # Calculate raw_sentiment_score (title + content only)
        if post.get('content', '').strip():
            raw_sentiment = (title_sentiment * 0.5 + content_sentiment * 0.5)
        else:
            raw_sentiment = title_sentiment

        # Create variance - scores already in 0-1 range
        if raw_sentiment > 0.6:
            # Strong positive: amplify
            raw_sentiment = raw_sentiment ** 0.85 + 0.1
        elif raw_sentiment > 0.4:
            # Neutral: keep as is
            raw_sentiment = raw_sentiment
        else:
            # Low: slight penalty
            raw_sentiment = raw_sentiment * 0.9

        # Ensure 0-1 range
        raw_sentiment = max(0.0, min(1.0, raw_sentiment))

        post['raw_sentiment_score'] = round(raw_sentiment, 3)

        # Analyze each comment and calculate average
        comment_sentiments = []
        if 'comments' in post and post['comments']:
            for comment in post['comments']:
                sentiment = analyze_sentiment(comment)
                comment_sentiments.append(sentiment)

        comments_avg = sum(comment_sentiments) / len(comment_sentiments) if comment_sentiments else 0

        print(f"   💬 Comments analyzed: {len(comment_sentiments)}")
        print(f"   📈 Raw sentiment: {post['raw_sentiment_score']}")

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

        print(f"   ✅ Aggregate sentiment: {post['aggregate_sentiment_score']}")
        print(f"   ✅ Engagement score: {post['engagement_score']}")

        processed_posts.append(post)

    # Write output JSON (overwrite)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_posts, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"✅ SENTIMENT ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"📂 Output: {output_path}")
    print(f"📊 Total posts processed: {len(processed_posts)}")
    print(f"⏭️  Posts skipped (no token): {skipped_count}")
    print(f"🪙 Unique tokens found: {len(tokens_found)}")
    print(f"   Tokens: {', '.join(sorted(tokens_found))}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    input_file = "scraped_posts.json"
    output_file = "sentiment.json"

    process_posts(input_file, output_file)
