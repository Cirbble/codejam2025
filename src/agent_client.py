"""Agent API client for Browser Cash - use as fallback when scraping fails."""
import requests
from typing import Optional, Dict, Any
from src.config import AGENT_CASH_API_KEY, AGENT_CASH_BASE_URL


class AgentClient:
    """Client for Browser Cash Agent API - useful for complex tasks or when scraping fails."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Agent client.
        
        Args:
            api_key: Agent API key. If not provided, uses config value.
        """
        self.api_key = api_key or AGENT_CASH_API_KEY
        if not self.api_key:
            raise ValueError("Agent API key is required. Set AGENT_CASH_API_KEY in .env file.")
        
        self.base_url = AGENT_CASH_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_task(self, prompt: str, agent: str = "gemini", mode: str = "text", step_limit: int = 10) -> Dict[str, Any]:
        """Create an agent task.
        
        Args:
            prompt: Task description/prompt for the agent
            agent: Agent to use (default: "gemini")
            mode: Task mode (default: "text")
            step_limit: Maximum steps for the agent
            
        Returns:
            Task creation response with task_id
        """
        url = f"{self.base_url}/v1/task/create"
        payload = {
            "agent": agent,
            "prompt": prompt,
            "mode": mode,
            "stepLimit": step_limit
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Agent API request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            raise
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get task status and results.
        
        Args:
            task_id: Task ID to check
            
        Returns:
            Task status and results
        """
        url = f"{self.base_url}/v1/task/{task_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Agent API get_task error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            raise
    
    def scrape_with_agent(self, url: str, extract_what: str = "all posts and their details") -> Dict[str, Any]:
        """Use agent to scrape a page when normal scraping fails.
        
        Args:
            url: URL to scrape
            extract_what: What to extract (e.g., "all posts with titles, upvotes, and comments")
            
        Returns:
            Agent task result
        """
        prompt = f"Navigate to {url} and extract {extract_what}. Return the data in JSON format."
        
        task = self.create_task(prompt, step_limit=20)
        task_id = task.get("taskId") or task.get("id")
        
        if not task_id:
            raise ValueError("No task ID in response")
        
        print(f"🤖 Agent task created: {task_id}")
        print(f"⏳ Waiting for agent to complete...")
        
        # Poll for completion (simplified - you might want to add timeout)
        import time
        while True:
            task_status = self.get_task(task_id)
            status = task_status.get("status", "").lower()
            
            if status in ["completed", "done", "success"]:
                print(f"✅ Agent task completed")
                return task_status
            elif status in ["failed", "error"]:
                raise Exception(f"Agent task failed: {task_status}")
            
            time.sleep(2)
    
    def identify_token_name(self, post_content: str) -> Optional[str]:
        """Use agent to identify token/coin name from post content.
        
        Args:
            post_content: Post title and content
            
        Returns:
            Token name if found, None otherwise
        """
        # Truncate content if too long to speed up processing
        if len(post_content) > 500:
            post_content = post_content[:500] + "..."
        
        prompt = f"Analyze this crypto post and identify the main token/coin name mentioned: {post_content}\n\nIMPORTANT: Return ONLY the token name in uppercase letters (e.g., HEGE, DOGE, SOL, BTC, ETH). Do NOT include any explanation, reasoning, or other text. If no token is found, return exactly: UNKNOWN\n\nToken name:"
        
        try:
            task = self.create_task(prompt, step_limit=3)  # Reduced steps for speed
            task_id = task.get("taskId") or task.get("id")
            
            if not task_id:
                return None
            
            # Wait for completion with shorter timeout
            import time
            for i in range(10):  # Max 20 seconds
                task_status = self.get_task(task_id)
                # API uses 'state' not 'status'
                state = task_status.get("state", "").lower() or task_status.get("status", "").lower()
                stopped_at = task_status.get("stoppedAt")
                result = task_status.get("result")
                
                # Task is complete if stoppedAt is set or state is completed/done
                if stopped_at or state in ["completed", "done", "success", "finished"]:
                    final_result = result or task_status.get("output", "")
                    # Extract token name from result - clean it up
                    if final_result:
                        final_result = str(final_result).strip()
                        
                        # Remove common prefixes and clean up
                        import re
                        # Remove JSON-like structures, quotes, etc.
                        final_result = re.sub(r"\{.*?'answer'\s*:\s*['\"]", "", final_result)
                        final_result = re.sub(r"['\"].*", "", final_result)
                        final_result = final_result.strip()
                        
                        # Skip if it's clearly not a token name
                        if final_result.lower() in ["unknown", "none", "n/a", "i have", "i have a", "i have e"]:
                            return None
                        
                        # Extract token name (uppercase letters, 2-10 chars, possibly with $)
                        token_matches = re.findall(r'\$?([A-Z]{2,10})', final_result)
                        if token_matches:
                            # Take the last token mentioned (usually the answer)
                            token = token_matches[-1]
                            # Filter out common false positives
                            if token not in ["HAVE", "THE", "THIS", "THAT", "WITH", "FROM", "WHEN", "WHAT", "WHERE", "WHICH"]:
                                return token
                        
                        # If no token found but result looks like a token (all caps, short)
                        if re.match(r'^[A-Z]{2,10}$', final_result):
                            return final_result
                        
                        # Last resort: take first word if it's uppercase and looks like a token
                        first_word = final_result.split()[0] if final_result.split() else ""
                        if re.match(r'^[A-Z]{2,10}$', first_word):
                            return first_word
                        
                        return None
                    return None
                elif state in ["failed", "error"]:
                    return None
                # Continue polling if still active/running
                
                time.sleep(2)
            
            return None
        except Exception as e:
            print(f"⚠️ Agent error identifying token: {e}")
            return None

