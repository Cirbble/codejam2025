"""Data models for scraped posts."""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Post:
    """Represents a scraped post from any platform."""
    id: int  # Scrape number/ID
    source: str  # Subreddit, Twitter handle, Telegram channel, etc.
    platform: str  # "reddit", "twitter", "telegram", etc.
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    timestamp: Optional[str] = None  # ISO format datetime
    post_age: Optional[str] = None  # Human readable (e.g., "2 hours ago")
    
    # Engagement metrics
    upvotes_likes: int = 0
    comment_count: int = 0
    share_count: int = 0  # Twitter/X shares/retweets
    award_count: int = 0  # Reddit awards
    
    # Content
    comments: List[str] = field(default_factory=list)  # List of comment texts
    link: Optional[str] = None
    post_type: Optional[str] = None  # "text", "image", "link", "video"
    
    # Media
    screenshot_path: Optional[str] = None
    
    # Analysis fields (can be populated later)
    sentiment_score: Optional[float] = None  # -1 to 1
    hype_score: Optional[float] = None  # Calculated metric
    keywords_found: List[str] = field(default_factory=list)
    token_name: Optional[str] = None  # Token/coin name identified (can use Agent API if needed)
    
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "source": self.source,
            "platform": self.platform,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "timestamp": self.timestamp,
            "post_age": self.post_age,
            "upvotes_likes": self.upvotes_likes,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "award_count": self.award_count,
            "comments": self.comments,
            "link": self.link,
            "post_type": self.post_type,
            "screenshot_path": self.screenshot_path,
            "sentiment_score": self.sentiment_score,
            "hype_score": self.hype_score,
            "keywords_found": self.keywords_found,
            "token_name": self.token_name,
        }

