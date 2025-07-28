
from typing import Dict, Any, List, Optional, Literal
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
import os

# Import datasource module
from datasource import (
    datasource_manager,
    CoinGeckoDataSource,
    NewsDataSource,
    GitHubDataSource
)

# --- CoinGecko Unified Tool ---
class CoinGeckoToolInput(BaseModel):
    action: Literal[
        "get_coin_price",
        "get_coin_market_data",
        "get_trending_coins",
        "get_coin_history",
        "get_coin_market_chart",
        "get_exchange_rates",
        "get_global_data",
        "search_coins",
        "get_coin_info",
        "get_top_coins",
        "get_exchanges"
    ]
    coin_id: Optional[str] = Field(None, description="CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')")
    vs_currency: Optional[str] = Field("usd", description="Target currency (e.g., 'usd', 'eur')")
    query: Optional[str] = Field(None, description="Search query or keyword")
    date: Optional[str] = Field(None, description="Date for historical data (DD-MM-YYYY)")
    days: Optional[int] = Field(None, description="Number of days for market chart")
    order: Optional[str] = Field(None, description="Sort order for top coins")
    per_page: Optional[int] = Field(None, description="Results per page")
    page: Optional[int] = Field(None, description="Page number")

class CoinGeckoTool(BaseTool):
    name: str = "coingecko_data"
    description: str = "Unified tool for accessing CoinGecko cryptocurrency data. Supports price, market data, trending, history, search, and more."
    args_schema: type = CoinGeckoToolInput

    def _run(self, action, coin_id=None, vs_currency="usd", query=None, date=None, days=None, order=None, per_page=None, page=None):
        cg = datasource_manager.get_source("coingecko")
        if not cg:
            cg = CoinGeckoDataSource()
            datasource_manager.register_source("coingecko", cg)
        try:
            if action == "get_coin_price":
                return json.dumps(cg.get_coin_price(coin_id, vs_currency), indent=2)
            elif action == "get_coin_market_data":
                return json.dumps(cg.get_coin_market_data(coin_id, vs_currency), indent=2)
            elif action == "get_trending_coins":
                return json.dumps(cg.get_trending_coins(), indent=2)
            elif action == "get_coin_history":
                return json.dumps(cg.get_coin_history(coin_id, date, vs_currency), indent=2)
            elif action == "get_coin_market_chart":
                return json.dumps(cg.get_coin_market_chart(coin_id, vs_currency, days), indent=2)
            elif action == "get_exchange_rates":
                return json.dumps(cg.get_exchange_rates(), indent=2)
            elif action == "get_global_data":
                return json.dumps(cg.get_global_data(), indent=2)
            elif action == "search_coins":
                return json.dumps(cg.search_coins(query), indent=2)
            elif action == "get_coin_info":
                return json.dumps(cg.get_coin_info(coin_id), indent=2)
            elif action == "get_top_coins":
                return json.dumps(cg.get_top_coins(vs_currency, order, per_page), indent=2)
            elif action == "get_exchanges":
                return json.dumps(cg.get_exchanges(per_page), indent=2)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {str(e)}"

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)

# --- GitHub Unified Tool ---
class GitHubToolInput(BaseModel):
    action: Literal[
        "get_repository_info",
        "get_user_profile",
        "search_repositories",
        "get_repository_readme",
        "get_repository_languages",
        "get_repository_contributors",
        "get_trending_repositories",
        "get_repository_issues",
        "search_code",
        "get_repository_stargazers",
        "get_user_repositories"
    ]
    owner: Optional[str] = Field(None, description="Repository owner")
    repo: Optional[str] = Field(None, description="Repository name")
    username: Optional[str] = Field(None, description="GitHub username")
    query: Optional[str] = Field(None, description="Search query")
    state: Optional[str] = Field(None, description="Issue state (open, closed, all)")
    per_page: Optional[int] = Field(None, description="Results per page")
    page: Optional[int] = Field(None, description="Page number")
    type: Optional[str] = Field(None, description="Repository type (owner, member, all)")
    sort: Optional[str] = Field(None, description="Sort order")
    order: Optional[str] = Field(None, description="Sort direction")
    language: Optional[str] = Field(None, description="Programming language")
    since: Optional[str] = Field(None, description="Trending period (daily, weekly, monthly)")

class GitHubUnifiedTool(BaseTool):
    name: str = "github_data"
    description: str = "Unified tool for accessing GitHub repository and user data. Supports repo info, user profile, search, trending, issues, and more."
    args_schema: type = GitHubToolInput

    def _run(self, action, owner=None, repo=None, username=None, query=None, state=None, per_page=None, page=None, type=None, sort=None, order=None, language=None, since=None):
        gh = datasource_manager.get_source("github")
        if not gh:
            gh = GitHubDataSource()
            datasource_manager.register_source("github", gh)
        try:
            if action == "get_repository_info":
                return json.dumps(gh.get_repository_info(owner, repo), indent=2)
            elif action == "get_user_profile":
                return json.dumps(gh.get_user_profile(username), indent=2)
            elif action == "search_repositories":
                return json.dumps(gh.search_repositories(query, sort, order, per_page, page), indent=2)
            elif action == "get_repository_readme":
                return json.dumps(gh.get_repository_readme(owner, repo), indent=2)
            elif action == "get_repository_languages":
                return json.dumps(gh.get_repository_languages(owner, repo), indent=2)
            elif action == "get_repository_contributors":
                return json.dumps(gh.get_repository_contributors(owner, repo, per_page), indent=2)
            elif action == "get_trending_repositories":
                return json.dumps(gh.get_trending_repositories(since, language), indent=2)
            elif action == "get_repository_issues":
                return json.dumps(gh.get_repository_issues(owner, repo, state, per_page, page), indent=2)
            elif action == "search_code":
                return json.dumps(gh.search_code(query, sort, order, per_page, page), indent=2)
            elif action == "get_repository_stargazers":
                return json.dumps(gh.get_repository_stargazers(owner, repo, per_page), indent=2)
            elif action == "get_user_repositories":
                return json.dumps(gh.get_user_repositories(username, type, sort, per_page, page), indent=2)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {str(e)}"

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)

# --- News Unified Tool ---
class NewsToolInput(BaseModel):
    action: Literal[
        "get_top_headlines",
        "search_news",
        "get_news_by_domain",
        "get_news_sources",
        "get_news_by_topic",
        "get_breaking_news",
        "get_news_analysis"
    ]
    query: Optional[str] = Field(None, description="Search query or topic")
    country: Optional[str] = Field("us", description="Country code")
    category: Optional[str] = Field(None, description="News category")
    domain: Optional[str] = Field(None, description="News domain (e.g., 'bbc.com')")
    language: Optional[str] = Field(None, description="Language code")
    sort_by: Optional[str] = Field(None, description="Sort order")
    from_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    to_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    page_size: Optional[int] = Field(None, description="Results per page")
    page: Optional[int] = Field(None, description="Page number")
    topic: Optional[str] = Field(None, description="News topic")

class NewsUnifiedTool(BaseTool):
    name: str = "news_data"
    description: str = "Unified tool for accessing news articles and sources. Supports headlines, search, topics, domains, and more."
    args_schema: type = NewsToolInput

    def _run(self, action, query=None, country="us", category=None, domain=None, language=None, sort_by=None, from_date=None, to_date=None, page_size=None, page=None, topic=None):
        news = datasource_manager.get_source("news")
        if not news:
            api_key = os.getenv("NEWS_API_KEY")
            if not api_key:
                return "Error: NEWS_API_KEY environment variable not set"
            news = NewsDataSource(api_key)
            datasource_manager.register_source("news", news)
        try:
            if action == "get_top_headlines":
                return json.dumps(news.get_top_headlines(country, category, page_size, page), indent=2)
            elif action == "search_news":
                return json.dumps(news.search_news(query, language, sort_by, from_date, to_date, page_size, page), indent=2)
            elif action == "get_news_by_domain":
                return json.dumps(news.get_news_by_domain(domain, language, sort_by, page_size, page), indent=2)
            elif action == "get_news_sources":
                return json.dumps(news.get_news_sources(category, language, country), indent=2)
            elif action == "get_news_by_topic":
                return json.dumps(news.get_news_by_topic(topic, language, sort_by, page_size, page), indent=2)
            elif action == "get_breaking_news":
                return json.dumps(news.get_breaking_news(country, page_size), indent=2)
            elif action == "get_news_analysis":
                return json.dumps(news.get_news_analysis(query, language, page_size), indent=2)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {str(e)}"

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)

# List of all datasource tools
datasource_tools = [
    CoinGeckoTool(),
    GitHubUnifiedTool(),
    NewsUnifiedTool()
] 