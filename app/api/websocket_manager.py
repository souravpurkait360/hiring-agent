from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, analysis_id: str):
        await websocket.accept()
        if analysis_id not in self.active_connections:
            self.active_connections[analysis_id] = []
        self.active_connections[analysis_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, analysis_id: str):
        if analysis_id in self.active_connections:
            self.active_connections[analysis_id].remove(websocket)
            if not self.active_connections[analysis_id]:
                del self.active_connections[analysis_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def send_progress_update(self, analysis_id: str, state: Dict):
        print(f"DEBUG: WebSocket send_progress_update called for analysis {analysis_id}")
        print(f"DEBUG: Active connections for analysis: {analysis_id in self.active_connections}")
        
        if analysis_id in self.active_connections:
            print(f"DEBUG: Building progress message for {len(self.active_connections[analysis_id])} connections")
            
            progress_list = [
                {
                    "task_id": task.task_id,
                    "task_name": task.task_name,
                    "status": task.status,
                    "progress_percentage": task.progress_percentage,
                    "message": task.message
                }
                for task in state.get("progress", [])
            ]
            
            print(f"DEBUG: Progress list has {len(progress_list)} tasks")
            print(f"DEBUG: Final analysis exists: {state.get('final_analysis') is not None}")
            
            message = {
                "type": "progress_update",
                "analysis_id": analysis_id,
                "progress": progress_list,
                "final_analysis": state.get("final_analysis"),
                "thinking_data": self._extract_thinking_data(state)
            }
            
            print(f"DEBUG: Sending message to {len(self.active_connections[analysis_id])} connections")
            
            for connection in self.active_connections[analysis_id]:
                try:
                    await connection.send_text(json.dumps(message, default=str))
                    print(f"DEBUG: Message sent successfully to one connection")
                except Exception as e:
                    print(f"WebSocket send error: {e}")
                    import traceback
                    print(f"DEBUG: WebSocket error traceback: {traceback.format_exc()}")
                    pass
        else:
            print(f"DEBUG: No active connections found for analysis {analysis_id}")
    
    async def send_thinking_update(self, analysis_id: str, task_id: str, content: str):
        """Send thinking/analysis content for a specific task"""
        print(f"DEBUG: WebSocket send_thinking_update called for analysis {analysis_id}, task {task_id}")
        
        if analysis_id in self.active_connections:
            print(f"DEBUG: Sending thinking update to {len(self.active_connections[analysis_id])} connections")
            message = {
                "type": "thinking_update",
                "analysis_id": analysis_id,
                "task_id": task_id,
                "content": content
            }
            
            for connection in self.active_connections[analysis_id]:
                try:
                    await connection.send_text(json.dumps(message))
                    print(f"DEBUG: Thinking update sent successfully")
                except Exception as e:
                    print(f"WebSocket thinking update error: {e}")
                    import traceback
                    print(f"DEBUG: Thinking update error traceback: {traceback.format_exc()}")
                    pass
        else:
            print(f"DEBUG: No active connections for thinking update - analysis {analysis_id}")
    
    def _extract_thinking_data(self, state: Dict) -> Dict:
        """Extract analysis data for the thinking section"""
        print(f"DEBUG: Extracting thinking data from state")
        thinking_data = {}
        
        # GitHub Analysis
        if state.get("github_analysis"):
            github = state["github_analysis"]
            thinking_data["github"] = {
                "username": github.username,
                "public_repos": github.public_repos_count,
                "followers": github.followers,
                "total_commits": github.total_commits,
                "languages": github.languages,
                "code_quality_score": github.code_quality_score,
                "complexity_score": github.project_complexity_score,
                "domain_relevance": github.domain_relevance_score,
                "top_repos": github.repositories[:5]
            }
        
        # LinkedIn Analysis
        if state.get("linkedin_analysis"):
            linkedin = state["linkedin_analysis"]
            thinking_data["linkedin"] = {
                "technical_posts": linkedin.technical_posts_count,
                "domain_relevant_posts": linkedin.domain_relevant_posts,
                "connections": linkedin.connections,
                "endorsements": linkedin.endorsements,
                "certifications": linkedin.certifications,
                "domain_relevance": linkedin.domain_relevance_score
            }
        
        # Twitter Analysis
        if state.get("twitter_analysis"):
            twitter = state["twitter_analysis"]
            thinking_data["twitter"] = {
                "username": twitter.username,
                "followers": twitter.followers,
                "technical_tweets": twitter.technical_tweets_count,
                "domain_relevant_tweets": twitter.domain_relevant_tweets,
                "engagement_rate": twitter.engagement_rate,
                "domain_relevance": twitter.domain_relevance_score
            }
        
        # Medium Analysis
        if state.get("medium_analysis"):
            medium = state["medium_analysis"]
            thinking_data["medium"] = {
                "username": medium.username,
                "articles_count": medium.articles_count,
                "domain_relevant_articles": medium.domain_relevant_articles,
                "total_claps": medium.total_claps,
                "followers": medium.followers,
                "domain_relevance": medium.domain_relevance_score
            }
        
        # Project Analysis
        if state.get("project_analyses"):
            thinking_data["projects"] = [
                {
                    "name": project.project_name,
                    "is_live": project.is_live,
                    "url": str(project.url) if project.url else None,
                    "technologies": project.technologies,
                    "complexity_score": project.complexity_score,
                    "responsiveness_score": project.responsiveness_score,
                    "seo_score": project.seo_score,
                    "performance_score": project.performance_score
                }
                for project in state["project_analyses"]
            ]
        
        # Company Analysis
        if state.get("company_analyses"):
            thinking_data["companies"] = [
                {
                    "name": company.company_name,
                    "role": company.role,
                    "difficulty_score": company.difficulty_score,
                    "tier": company.company_tier,
                    "reputation": company.market_reputation
                }
                for company in state["company_analyses"]
            ]
        
        # Resume-JD Match
        if state.get("resume_jd_score"):
            thinking_data["resume_match"] = {
                "score": state["resume_jd_score"]
            }
        
        # Score breakdown if available
        if state.get("score_breakdown"):
            thinking_data["score_breakdown"] = state["score_breakdown"]
        
        return thinking_data

    async def send_final_analysis_stream(self, analysis_id: str, content: str, is_complete: bool = False):
        """Stream final analysis results in real-time"""
        print(f"DEBUG: WebSocket send_final_analysis_stream called for analysis {analysis_id}")
        
        if analysis_id in self.active_connections:
            print(f"DEBUG: Streaming final analysis to {len(self.active_connections[analysis_id])} connections")
            message = {
                "type": "final_analysis_stream",
                "analysis_id": analysis_id,
                "content": content,
                "is_complete": is_complete
            }
            
            for connection in self.active_connections[analysis_id]:
                try:
                    await connection.send_text(json.dumps(message))
                    print(f"DEBUG: Final analysis stream sent successfully")
                except Exception as e:
                    print(f"WebSocket final analysis stream error: {e}")
                    import traceback
                    print(f"DEBUG: Final analysis stream error traceback: {traceback.format_exc()}")
                    pass
        else:
            print(f"DEBUG: No active connections for final analysis stream - analysis {analysis_id}")

manager = ConnectionManager()