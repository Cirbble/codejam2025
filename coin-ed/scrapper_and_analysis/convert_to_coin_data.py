import json
import os

def convert_sentiment_to_coin_data(input_file, output_file):
    """
    Convert sentiment.json to coin-data.json format.
    Combines duplicate coins by averaging values and merging comments.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, input_file)
    output_path = os.path.join(script_dir, '..', 'public', output_file)
    
    # Read sentiment data
    with open(input_path, 'r', encoding='utf-8') as f:
        sentiment_data = json.load(f)
    
    # Dictionary to group posts by token name
    coin_groups = {}
    
    for post in sentiment_data:
        token_name = post.get('token_name', 'UNKNOWN')
        
        if token_name not in coin_groups:
            coin_groups[token_name] = []
        
        coin_groups[token_name].append(post)
    
    # Process each coin group
    coin_data = []
    
    for token_name, posts in coin_groups.items():
        # Calculate averages
        avg_raw_sentiment = sum(p.get('raw_sentiment_score', 0.0) for p in posts) / len(posts)
        avg_aggregate_sentiment = sum(p.get('aggregate_sentiment_score', 0.0) for p in posts) / len(posts)
        avg_engagement = sum(p.get('engagement_score', 0.0) for p in posts) / len(posts)
        
        # Combine all comments from all posts
        all_comments = []
        for post in posts:
            post_comments = post.get('comments', [])
            if isinstance(post_comments, list):
                all_comments.extend(post_comments)
        
        # Remove duplicate comments and moderator messages
        unique_comments = []
        seen_comments = set()
        for comment in all_comments:
            # Skip moderator announcements
            if 'Moderator Announcement' in comment or 'I am a bot' in comment:
                continue
            # Skip duplicates
            comment_lower = comment.lower().strip()
            if comment_lower not in seen_comments:
                seen_comments.add(comment_lower)
                unique_comments.append(comment)
        
        # Use the most recent post for main data
        latest_post = max(posts, key=lambda p: p.get('timestamp', ''))
        
        # Combine titles if multiple posts
        if len(posts) > 1:
            title = f"{latest_post.get('title', '')} (+{len(posts)-1} more posts)"
        else:
            title = latest_post.get('title', '')
        
        # Sum up engagement metrics
        total_upvotes = sum(p.get('upvotes_likes', 0) for p in posts)
        total_comments = len(unique_comments)
        
        # Calculate overall confidence score (0-100%)
        # Weight: 30% raw sentiment, 50% aggregate sentiment, 20% engagement
        normalized_raw = (avg_raw_sentiment + 1) / 2  # Convert from -1 to 1 scale to 0 to 1
        normalized_aggregate = (avg_aggregate_sentiment + 1) / 2
        normalized_engagement = avg_engagement  # Already 0-1
        
        confidence = (normalized_raw * 0.3) + (normalized_aggregate * 0.5) + (normalized_engagement * 0.2)
        confidence_percentage = round(confidence * 100)
        
        # Determine recommendation based on confidence
        if confidence_percentage >= 75:
            recommendation = "BUY"
        elif confidence_percentage >= 55:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"
        
        # Create combined coin entry
        coin_entry = {
            "id": token_name.lower(),
            "name": token_name,
            "symbol": token_name,
            "price": 1000,  # Default price
            "balance": 1000,  # Default balance
            "feedback": f"Trending on {latest_post.get('source', 'reddit')} ({len(posts)} posts)",
            "changePercentage": 0.0,
            "icon": token_name,
            "raw_sentiment_score": round(avg_raw_sentiment, 3),
            "aggregate_sentiment_score": round(avg_aggregate_sentiment, 3),
            "engagement_score": round(avg_engagement, 3),
            "source": latest_post.get('source', ''),
            "platform": latest_post.get('platform', ''),
            "title": title,
            "content": latest_post.get('content', '')[:500] if latest_post.get('content') else '',
            "author": latest_post.get('author', ''),
            "timestamp": latest_post.get('timestamp', ''),
            "post_age": latest_post.get('post_age', ''),
            "upvotes_likes": total_upvotes,
            "comment_count": total_comments,
            "comments": unique_comments,  # All unique comments combined
            "link": latest_post.get('link', ''),
            "post_count": len(posts),  # Track how many posts were combined
            "confidence": confidence_percentage,
            "recommendation": recommendation
        }
        
        coin_data.append(coin_entry)
    
    # Sort by aggregate sentiment score (highest first)
    coin_data.sort(key=lambda x: x['aggregate_sentiment_score'], reverse=True)
    
    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coin_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Conversion Complete ===")
    print(f"Total unique coins: {len(coin_data)}")
    print(f"Total posts processed: {len(sentiment_data)}")
    print(f"Posts combined: {len(sentiment_data) - len(coin_data)}")
    print(f"\nTop 5 coins by sentiment:")
    for i, coin in enumerate(coin_data[:5], 1):
        print(f"{i}. {coin['name']}: {coin['aggregate_sentiment_score']} | Confidence: {coin['confidence']}% | {coin['recommendation']} ({coin['post_count']} posts, {coin['comment_count']} comments)")
    
    # Show recommendation breakdown
    buy_count = sum(1 for c in coin_data if c['recommendation'] == 'BUY')
    hold_count = sum(1 for c in coin_data if c['recommendation'] == 'HOLD')
    sell_count = sum(1 for c in coin_data if c['recommendation'] == 'SELL')
    print(f"\nRecommendations: {buy_count} BUY | {hold_count} HOLD | {sell_count} SELL")
    print(f"\nOutput saved to: {output_path}")

if __name__ == "__main__":
    convert_sentiment_to_coin_data("sentiment.json", "coin-data.json")
