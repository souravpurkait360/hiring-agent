import httpx
from typing import Dict
from app.models.schemas import CompanyAnalysis
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json

class CompanyService:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
    
    async def research_company(self, company_name: str, role: str) -> CompanyAnalysis:
        try:
            company_info = await self._research_company_info(company_name)
            role_difficulty = await self._analyze_role_difficulty(company_name, role, company_info)
            company_tier = await self._determine_company_tier(company_name, company_info)
            market_reputation = await self._analyze_market_reputation(company_name, company_info)
            
            return CompanyAnalysis(
                company_name=company_name,
                role=role,
                difficulty_score=role_difficulty,
                company_tier=company_tier,
                market_reputation=market_reputation
            )
        
        except Exception as e:
            return CompanyAnalysis(
                company_name=company_name,
                role=role,
                difficulty_score=50.0,
                company_tier="Unknown",
                market_reputation=50.0
            )
    
    async def _research_company_info(self, company_name: str) -> Dict:
        system_message = SystemMessage(content=f"""
        Provide information about {company_name} as a company.
        Return JSON with: size, industry, founded_year, notable_facts, reputation_score (0-100).
        If you don't have specific information, make reasonable estimates based on the company name.
        """)
        
        human_message = HumanMessage(content=f"Tell me about {company_name} company")
        
        try:
            response = await self.llm.ainvoke([system_message, human_message])
            return json.loads(response.content)
        except:
            return {
                "size": "Unknown",
                "industry": "Unknown",
                "founded_year": None,
                "notable_facts": [],
                "reputation_score": 50
            }
    
    async def _analyze_role_difficulty(self, company_name: str, role: str, company_info: Dict) -> float:
        system_message = SystemMessage(content=f"""
        Analyze the difficulty of getting the role "{role}" at {company_name}.
        Consider company reputation, role requirements, competition, and market standards.
        Return a difficulty score from 0-100 (100 being extremely difficult).
        """)
        
        context = f"""
        Company: {company_name}
        Role: {role}
        Company Info: {company_info}
        """
        
        human_message = HumanMessage(content=context)
        
        try:
            response = await self.llm.ainvoke([system_message, human_message])
            return float(response.content.strip())
        except:
            return 50.0
    
    async def _determine_company_tier(self, company_name: str, company_info: Dict) -> str:
        system_message = SystemMessage(content=f"""
        Classify {company_name} into one of these tiers based on size, reputation, and market position:
        - "FAANG": Facebook/Meta, Apple, Amazon, Netflix, Google
        - "Big Tech": Microsoft, Tesla, Uber, Airbnb, etc.
        - "Unicorn": High-value startups ($1B+ valuation)
        - "Large Enterprise": Established large companies
        - "Mid-size": Medium-sized companies
        - "Startup": Early-stage companies
        - "Unknown": Cannot determine
        
        Return only the tier name.
        """)
        
        context = f"""
        Company: {company_name}
        Company Info: {company_info}
        """
        
        human_message = HumanMessage(content=context)
        
        try:
            response = await self.llm.ainvoke([system_message, human_message])
            tier = response.content.strip().strip('"')
            valid_tiers = ["FAANG", "Big Tech", "Unicorn", "Large Enterprise", "Mid-size", "Startup", "Unknown"]
            return tier if tier in valid_tiers else "Unknown"
        except:
            return "Unknown"
    
    async def _analyze_market_reputation(self, company_name: str, company_info: Dict) -> float:
        reputation_score = company_info.get("reputation_score", 50)
        
        company_lower = company_name.lower()
        
        if any(faang in company_lower for faang in ['google', 'facebook', 'meta', 'apple', 'amazon', 'netflix']):
            reputation_score = max(reputation_score, 95)
        elif any(bigtech in company_lower for bigtech in ['microsoft', 'tesla', 'uber', 'airbnb', 'twitter', 'salesforce']):
            reputation_score = max(reputation_score, 85)
        elif 'startup' in company_lower or 'inc' in company_lower:
            reputation_score = min(reputation_score, 70)
        
        return min(100, max(0, reputation_score))