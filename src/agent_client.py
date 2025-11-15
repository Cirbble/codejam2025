"""Agent API client for Browser Cash - use as fallback when scraping fails."""
import os
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
        
        # Log which API key is being used (masked for security)
        masked_key = f"{self.api_key[:8]}...{self.api_key[-8:]}" if len(self.api_key) > 16 else "***"
        print(f"🔑 Using Agent API key: {masked_key}")
        
        self.base_url = AGENT_CASH_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_task(self, prompt: str, agent: str = "gemini", mode: str = "text", step_limit: int = 10, cdp_url: Optional[str] = None, session_id: Optional[str] = None, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Create an agent task.
        
        Args:
            prompt: Task description/prompt for the agent
            agent: Agent to use (default: "gemini")
            mode: Task mode (default: "text")
            step_limit: Maximum steps for the agent
            cdp_url: Optional CDP WebSocket URL to use existing browser session
            session_id: Optional session ID to use existing browser session
            image_path: Optional path to image file to include (will be converted to base64)
            
        Returns:
            Task creation response with task_id
        """
        url = f"{self.base_url}/v1/task/create"
        
        # Build payload
        payload = {
            "agent": agent,
            "prompt": prompt,
            "mode": mode,
            "stepLimit": step_limit
        }
        
        # If we have an image path, convert to base64 and include in payload
        if image_path and os.path.exists(image_path):
            import base64
            with open(image_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
                # Try different possible field names the API might expect
                payload["image"] = img_data  # Try 'image' field
                # Alternative: payload["imageData"] = img_data
                # Alternative: payload["imageBase64"] = img_data
        
        # If we have a CDP URL or session ID, pass it to use existing session
        if cdp_url:
            payload["cdpUrl"] = cdp_url
        if session_id:
            payload["sessionId"] = session_id
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Agent API request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Status: {e.response.status_code}")
                print(f"   Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"⚠️ Unexpected error creating agent task: {e}")
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
            result = response.json()
            
            # Log failure reasons for debugging
            if result.get("state") == "failed":
                failed_reason = result.get("failedReason", "Unknown")
                error_msg = result.get("error", "")
                print(f"     🔍 Task {task_id[:8]}... failed: {failed_reason}")
                if error_msg:
                    print(f"     🔍 Error: {error_msg}")
            
            return result
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Agent API get_task error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Status: {e.response.status_code}")
                print(f"   Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"⚠️ Unexpected error getting task: {e}")
            raise
    
    def stop_task(self, task_id: str) -> bool:
        """Stop/close an agent task to free up resources.
        
        Args:
            task_id: Task ID to stop
            
        Returns:
            True if successful, False otherwise
        """
        # Try DELETE endpoint first (most common)
        url = f"{self.base_url}/v1/task/{task_id}"
        try:
            response = requests.delete(url, headers=self.headers, timeout=5)
            if response.status_code == 200 or response.status_code == 204:
                return True
            # If DELETE doesn't work, try POST to stop endpoint
            if response.status_code == 404:
                url = f"{self.base_url}/v1/task/{task_id}/stop"
                response = requests.post(url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    return True
        except Exception as e:
            # Silently fail - task may already be stopped or endpoint may not exist
            pass
        return False
    
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
    
    def identify_token_name(self, post_content: str, cdp_url: Optional[str] = None, session_id: Optional[str] = None) -> Optional[str]:
        """Use agent to identify token/coin name from post content.
        
        Args:
            post_content: Post title and content
            cdp_url: Optional CDP WebSocket URL to use existing browser session
            session_id: Optional session ID to use existing browser session
            
        Returns:
            Token name if found, None otherwise
        """
        # Truncate content if too long to speed up processing (increased limit for comments)
        if len(post_content) > 2000:
            post_content = post_content[:2000] + "..."
        
        # Text analysis - agent should analyze the provided text without needing browser navigation
        prompt = f"Analyze this crypto post text and identify the main token/coin name mentioned: {post_content}\n\nIMPORTANT: Return ONLY the token name in uppercase letters (e.g., EMPI, HEGE, DOGE, SOL, BTC, ETH). Do NOT navigate to any website. Do NOT include any explanation, reasoning, or other text. Just analyze the text provided above. If no token is found, return exactly: UNKNOWN\n\nToken name:"
        
        try:
            # TEXT-ONLY analysis - NO CDP URL, NO browser session
            # Agent analyzes the provided text directly without navigating anywhere
            task = self.create_task(prompt, step_limit=3, cdp_url=None)
            task_id = task.get("taskId") or task.get("id")
            
            if not task_id:
                return None
            
            # Check if we got a session limit error
            if "limit" in str(task).lower() or "403" in str(task):
                print(f"     ⚠️ Session limit reached, skipping token identification")
                return None
            
            # Wait for completion with shorter timeout
            import time
            for i in range(10):  # Max 20 seconds
                task_status = self.get_task(task_id)
                # API uses 'state' not 'status'
                state = task_status.get("state", "").lower() or task_status.get("status", "").lower()
                stopped_at = task_status.get("stoppedAt")
                result = task_status.get("result")
                
                # Check for session limit or other errors first
                if state == "failed":
                    failed_reason = task_status.get("failedReason", "")
                    if "limit" in failed_reason.lower() or "session" in failed_reason.lower():
                        print(f"     ⚠️ Session limit reached, stopping task")
                        self.stop_task(task_id)
                        return None
                
                # Task is complete if stoppedAt is set or state is completed/done
                if stopped_at or state in ["completed", "done", "success", "finished"]:
                    # Try multiple possible result locations
                    data = task_status.get("data", {})
                    final_result = (
                        result or 
                        task_status.get("output") or 
                        (data.get("result") if isinstance(data, dict) else None) or
                        (data.get("output") if isinstance(data, dict) else None)
                    )
                    
                    # Extract token name from result - clean it up
                    if final_result:
                        import re
                        
                        # If result is a dict, extract 'answer' field directly
                        if isinstance(final_result, dict):
                            token_answer = final_result.get("answer")
                            if token_answer:
                                token_answer = str(token_answer).strip()
                                # Check if it's a valid token name
                                if re.match(r'^[A-Z]{2,10}$', token_answer):
                                    # Stop task to free resources
                                    self.stop_task(task_id)
                                    return token_answer
                                # Try to extract token from the answer text
                                token_matches = re.findall(r'\$?([A-Z]{2,10})', token_answer)
                                if token_matches:
                                    token = token_matches[-1]
                                    if token not in ["HAVE", "THE", "THIS", "THAT", "WITH", "FROM", "WHEN", "WHAT", "WHERE", "WHICH", "UNKNOWN"]:
                                        # Stop task to free resources
                                        self.stop_task(task_id)
                                        return token
                            # If no 'answer' field, convert dict to string and process
                            final_result = str(final_result)
                        else:
                            final_result = str(final_result).strip()
                        
                        # Remove common prefixes and clean up (for string results)
                        if isinstance(final_result, str):
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
                                print(f"     ✅ Extracted token: {token}")
                                # Stop task to free resources
                                self.stop_task(task_id)
                                return token
                            else:
                                print(f"     ⚠️ Filtered out false positive: {token}")
                        
                        # If no token found but result looks like a token (all caps, short)
                        if re.match(r'^[A-Z]{2,10}$', final_result):
                            print(f"     ✅ Result is token-like: {final_result}")
                            # Stop task to free resources
                            self.stop_task(task_id)
                            return final_result
                        
                        # Last resort: take first word if it's uppercase and looks like a token
                        first_word = final_result.split()[0] if final_result.split() else ""
                        if re.match(r'^[A-Z]{2,10}$', first_word):
                            print(f"     ✅ Using first word as token: {first_word}")
                            # Stop task to free resources
                            self.stop_task(task_id)
                            return first_word
                        
                        print(f"     ⚠️ Could not extract token from: {final_result[:100]}")
                        # Stop task even if no token found
                        self.stop_task(task_id)
                        return None
                    else:
                        print(f"     ⚠️ Agent returned empty result")
                    # Stop task even if empty result
                    self.stop_task(task_id)
                    return None
                elif state in ["failed", "error"]:
                    failed_reason = task_status.get("failedReason", "Unknown")
                    error_msg = task_status.get("error", "")
                    attempts = task_status.get("attemptsMade", 0)
                    print(f"     ❌ Token identification task failed")
                    print(f"     🔍 Failed reason: {failed_reason}")
                    if error_msg:
                        print(f"     🔍 Error message: {error_msg}")
                    print(f"     🔍 Attempts made: {attempts}")
                    print(f"     🔍 Full task_status: {task_status}")
                    # Stop failed task to free resources
                    self.stop_task(task_id)
                    return None
                # Continue polling if still active/running
                
                time.sleep(2)
            
            print(f"     ⏱️ Token identification timed out after 20 seconds")
            # Stop timed out task to free resources
            self.stop_task(task_id)
            return None
        except Exception as e:
            print(f"⚠️ Agent error identifying token: {e}")
            # Try to stop task if we have task_id (may not be set if create_task failed)
            if 'task_id' in locals():
                try:
                    self.stop_task(task_id)
                except:
                    pass
            return None

