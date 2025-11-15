import json
import os

def convert_sentiment_to_coin_data(input_file, output_file):
    """
    Convert sentiment.json to coin-data.json format
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, input_file)
    output_path = os.path.join(script_dir, '..', 'public', output_file)
    
    # Read sentiment data
    with open(input_path, 'r', encoding='utf-8') as f:
        sentiment_data = json.load(f)
    
    coin_data = []
    
    for post in sentiment_data:
        token_name = post.get('token_name', 'UNKNOWN')
        
        # Create coin data entry
        coin_entry = {
            "id": token_name.lower(),
            "name": token_name,
            "symbol": token_name,
            "price": 1000,  # Default price
            "balance": 1000,  # Default balance
            "feedback": f"Trending on {post.get('source', 'reddit')}",
            "changePercentage": 0.0,
            "icon": token_name,
            "raw_sentiment_score": post.get('raw_sentiment_score', 0.0),
            "aggregate_sentiment_score": post.get('aggregate_sentiment_score', 0.0),
            "engagement_score": post.get('engagement_score', 0.0),
            "source": post.get('source', ''),
            "platform": post.get('platform', ''),
            "title": post.get('title', ''),
            "content": post.get('content', '')[:500] if post.get('content') else '',  # Truncate long content
            "author": post.get('author', ''),
            "timestamp": post.get('timestamp', ''),
            "post_age": post.get('post_age', ''),
            "upvotes_likes": post.get('upvotes_likes', 0),
            "comment_count": post.get('comment_count', 0),
            "comments": post.get('comments', [])[:5],  # Only keep first 5 comments
            "link": post.get('link', '')
        }
        
        coin_data.append(coin_entry)
    
    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coin_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully converted {len(coin_data)} entries")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    convert_sentiment_to_coin_data("sentiment.json", "coin-data.json")
