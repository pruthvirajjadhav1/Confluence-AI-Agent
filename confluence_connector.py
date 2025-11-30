"""
Confluence Connector Module
Handles all interactions with Confluence API
"""
import os
import requests
from typing import List, Dict, Optional
from urllib.parse import quote


class ConfluenceConnector:
    """Connector for Confluence API operations"""
    
    def __init__(self, base_url: str, username: str, api_token: str):
        """
        Initialize Confluence connector
        
        Args:
            base_url: Confluence base URL (e.g., https://yourcompany.atlassian.net)
            username: Confluence username or email
            api_token: Confluence API token
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.auth = (username, api_token)
        self.api_base = f"{self.base_url}/wiki/rest/api"
        
    def search_content(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for content in Confluence using multiple strategies
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of content items with metadata
        """
        all_results = []
        seen_ids = set()
        
        # Strategy 1: Title search (most specific) - try exact match first
        title_results = self._search_by_title(query, limit)
        for result in title_results:
            if result["id"] not in seen_ids:
                all_results.append(result)
                seen_ids.add(result["id"])
        
        # Strategy 2: Title search with individual keywords (for long titles)
        if len(all_results) < limit:
            title_keywords = [word.strip() for word in query.split() if len(word.strip()) > 2]
            if len(title_keywords) > 1:
                for keyword in title_keywords[:3]:  # Try first 3 keywords
                    keyword_title_results = self._search_cql(f'title ~ "{keyword}"', limit)
                    for result in keyword_title_results:
                        if result["id"] not in seen_ids:
                            all_results.append(result)
                            seen_ids.add(result["id"])
        
        # Strategy 3: CQL text search with exact phrase
        if len(all_results) < limit:
            cql_results = self._search_cql(f'text ~ "{query}"', limit)
            for result in cql_results:
                if result["id"] not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(result["id"])
        
        # Strategy 4: CQL title search (redundant but ensures coverage)
        if len(all_results) < limit:
            cql_title_results = self._search_cql(f'title ~ "{query}"', limit)
            for result in cql_title_results:
                if result["id"] not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(result["id"])
        
        # Strategy 5: Break query into keywords and search in text
        if len(all_results) < limit:
            keywords = [word.strip() for word in query.split() if len(word.strip()) > 2]
            if keywords:
                keyword_query = " OR ".join([f'text ~ "{kw}"' for kw in keywords[:3]])
                keyword_results = self._search_cql(f"({keyword_query})", limit)
                for result in keyword_results:
                    if result["id"] not in seen_ids:
                        all_results.append(result)
                        seen_ids.add(result["id"])
        
        # Strategy 6: Use REST API content search (fallback)
        if len(all_results) < limit:
            rest_results = self._search_rest_api(query, limit)
            for result in rest_results:
                if result["id"] not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(result["id"])
        
        return all_results[:limit]
    
    def search_by_title(self, query: str, limit: int = 10) -> List[Dict]:
        """Search by title using CQL - public method"""
        return self._search_cql(f'title ~ "{query}"', limit)
    
    def _search_by_title(self, query: str, limit: int = 10) -> List[Dict]:
        """Search by title using CQL - internal method"""
        return self._search_cql(f'title ~ "{query}"', limit)
    
    def _search_cql(self, cql_query: str, limit: int = 10) -> List[Dict]:
        """Search using CQL query"""
        url = f"{self.api_base}/content/search"
        params = {
            "cql": cql_query,
            "limit": limit,
            "expand": "space,version,body.storage"
        }
        
        try:
            response = requests.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
            return self._format_results(results)
        except requests.exceptions.HTTPError as e:
            # Log HTTP errors for debugging but don't fail completely
            if hasattr(e.response, 'status_code') and e.response.status_code == 400:
                # Bad CQL query, try a simpler version
                return []
            return []
        except Exception as e:
            # Silently fail for individual strategies
            return []
    
    def _search_rest_api(self, query: str, limit: int = 10) -> List[Dict]:
        """Search using REST API content endpoint"""
        url = f"{self.api_base}/content/search"
        params = {
            "cql": f'text ~ "{query}" OR title ~ "{query}"',
            "limit": limit,
            "expand": "space,version,body.storage"
        }
        
        try:
            response = requests.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
            return self._format_results(results)
        except Exception as e:
            return []
    
    def _format_results(self, results: List[Dict]) -> List[Dict]:
        """Format search results"""
        formatted_results = []
        for item in results:
            formatted_results.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "url": f"{self.base_url}{item.get('_links', {}).get('webui', '')}",
                "space": item.get("space", {}).get("name", "Unknown"),
                "type": item.get("type", "page"),
                "excerpt": item.get("excerpt", ""),
                "body": item.get("body", {}).get("storage", {}).get("value", "")
            })
        return formatted_results
    
    def get_content_by_id(self, content_id: str) -> Optional[Dict]:
        """
        Retrieve specific content by ID
        
        Args:
            content_id: Confluence content ID
            
        Returns:
            Content dictionary with full details
        """
        url = f"{self.api_base}/content/{content_id}"
        params = {
            "expand": "space,version,body.storage,ancestors"
        }
        
        try:
            response = requests.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            item = response.json()
            
            return {
                "id": item.get("id"),
                "title": item.get("title"),
                "url": f"{self.base_url}{item.get('_links', {}).get('webui', '')}",
                "space": item.get("space", {}).get("name", "Unknown"),
                "type": item.get("type", "page"),
                "body": item.get("body", {}).get("storage", {}).get("value", ""),
                "version": item.get("version", {}).get("number", 1),
                "lastModified": item.get("version", {}).get("when", "")
            }
        except Exception as e:
            print(f"Error retrieving content: {e}")
            return None
    
    def get_space_content(self, space_key: str, limit: int = 50) -> List[Dict]:
        """
        Get all content from a specific space
        
        Args:
            space_key: Confluence space key
            limit: Maximum number of results
            
        Returns:
            List of content items
        """
        url = f"{self.api_base}/content"
        params = {
            "spaceKey": space_key,
            "limit": limit,
            "expand": "space,version,body.storage"
        }
        
        try:
            response = requests.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
            
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "url": f"{self.base_url}{item.get('_links', {}).get('webui', '')}",
                    "space": item.get("space", {}).get("name", "Unknown"),
                    "type": item.get("type", "page"),
                    "body": item.get("body", {}).get("storage", {}).get("value", "")
                })
            return formatted_results
        except Exception as e:
            print(f"Error retrieving space content: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test if the connection to Confluence is working"""
        try:
            url = f"{self.api_base}/user/current"
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

