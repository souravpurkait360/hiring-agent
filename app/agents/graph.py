from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from typing import TypedDict, List, Optional, Dict, Any
from app.models.schemas import (
    CandidateAnalysis, Resume, JobDescription, TaskProgress, 
    AnalysisStatus, GitHubAnalysis, LinkedInAnalysis, 
    TwitterAnalysis, MediumAnalysis, ProjectAnalysis, CompanyAnalysis
)
from app.agents.nodes import (
    resume_jd_matcher,
    github_analyzer,
    linkedin_analyzer,
    twitter_analyzer,
    medium_analyzer,
    project_evaluator,
    company_researcher,
    final_scorer
)
import asyncio
from datetime import datetime

class AgentState(TypedDict):
    resume: Resume
    job_description: JobDescription
    analysis_id: str
    progress: List[TaskProgress]
    resume_jd_score: Optional[float]
    github_analysis: Optional[GitHubAnalysis]
    linkedin_analysis: Optional[LinkedInAnalysis]
    twitter_analysis: Optional[TwitterAnalysis]
    medium_analysis: Optional[MediumAnalysis]
    project_analyses: List[ProjectAnalysis]
    company_analyses: List[CompanyAnalysis]
    final_analysis: Optional[CandidateAnalysis]
    custom_weights: Optional[Dict[str, float]]
    errors: List[str]

def safe_analysis_wrapper(analysis_func, task_name):
    """Wrapper to ensure analysis tasks complete or fail gracefully"""
    async def wrapped_func(state):
        try:
            print(f"DEBUG: Starting {task_name} analysis")
            result = await analysis_func(state)
            print(f"DEBUG: Completed {task_name} analysis successfully")
            return result
        except Exception as e:
            print(f"DEBUG: {task_name} analysis failed with error: {e}")
            import traceback
            print(f"DEBUG: {task_name} traceback: {traceback.format_exc()}")
            
            # Update task progress to failed but continue workflow
            from app.models.schemas import AnalysisStatus
            for task in state.get("progress", []):
                if task.task_id == task_name.lower().replace(" ", "_"):
                    task.status = AnalysisStatus.FAILED
                    task.message = f"Failed: {str(e)}"
                    break
            
            state["errors"].append(f"{task_name} failed: {str(e)}")
            return state
    return wrapped_func

def create_hiring_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Wrap all analysis functions for safety
    workflow.add_node("resume_jd_match", safe_analysis_wrapper(resume_jd_matcher, "Resume JD Match"))
    workflow.add_node("github_analyze", safe_analysis_wrapper(github_analyzer, "GitHub Analysis"))
    workflow.add_node("linkedin_analyze", safe_analysis_wrapper(linkedin_analyzer, "LinkedIn Analysis"))
    workflow.add_node("twitter_analyze", safe_analysis_wrapper(twitter_analyzer, "Twitter Analysis"))
    workflow.add_node("medium_analyze", safe_analysis_wrapper(medium_analyzer, "Medium Analysis"))
    workflow.add_node("project_evaluate", safe_analysis_wrapper(project_evaluator, "Project Evaluation"))
    workflow.add_node("company_research", safe_analysis_wrapper(company_researcher, "Company Research"))
    workflow.add_node("final_score", safe_analysis_wrapper(final_scorer, "Final Scoring"))
    
    workflow.set_entry_point("resume_jd_match")
    
    # After resume_jd_match, run all analysis tasks in parallel
    for task in ["github_analyze", "linkedin_analyze", "twitter_analyze", 
                 "medium_analyze", "project_evaluate", "company_research"]:
        workflow.add_edge("resume_jd_match", task)
    
    # All analysis tasks feed into final scoring
    for task in ["github_analyze", "linkedin_analyze", "twitter_analyze", 
                 "medium_analyze", "project_evaluate", "company_research"]:
        workflow.add_edge(task, "final_score")
    
    workflow.add_edge("final_score", END)
    
    print("DEBUG: LangGraph workflow created with safe wrappers")
    
    return workflow.compile()

class HiringAgentOrchestrator:
    def __init__(self):
        self.graph = create_hiring_agent_graph()
        self.active_analyses: Dict[str, AgentState] = {}
        self.use_simple_workflow = True  # Enable simple workflow to bypass LangGraph issues
    
    async def start_analysis(
        self, 
        analysis_id: str,
        resume: Resume, 
        job_description: JobDescription,
        custom_weights: Optional[Dict[str, float]] = None,
        progress_callback = None
    ) -> AgentState:
        
        initial_state: AgentState = {
            "resume": resume,
            "job_description": job_description,
            "analysis_id": analysis_id,
            "progress": [
                TaskProgress(
                    task_id="resume_jd_match",
                    task_name="Resume and JD Matching",
                    status=AnalysisStatus.PENDING
                ),
                TaskProgress(
                    task_id="github_analyze",
                    task_name="GitHub Analysis",
                    status=AnalysisStatus.PENDING
                ),
                TaskProgress(
                    task_id="linkedin_analyze",
                    task_name="LinkedIn Analysis",
                    status=AnalysisStatus.PENDING
                ),
                TaskProgress(
                    task_id="twitter_analyze",
                    task_name="Twitter Analysis",
                    status=AnalysisStatus.PENDING
                ),
                TaskProgress(
                    task_id="medium_analyze",
                    task_name="Medium Analysis",
                    status=AnalysisStatus.PENDING
                ),
                TaskProgress(
                    task_id="project_evaluate",
                    task_name="Project Evaluation",
                    status=AnalysisStatus.PENDING
                ),
                TaskProgress(
                    task_id="company_research",
                    task_name="Company Research",
                    status=AnalysisStatus.PENDING
                ),
                TaskProgress(
                    task_id="final_score",
                    task_name="Final Scoring",
                    status=AnalysisStatus.PENDING
                )
            ],
            "resume_jd_score": None,
            "github_analysis": None,
            "linkedin_analysis": None,
            "twitter_analysis": None,
            "medium_analysis": None,
            "project_analyses": [],
            "company_analyses": [],
            "final_analysis": None,
            "custom_weights": custom_weights,
            "errors": []
        }
        
        self.active_analyses[analysis_id] = initial_state
        
        # Use simple sequential workflow to ensure completion
        if self.use_simple_workflow:
            return await self._run_simple_workflow(analysis_id, initial_state, progress_callback)
        
        try:
            print(f"DEBUG: Starting LangGraph execution for analysis {analysis_id}")
            final_state = initial_state
            step_count = 0
            
            # Add timeout to prevent infinite hanging
            import asyncio
            
            async def run_with_timeout():
                nonlocal final_state, step_count
                async for output in self.graph.astream(initial_state):
                    step_count += 1
                    print(f"DEBUG: LangGraph step {step_count} - output type: {type(output)}")
                    
                    # LangGraph 0.6+ returns dict with node names as keys
                    if isinstance(output, dict):
                        print(f"DEBUG: Processing dict output with keys: {list(output.keys())}")
                        for node_name, state in output.items():
                            print(f"DEBUG: Processing node '{node_name}' output")
                            final_state = state
                            self.active_analyses[analysis_id] = state
                            if progress_callback:
                                print(f"DEBUG: Calling progress callback for node '{node_name}'")
                                await progress_callback(analysis_id, state)
                            else:
                                print(f"DEBUG: No progress callback provided")
                    else:
                        # Fallback for different output format
                        print(f"DEBUG: Processing non-dict output")
                        final_state = output
                        self.active_analyses[analysis_id] = output
                        if progress_callback:
                            print(f"DEBUG: Calling progress callback for fallback output")
                            await progress_callback(analysis_id, output)
            
            # Run with 5 minute timeout
            try:
                await asyncio.wait_for(run_with_timeout(), timeout=300)
            except asyncio.TimeoutError:
                print(f"DEBUG: LangGraph execution timed out after 5 minutes")
                final_state["errors"].append("Analysis timed out after 5 minutes")
            
            print(f"DEBUG: LangGraph execution completed after {step_count} steps")
            print(f"DEBUG: Final state keys: {list(final_state.keys()) if isinstance(final_state, dict) else 'not a dict'}")
            return final_state
        
        except Exception as e:
            print(f"DEBUG: LangGraph execution error: {e}")
            import traceback
            print(f"DEBUG: LangGraph error traceback: {traceback.format_exc()}")
            initial_state["errors"].append(str(e))
            self.active_analyses[analysis_id] = initial_state
            return initial_state
    
    def get_analysis_progress(self, analysis_id: str) -> Optional[AgentState]:
        return self.active_analyses.get(analysis_id)
    
    async def _run_simple_workflow(self, analysis_id: str, state: AgentState, progress_callback):
        """Run a simplified sequential workflow to ensure completion"""
        print(f"DEBUG: Starting simple workflow for analysis {analysis_id}")
        
        try:
            # Step 1: Resume-JD Matching
            print(f"DEBUG: Running resume-JD matching")
            state = await resume_jd_matcher(state)
            self.active_analyses[analysis_id] = state
            if progress_callback:
                await progress_callback(analysis_id, state)
            
            # Step 2: Run analysis tasks with timeouts
            analysis_tasks = [
                ("GitHub", github_analyzer),
                ("LinkedIn", linkedin_analyzer), 
                ("Twitter", twitter_analyzer),
                ("Medium", medium_analyzer),
                ("Projects", project_evaluator),
                ("Companies", company_researcher)
            ]
            
            for task_name, task_func in analysis_tasks:
                print(f"DEBUG: Running {task_name} analysis")
                try:
                    import asyncio
                    state = await asyncio.wait_for(task_func(state), timeout=60)  # 1 minute timeout per task
                    print(f"DEBUG: {task_name} analysis completed")
                except asyncio.TimeoutError:
                    print(f"DEBUG: {task_name} analysis timed out")
                    state["errors"].append(f"{task_name} analysis timed out")
                except Exception as e:
                    print(f"DEBUG: {task_name} analysis failed: {e}")
                    state["errors"].append(f"{task_name} analysis failed: {str(e)}")
                
                self.active_analyses[analysis_id] = state
                if progress_callback:
                    await progress_callback(analysis_id, state)
            
            # Step 3: Final Scoring - ensure this always runs
            print(f"DEBUG: Running final scoring")
            try:
                import asyncio
                state = await asyncio.wait_for(final_scorer(state), timeout=120)  # 2 minute timeout for final scoring
                print(f"DEBUG: Final scoring completed successfully")
            except asyncio.TimeoutError:
                print(f"DEBUG: Final scoring timed out")
                state["errors"].append("Final scoring timed out")
                # Create a basic final analysis if scoring times out
                from app.models.schemas import CandidateAnalysis
                state["final_analysis"] = CandidateAnalysis(
                    resume=state["resume"],
                    job_description=state["job_description"],
                    resume_jd_match_score=state.get("resume_jd_score", 0),
                    github_analysis=state.get("github_analysis"),
                    linkedin_analysis=state.get("linkedin_analysis"),
                    twitter_analysis=state.get("twitter_analysis"),
                    medium_analysis=state.get("medium_analysis"),
                    project_analyses=state.get("project_analyses", []),
                    company_analyses=state.get("company_analyses", []),
                    overall_score=state.get("resume_jd_score", 0) * 0.25,  # Basic fallback score
                    recommendation="Analysis Incomplete",
                    detailed_report="Analysis completed with errors. Some components may have timed out."
                )
            except Exception as e:
                print(f"DEBUG: Final scoring failed: {e}")
                import traceback
                print(f"DEBUG: Final scoring error traceback: {traceback.format_exc()}")
                state["errors"].append(f"Final scoring failed: {str(e)}")
            
            self.active_analyses[analysis_id] = state
            if progress_callback:
                await progress_callback(analysis_id, state)
            
            print(f"DEBUG: Simple workflow completed")
            return state
            
        except Exception as e:
            print(f"DEBUG: Simple workflow error: {e}")
            import traceback
            print(f"DEBUG: Simple workflow traceback: {traceback.format_exc()}")
            state["errors"].append(f"Workflow error: {str(e)}")
            return state
    
    def cleanup_analysis(self, analysis_id: str):
        if analysis_id in self.active_analyses:
            del self.active_analyses[analysis_id]

orchestrator = HiringAgentOrchestrator()