"""
GitHub Data Source for LangGraph Assistant
Provides GitHub repository and user data via GitHub API.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from .core import DataSource, DataSourceConfig
import logging

logger = logging.getLogger(__name__)

class GitHubDataSource(DataSource):
    """Data source for GitHub repository and user data via GitHub API.
    
    This data source provides comprehensive access to GitHub data through
    GitHub's REST API. It supports repository information, user profiles,
    code search, and GitHub statistics.
    
    Key Features:
    - Repository information and statistics
    - User profiles and activity
    - Code search and analysis
    - Issue and pull request data
    - GitHub trending repositories
    - Repository analytics and insights
    
    Supported Data:
    - Public repositories and users
    - Code search and analysis
    - GitHub statistics and trends
    - Repository metadata and content
    
    API Documentation: https://docs.github.com/en/rest
    """
    
    def __init__(self, api_key: Optional[str] = None):
        headers = {"Accept": "application/vnd.github.v3+json"}
        if api_key:
            headers["Authorization"] = f"token {api_key}"
            
        config = DataSourceConfig(
            name="github",
            rest_url="https://api.github.com",
            headers=headers
        )
        super().__init__(config)
        self.api_key = api_key
    
    def health_check(self) -> bool:
        """Check if the GitHub API is accessible."""
        try:
            response = self.session.get("https://api.github.com/zen", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            return False
    
    def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get comprehensive information about a GitHub repository.
        
        Args:
            owner (str): Repository owner (username or organization)
            repo (str): Repository name
            
        Returns:
            Dict containing repository information with:
            - Repository name, description, and URL
            - Star count and fork count
            - Language and topics
            - Creation and last update dates
            - License and visibility status
            - Repository size and open issues count
            - Default branch and homepage
        """
        return self.get_data(f"repos/{owner}/{repo}")
    
    def get_user_profile(self, username: str) -> Dict[str, Any]:
        """Get detailed profile information for a GitHub user.
        
        Args:
            username (str): GitHub username
            
        Returns:
            Dict containing user profile with:
            - Username and display name
            - Bio and location
            - Company and website
            - Public repositories count
            - Followers and following count
            - Account creation date
            - Profile picture and social links
        """
        return self.get_data(f"users/{username}")
    
    def search_repositories(self, query: str, sort: str = "stars", order: str = "desc",
                           per_page: int = 30, page: int = 1) -> Dict[str, Any]:
        """Search for GitHub repositories by query.
        
        Args:
            query (str): Search query (keywords, language, user, etc.)
            sort (str): Sort order (stars, forks, help-wanted-issues, updated)
            order (str): Sort direction (desc, asc)
            per_page (int): Results per page (max: 100)
            page (int): Page number for pagination
            
        Returns:
            Dict containing search results with:
            - Matching repositories and metadata
            - Repository statistics and information
            - Owner details and descriptions
            - Language and topic information
            - Total results count
            - Pagination information
        """
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page,
            "page": page
        }
        return self.get_data("search/repositories", params)
    
    def get_repository_readme(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get the README file content for a repository.
        
        Args:
            owner (str): Repository owner (username or organization)
            repo (str): Repository name
            
        Returns:
            Dict containing README information with:
            - README content and format
            - File size and encoding
            - Download URL and SHA
            - Content type and language
        """
        return self.get_data(f"repos/{owner}/{repo}/readme")
    
    def get_repository_languages(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get programming languages used in a repository.
        
        Args:
            owner (str): Repository owner (username or organization)
            repo (str): Repository name
            
        Returns:
            Dict containing language statistics with:
            - Programming languages and their usage
            - Bytes of code per language
            - Language percentages
            - Total repository size
        """
        return self.get_data(f"repos/{owner}/{repo}/languages")
    
    def get_repository_contributors(self, owner: str, repo: str, per_page: int = 30) -> Dict[str, Any]:
        """Get contributors to a repository.
        
        Args:
            owner (str): Repository owner (username or organization)
            repo (str): Repository name
            per_page (int): Results per page (max: 100)
            
        Returns:
            Dict containing contributors with:
            - Contributor usernames and profiles
            - Contribution counts and statistics
            - Contributor avatars and URLs
            - Contribution types and activity
        """
        params = {"per_page": per_page}
        return self.get_data(f"repos/{owner}/{repo}/contributors", params)
    
    def get_trending_repositories(self, since: str = "daily", language: Optional[str] = None) -> Dict[str, Any]:
        """Get trending repositories on GitHub.
        
        Args:
            since (str): Time period (daily, weekly, monthly)
            language (str, optional): Programming language filter
            
        Returns:
            Dict containing trending repositories with:
            - Trending repository information
            - Star growth and statistics
            - Repository descriptions and URLs
            - Language and topic information
            - Trending period and metrics
        """
        # Note: This would require scraping GitHub trending page or using a different API
        # For now, we'll use search with trending criteria
        query = "stars:>100"
        if language:
            query += f" language:{language}"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 30
        }
        return self.get_data("search/repositories", params)
    
    def get_repository_issues(self, owner: str, repo: str, state: str = "open",
                             per_page: int = 30, page: int = 1) -> Dict[str, Any]:
        """Get issues for a repository.
        
        Args:
            owner (str): Repository owner (username or organization)
            repo (str): Repository name
            state (str): Issue state (open, closed, all)
            per_page (int): Results per page (max: 100)
            page (int): Page number for pagination
            
        Returns:
            Dict containing issues with:
            - Issue titles and descriptions
            - Issue numbers and states
            - Assignees and labels
            - Creation and update dates
            - Issue URLs and comments count
        """
        params = {
            "state": state,
            "per_page": per_page,
            "page": page
        }
        return self.get_data(f"repos/{owner}/{repo}/issues", params)
    
    def search_code(self, query: str, sort: str = "indexed", order: str = "desc",
                   per_page: int = 30, page: int = 1) -> Dict[str, Any]:
        """Search for code on GitHub.
        
        Args:
            query (str): Code search query
            sort (str): Sort order (indexed, best-match)
            order (str): Sort direction (desc, asc)
            per_page (int): Results per page (max: 100)
            page (int): Page number for pagination
            
        Returns:
            Dict containing code search results with:
            - Matching code files and snippets
            - Repository and file information
            - Code content and metadata
            - File paths and URLs
            - Language and size information
        """
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page,
            "page": page
        }
        return self.get_data("search/code", params)
    
    def get_repository_stargazers(self, owner: str, repo: str, per_page: int = 30) -> Dict[str, Any]:
        """Get users who starred a repository.
        
        Args:
            owner (str): Repository owner (username or organization)
            repo (str): Repository name
            per_page (int): Results per page (max: 100)
            
        Returns:
            Dict containing stargazers with:
            - User profiles and information
            - Star dates and timestamps
            - User avatars and URLs
            - Stargazer statistics
        """
        params = {"per_page": per_page}
        return self.get_data(f"repos/{owner}/{repo}/stargazers", params)
    
    def get_user_repositories(self, username: str, type: str = "owner", sort: str = "full_name",
                             per_page: int = 30, page: int = 1) -> Dict[str, Any]:
        """Get repositories for a specific user.
        
        Args:
            username (str): GitHub username
            type (str): Repository type (owner, member, all)
            sort (str): Sort order (created, updated, pushed, full_name)
            per_page (int): Results per page (max: 100)
            page (int): Page number for pagination
            
        Returns:
            Dict containing user repositories with:
            - Repository names and descriptions
            - Repository statistics and information
            - Language and topic data
            - Creation and update dates
            - Repository visibility and settings
        """
        params = {
            "type": type,
            "sort": sort,
            "per_page": per_page,
            "page": page
        }
        return self.get_data(f"users/{username}/repos", params)

# Factory function for GitHub data source
def create_github_source(api_key: Optional[str] = None) -> GitHubDataSource:
    """Create a GitHub data source instance.
    
    Args:
        api_key (str, optional): GitHub personal access token
        
    Returns:
        GitHubDataSource: Configured GitHub data source instance
    """
    return GitHubDataSource(api_key) 