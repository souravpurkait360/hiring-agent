import httpx
import os
from typing import Dict, List, Optional
from app.models.schemas import GitHubAnalysis
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json

class GitHubService:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {"Authorization": f"token {self.token}"} if self.token else {}
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
    
    async def analyze_profile(self, username: str, domain: str) -> GitHubAnalysis:
        try:
            async with httpx.AsyncClient() as client:
                user_data = await self._get_user_data(client, username)
                repos_data = await self._get_repositories(client, username)
                
                # Ensure repos_data is a list and not None
                if not isinstance(repos_data, list):
                    repos_data = []
                
                # Filter out None repos
                repos_data = [repo for repo in repos_data if repo is not None and isinstance(repo, dict)]
                
                total_commits = sum(repo.get("size", 0) for repo in repos_data if repo)
                
                languages = {}
                for repo in repos_data:
                    if repo and repo.get("language"):
                        lang = repo["language"]
                        languages[lang] = languages.get(lang, 0) + 1
                
                code_quality_score = await self._analyze_code_quality(repos_data[:5])
                complexity_score = await self._analyze_project_complexity(repos_data[:5])
                domain_relevance = await self._analyze_domain_relevance(repos_data, domain)
                
                return GitHubAnalysis(
                    username=username,
                    public_repos_count=user_data.get("public_repos", 0),
                    followers=user_data.get("followers", 0),
                    following=user_data.get("following", 0),
                    total_commits=total_commits,
                    repositories=[{
                        "name": repo.get("name", "Unknown"),
                        "description": repo.get("description", ""),
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "language": repo.get("language", ""),
                        "updated_at": repo.get("updated_at", "")
                    } for repo in repos_data[:10] if repo and isinstance(repo, dict)],
                    languages=languages,
                    contribution_streak=await self._calculate_contribution_streak(client, username),
                    code_quality_score=code_quality_score,
                    project_complexity_score=complexity_score,
                    domain_relevance_score=domain_relevance
                )
        except Exception as e:
            print(f"GitHub service error: {e}")
            # Return a basic analysis with minimal data
            return GitHubAnalysis(
                username=username,
                public_repos_count=0,
                followers=0,
                following=0,
                total_commits=0,
                repositories=[],
                languages={},
                contribution_streak=0,
                code_quality_score=0.0,
                project_complexity_score=0.0,
                domain_relevance_score=0.0
            )
    
    async def _get_user_data(self, client: httpx.AsyncClient, username: str) -> Dict:
        try:
            response = await client.get(
                f"https://api.github.com/users/{username}",
                headers=self.headers,
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, dict) else {}
            else:
                print(f"GitHub user API error: {response.status_code}")
                return {}
        except Exception as e:
            print(f"GitHub user API exception: {e}")
            return {}
    
    async def _get_repositories(self, client: httpx.AsyncClient, username: str) -> List[Dict]:
        try:
            response = await client.get(
                f"https://api.github.com/users/{username}/repos?sort=updated&per_page=20",
                headers=self.headers,
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, list) else []
            else:
                print(f"GitHub repos API error: {response.status_code}")
                return []
        except Exception as e:
            print(f"GitHub repos API exception: {e}")
            return []
    
    async def _calculate_contribution_streak(self, client: httpx.AsyncClient, username: str) -> int:
        return 30
    
    async def _analyze_code_quality(self, repos: List[Dict]) -> float:
        if not repos:
            return 0.0
        
        system_message = SystemMessage(content="""Analyze the GitHub repositories and rate the code quality from 0-100.
Consider: README quality, documentation, project structure, naming conventions.
Return only a numeric score.""")
        
        repo_summary = "\n".join([
            f"- {repo['name']}: {repo.get('description', 'No description')} (Language: {repo.get('language', 'Unknown')})"
            for repo in repos
        ])
        
        human_message = HumanMessage(content=f"Repositories:\n{repo_summary}")
        
        try:
            response = await self.llm.ainvoke([system_message, human_message])
            return float(response.content.strip())
        except:
            return 50.0
    
    async def _analyze_project_complexity(self, repos: List[Dict]) -> float:
        if not repos:
            return 0.0
        
        complexity_score = 0.0
        for repo in repos:
            if repo.get("stargazers_count", 0) > 10:
                complexity_score += 20
            if repo.get("forks_count", 0) > 5:
                complexity_score += 15
            if repo.get("language") in ["Python", "JavaScript", "Java", "Go", "Rust"]:
                complexity_score += 10
        
        return min(100, complexity_score / len(repos) if repos else 0)
    
    async def _analyze_domain_relevance(self, repos: List[Dict], domain: str) -> float:
        if not repos:
            return 0.0
        
        system_message = SystemMessage(content=f"""Analyze how relevant these GitHub repositories are to the {domain} domain.
Rate from 0-100 based on project names, descriptions, and languages used.
Return only a numeric score.""")
        
        repo_summary = "\n".join([
            f"- {repo['name']}: {repo.get('description', 'No description')} (Language: {repo.get('language', 'Unknown')})"
            for repo in repos
        ])
        
        human_message = HumanMessage(content=f"Repositories:\n{repo_summary}")
        
        try:
            response = await self.llm.ainvoke([system_message, human_message])
            return float(response.content.strip())
        except:
            return 50.0