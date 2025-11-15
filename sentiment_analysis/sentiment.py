import json
from textblob import TextBlob

def analyze_sentiment(text):
    """
    Analyze sentiment of text using TextBlob.
    Returns a score between -1 (negative) and 1 (positive).
    """
    if not text or text.strip() == "":
        return 0.0
    
    blob = TextBlob(text)
    return round(blob.sentiment.polarity, 3)

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
    
    # Analyze each comment and calculate average
    comment_sentiments = []
    if 'comments' in data and data['comments']:
        for comment in data['comments']:
            sentiment = analyze_sentiment(comment)
            comment_sentiments.append(sentiment)
    
    # Calculate overall sentiment score
    # Weighted: title (30%), content (20%), comments average (50%)
    comments_avg = sum(comment_sentiments) / len(comment_sentiments) if comment_sentiments else 0
    
    if data.get('content', '').strip():
        overall_sentiment = (title_sentiment * 0.3 + content_sentiment * 0.2 + comments_avg * 0.5)
    else:
        # If no content, weight title and comments more
        overall_sentiment = (title_sentiment * 0.4 + comments_avg * 0.6)
    
    # Update data with sentiment score
    data['sentiment_score'] = round(overall_sentiment, 3)
    
    # Write output JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"Sentiment analysis complete!")
    print(f"Overall sentiment score: {data['sentiment_score']}")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    input_file = "sample.json"
    output_file = "sentiment.json"
    
    process_json_file(input_file, output_file)
