import httpx
import os
from typing import Dict, List
from app.models.schemas import MediumAnalysis
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from bs4 import BeautifulSoup
import json

class MediumService:
    def __init__(self):
        self.token = os.getenv("MEDIUM_TOKEN")
        from config.settings import settings
        self.llm = ChatOpenAI(model=settings.get_model(), temperature=0.1)
    
    async def analyze_profile(self, username: str, domain: str) -> MediumAnalysis:
        async with httpx.AsyncClient() as client:
            try:
                profile_url = f"https://medium.com/@{username}"
                response = await client.get(profile_url, follow_redirects=True)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                articles_data = await self._extract_articles(soup)
                analysis = await self._analyze_articles(articles_data, domain)
                
                return MediumAnalysis(
                    username=username,
                    articles_count=len(articles_data),
                    domain_relevant_articles=analysis.get("domain_relevant", 0),
                    total_claps=analysis.get("total_claps", 0),
                    followers=analysis.get("followers", 0),
                    domain_relevance_score=analysis.get("relevance_score", 0.0)
                )
            
            except Exception as e:
                return MediumAnalysis(
                    username=username,
                    articles_count=0,
                    domain_relevant_articles=0,
                    total_claps=0,
                    followers=0,
                    domain_relevance_score=0.0
                )
    
    async def _extract_articles(self, soup: BeautifulSoup) -> List[Dict]:
        articles = []
        
        article_elements = soup.find_all('article') or soup.find_all('div', class_=['postArticle', 'streamItem'])
        
        for article in article_elements[:10]:
            title_elem = article.find('h1') or article.find('h2') or article.find('h3')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            content_elem = article.find('div', class_=['postArticle-content', 'graf'])
            content = content_elem.get_text(strip=True)[:500] if content_elem else ""
            
            claps_elem = article.find('button', {'data-action': 'show-recommends'})
            claps = 0
            if claps_elem:
                claps_text = claps_elem.get_text(strip=True)
                try:
                    claps = int(''.join(filter(str.isdigit, claps_text)))
                except:
                    claps = 0
            
            if title or content:
                articles.append({
                    "title": title,
                    "content": content,
                    "claps": claps
                })
        
        return articles
    
    async def _analyze_articles(self, articles: List[Dict], domain: str) -> Dict:
        if not articles:
            return {
                "domain_relevant": 0,
                "total_claps": 0,
                "followers": 0,
                "relevance_score": 0.0
            }
        
        system_message = SystemMessage(content=f"""
        Analyze these Medium articles for relevance to {domain}.
        Return JSON with:
        - domain_relevant: number of articles relevant to {domain}
        - total_claps: sum of all claps
        - relevance_score: overall domain relevance (0-100)
        """)
        
        articles_text = "\n\n---\n\n".join([
            f"Title: {article.get('title', '')}\nContent: {article.get('content', '')[:200]}..."
            for article in articles
        ])
        
        human_message = HumanMessage(content=f"Articles:\n{articles_text}")
        
        try:
            response = await self.llm.ainvoke([system_message, human_message])
            result = json.loads(response.content)
            result["total_claps"] = sum(article.get("claps", 0) for article in articles)
            return result
        except:
            return {
                "domain_relevant": 0,
                "total_claps": sum(article.get("claps", 0) for article in articles),
                "followers": 0,
                "relevance_score": 0.0
            }