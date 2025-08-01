import httpx
import os
from typing import Dict, List
from app.models.schemas import TwitterAnalysis
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json

class TwitterService:
    def __init__(self):
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.bearer_token}"} if self.bearer_token else {}
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
    
    async def analyze_profile(self, username: str, domain: str) -> TwitterAnalysis:
        async with httpx.AsyncClient() as client:
            try:
                user_data = await self._get_user_data(client, username)
                tweets_data = await self._get_recent_tweets(client, user_data.get("id", ""))
                
                analysis = await self._analyze_tweets(tweets_data, domain)
                
                return TwitterAnalysis(
                    username=username,
                    followers=user_data.get("public_metrics", {}).get("followers_count", 0),
                    technical_tweets_count=analysis.get("technical_count", 0),
                    domain_relevant_tweets=analysis.get("domain_relevant", 0),
                    engagement_rate=analysis.get("engagement_rate", 0.0),
                    domain_relevance_score=analysis.get("relevance_score", 0.0)
                )
            
            except Exception as e:
                return TwitterAnalysis(
                    username=username,
                    followers=0,
                    technical_tweets_count=0,
                    domain_relevant_tweets=0,
                    engagement_rate=0.0,
                    domain_relevance_score=0.0
                )
    
    async def _get_user_data(self, client: httpx.AsyncClient, username: str) -> Dict:
        if not self.bearer_token:
            return {}
        
        response = await client.get(
            f"https://api.twitter.com/2/users/by/username/{username}",
            headers=self.headers,
            params={"user.fields": "public_metrics"}
        )
        
        if response.status_code == 200:
            return response.json().get("data", {})
        return {}
    
    async def _get_recent_tweets(self, client: httpx.AsyncClient, user_id: str) -> List[Dict]:
        if not self.bearer_token or not user_id:
            return []
        
        response = await client.get(
            f"https://api.twitter.com/2/users/{user_id}/tweets",
            headers=self.headers,
            params={
                "max_results": 20,
                "tweet.fields": "public_metrics,created_at"
            }
        )
        
        if response.status_code == 200:
            return response.json().get("data", [])
        return []
    
    async def _analyze_tweets(self, tweets: List[Dict], domain: str) -> Dict:
        if not tweets:
            return {
                "technical_count": 0,
                "domain_relevant": 0,
                "engagement_rate": 0.0,
                "relevance_score": 0.0
            }
        
        system_message = SystemMessage(content=f"""
        Analyze these tweets for technical content relevance to {domain}.
        Return JSON with:
        - technical_count: number of technical tweets
        - domain_relevant: tweets relevant to {domain}
        - engagement_rate: average engagement rate (0-100)
        - relevance_score: overall relevance to {domain} (0-100)
        """)
        
        tweets_text = "\n\n---\n\n".join([tweet.get("text", "") for tweet in tweets])
        human_message = HumanMessage(content=f"Tweets:\n{tweets_text}")
        
        try:
            response = await self.llm.ainvoke([system_message, human_message])
            result = json.loads(response.content)
            return result
        except:
            return {
                "technical_count": 0,
                "domain_relevant": 0,
                "engagement_rate": 0.0,
                "relevance_score": 0.0
            }