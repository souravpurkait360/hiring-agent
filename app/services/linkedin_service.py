import httpx
import os
from typing import Dict, List
from app.models.schemas import LinkedInAnalysis
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from bs4 import BeautifulSoup

class LinkedInService:
    def __init__(self):
        self.token = os.getenv("LINKEDIN_TOKEN")
        from config.settings import settings
        self.llm = ChatOpenAI(model=settings.get_model(), temperature=0.1)
    
    async def analyze_profile(self, profile_url: str, domain: str) -> LinkedInAnalysis:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(profile_url, follow_redirects=True)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                profile_data = await self._extract_profile_data(soup)
                posts_data = await self._analyze_posts(profile_data.get("posts", []), domain)
                
                return LinkedInAnalysis(
                    profile_url=profile_url,
                    technical_posts_count=posts_data.get("technical_count", 0),
                    domain_relevant_posts=posts_data.get("domain_relevant", 0),
                    connections=profile_data.get("connections"),
                    endorsements=profile_data.get("endorsements", []),
                    certifications=profile_data.get("certifications", []),
                    domain_relevance_score=posts_data.get("relevance_score", 0.0)
                )
            
            except Exception as e:
                return LinkedInAnalysis(
                    profile_url=profile_url,
                    technical_posts_count=0,
                    domain_relevant_posts=0,
                    domain_relevance_score=0.0
                )
    
    async def _extract_profile_data(self, soup: BeautifulSoup) -> Dict:
        posts = []
        
        post_elements = soup.find_all('div', class_=['feed-shared-update-v2', 'share-update-card'])
        for post in post_elements[:10]:
            text_content = post.get_text(strip=True)
            if text_content:
                posts.append(text_content)
        
        return {
            "posts": posts,
            "connections": None,
            "endorsements": [],
            "certifications": []
        }
    
    async def _analyze_posts(self, posts: List[str], domain: str) -> Dict:
        if not posts:
            return {"technical_count": 0, "domain_relevant": 0, "relevance_score": 0.0}
        
        system_message = SystemMessage(content=f"""
        Analyze these LinkedIn posts for technical content relevance to {domain}.
        Return JSON with:
        - technical_count: number of technical posts
        - domain_relevant: posts relevant to {domain}
        - relevance_score: overall relevance (0-100)
        """)
        
        posts_text = "\n\n---\n\n".join(posts)
        human_message = HumanMessage(content=f"Posts:\n{posts_text}")
        
        try:
            response = await self.llm.ainvoke([system_message, human_message])
            import json
            result = json.loads(response.content)
            return result
        except:
            return {"technical_count": 0, "domain_relevant": 0, "relevance_score": 0.0}