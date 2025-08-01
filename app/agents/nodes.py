import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

load_dotenv()
from app.models.schemas import (
    Resume, JobDescription, GitHubAnalysis, LinkedInAnalysis,
    TwitterAnalysis, MediumAnalysis, ProjectAnalysis, CompanyAnalysis,
    CandidateAnalysis, TaskProgress, AnalysisStatus, Platform
)
from app.services.github_service import GitHubService
from app.services.linkedin_service import LinkedInService
from app.services.twitter_service import TwitterService
from app.services.medium_service import MediumService
from app.services.project_service import ProjectService
from app.services.company_service import CompanyService
from config.settings import settings
import json
from app.agents.report_generator import generate_comprehensive_report
from app.agents.streaming_analyzer import stream_comprehensive_analysis
from app.agents.llm_streaming_analyzer import generate_llm_streaming_analysis

llm = ChatOpenAI(model="gpt-4", temperature=0.1)

async def send_thinking_update(state: Dict[str, Any], content: str):
    """Send thinking update to WebSocket if available"""
    try:
        from app.api.websocket_manager import manager
        analysis_id = state.get("analysis_id")
        if analysis_id:
            await manager.send_thinking_update(analysis_id, "thinking", content)
    except Exception as e:
        print(f"Failed to send thinking update: {e}")

def update_task_progress(state: Dict[str, Any], task_id: str, status: AnalysisStatus, message: str = None):
    for task in state["progress"]:
        if task.task_id == task_id:
            task.status = status
            task.message = message
            if status == AnalysisStatus.IN_PROGRESS:
                task.started_at = datetime.now()
            elif status == AnalysisStatus.COMPLETED:
                task.completed_at = datetime.now()
                task.progress_percentage = 100.0
            break

async def resume_jd_matcher(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "resume_jd_match", AnalysisStatus.IN_PROGRESS, "Analyzing resume and job description match")
    
    try:
        resume = state["resume"]
        jd = state["job_description"]
        
        # Send thinking update
        thinking_content = f"""### Resume-JD Matching Analysis

**Candidate:** {resume.candidate_name}
**Position:** {jd.title} at {jd.company}
**Domain:** {jd.domain}

**Analyzing compatibility between:**
- **Candidate Skills:** {', '.join(resume.skills[:5])}{'...' if len(resume.skills) > 5 else ''}
- **Required Skills:** {', '.join(jd.requirements[:5])}{'...' if len(jd.requirements) > 5 else ''}
- **Experience Level Required:** {jd.experience_level}
- **Candidate Experience:** {resume.experience_years or 'Not specified'} years

🔍 **Sending to AI for detailed analysis...**"""
        
        await send_thinking_update(state, thinking_content)
        
        system_message = SystemMessage(content="""You are an AI hiring expert. Analyze the resume against the job description and provide a detailed matching score.
Consider skills, experience, education, and domain relevance.
Return your analysis as a JSON with 'score' (0-100) and 'analysis' fields.""")
        
        human_message = HumanMessage(content=f"""Job Description:
Title: {jd.title}
Company: {jd.company}
Requirements: {jd.requirements}
Preferred Skills: {jd.preferred_skills}
Experience Level: {jd.experience_level}
Domain: {jd.domain}

Resume:
Name: {resume.candidate_name}
Skills: {resume.skills}
Experience: {resume.experience}
Education: {resume.education}
Projects: {resume.projects}""")
        
        response = await llm.ainvoke([system_message, human_message])
        result = json.loads(response.content)
        
        # Send detailed result
        result_thinking = f"""✅ **Resume-JD Match Analysis Complete**

**Final Score:** {result['score']}/100

**AI Analysis:** {result.get('analysis', 'No detailed analysis provided').strip()}"""
        
        await send_thinking_update(state, result_thinking)
        
        state["resume_jd_score"] = result["score"]
        update_task_progress(state, "resume_jd_match", AnalysisStatus.COMPLETED, f"Match score: {result['score']}")
        
    except Exception as e:
        error_msg = f"❌ **Resume-JD matching failed:** {str(e)}"
        await send_thinking_update(state, error_msg)
        state["errors"].append(f"Resume-JD matching failed: {str(e)}")
        update_task_progress(state, "resume_jd_match", AnalysisStatus.FAILED, str(e))
    
    return state

async def github_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "github_analyze", AnalysisStatus.IN_PROGRESS, "Analyzing GitHub profile")
    
    try:
        print("DEBUG: GitHub analyzer starting")
        resume = state["resume"]
        github_profiles = [p for p in resume.social_profiles if p.platform == Platform.GITHUB]
        
        if not github_profiles:
            no_profile_msg = "### GitHub Analysis\n\n❌ **No GitHub profile found** in candidate's social profiles"
            await send_thinking_update(state, no_profile_msg)
            update_task_progress(state, "github_analyze", AnalysisStatus.COMPLETED, "No GitHub profile found")
            print("DEBUG: No GitHub profile found")
            return state
        
        github_url = str(github_profiles[0].url)
        username = github_url.split('/')[-1]
        print(f"DEBUG: Analyzing GitHub user: {username}")
        
        # Send initial thinking update
        thinking_content = f"""### GitHub Analysis

🔍 **Analyzing GitHub profile:** [@{username}]({github_url})
**Live Profile URL:** {github_url}
**Target Domain:** {state["job_description"].domain}

**Fetching data from GitHub API:**
- Repository data: https://api.github.com/users/{username}/repos
- User profile: https://api.github.com/users/{username}"""
        
        await send_thinking_update(state, thinking_content)
        
        # Create GitHub service and analyze
        github_service = GitHubService()
        analysis = await github_service.analyze_profile(username, state["job_description"].domain)
        
        if not analysis:
            print("DEBUG: GitHub service returned None")
            await send_thinking_update(state, "❌ **GitHub service returned no data**")
            update_task_progress(state, "github_analyze", AnalysisStatus.FAILED, "Service returned no data")
            return state
        
        print(f"DEBUG: GitHub analysis successful, setting state")
        state["github_analysis"] = analysis
        
        # Send detailed results with safe access
        result_thinking = f"""✅ **GitHub Analysis Complete for @{username}**

**Live Profile:** [{github_url}]({github_url})

**Profile Statistics:**
- **Public Repositories:** {getattr(analysis, 'public_repos_count', 0)}
- **Followers:** {getattr(analysis, 'followers', 0)}
- **Following:** {getattr(analysis, 'following', 0)}
- **Total Commits:** {getattr(analysis, 'total_commits', 0)}

**Analysis Scores:**
- **Code Quality:** {getattr(analysis, 'code_quality_score', 0)}/100
- **Project Complexity:** {getattr(analysis, 'project_complexity_score', 0)}/100  
- **Domain Relevance:** {getattr(analysis, 'domain_relevance_score', 0)}/100"""

        # Safely add languages
        languages = getattr(analysis, 'languages', {})
        if languages:
            lang_list = ', '.join([f"**{lang}** ({count} repos)" for lang, count in list(languages.items())[:5]])
            result_thinking += f"\n\n**Top Programming Languages:**\n{lang_list}"
        
        # Safely add repositories
        repositories = getattr(analysis, 'repositories', [])
        if repositories and len(repositories) > 0:
            result_thinking += "\n\n**Top Repositories:**"
            for repo in repositories[:3]:
                if repo and isinstance(repo, dict) and repo.get('name'):
                    repo_url = f"https://github.com/{username}/{repo.get('name', '')}"
                    result_thinking += f"""
- **[{repo.get('name', 'Unknown')}]({repo_url})** ({repo.get('language', 'N/A')})
  - ⭐ {repo.get('stars', 0)} stars, 🍴 {repo.get('forks', 0)} forks
  - Live URL: {repo_url}"""
                    desc = repo.get('description', '')
                    if desc:
                        result_thinking += f"\n  - {desc[:100]}{'...' if len(desc) > 100 else ''}"
        else:
            result_thinking += "\n\n**Repositories:** No accessible repositories found"
        
        await send_thinking_update(state, result_thinking)
        
        update_task_progress(state, "github_analyze", AnalysisStatus.COMPLETED, f"GitHub analysis completed for {username}")
        print("DEBUG: GitHub analyzer completed successfully")
        
    except Exception as e:
        print(f"DEBUG: GitHub analyzer error: {str(e)}")
        import traceback
        print(f"DEBUG: GitHub traceback: {traceback.format_exc()}")
        error_msg = f"❌ **GitHub analysis failed:** {str(e)}"
        await send_thinking_update(state, error_msg)
        state["errors"].append(f"GitHub analysis failed: {str(e)}")
        update_task_progress(state, "github_analyze", AnalysisStatus.FAILED, str(e))
    
    return state

async def linkedin_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "linkedin_analyze", AnalysisStatus.IN_PROGRESS, "Analyzing LinkedIn profile")
    
    try:
        resume = state["resume"]
        linkedin_profiles = [p for p in resume.social_profiles if p.platform == Platform.LINKEDIN]
        
        if not linkedin_profiles:
            update_task_progress(state, "linkedin_analyze", AnalysisStatus.COMPLETED, "No LinkedIn profile found")
            return state
        
        linkedin_service = LinkedInService()
        linkedin_url = str(linkedin_profiles[0].url)
        
        analysis = await linkedin_service.analyze_profile(linkedin_url, state["job_description"].domain)
        state["linkedin_analysis"] = analysis
        
        update_task_progress(state, "linkedin_analyze", AnalysisStatus.COMPLETED, "LinkedIn analysis completed")
        
    except Exception as e:
        state["errors"].append(f"LinkedIn analysis failed: {str(e)}")
        update_task_progress(state, "linkedin_analyze", AnalysisStatus.FAILED, str(e))
    
    return state

async def twitter_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "twitter_analyze", AnalysisStatus.IN_PROGRESS, "Analyzing Twitter profile")
    
    try:
        resume = state["resume"]
        twitter_profiles = [p for p in resume.social_profiles if p.platform == Platform.TWITTER]
        
        if not twitter_profiles:
            update_task_progress(state, "twitter_analyze", AnalysisStatus.COMPLETED, "No Twitter profile found")
            return state
        
        twitter_service = TwitterService()
        twitter_url = str(twitter_profiles[0].url)
        username = twitter_url.split('/')[-1]
        
        analysis = await twitter_service.analyze_profile(username, state["job_description"].domain)
        state["twitter_analysis"] = analysis
        
        update_task_progress(state, "twitter_analyze", AnalysisStatus.COMPLETED, f"Twitter analysis completed for @{username}")
        
    except Exception as e:
        state["errors"].append(f"Twitter analysis failed: {str(e)}")
        update_task_progress(state, "twitter_analyze", AnalysisStatus.FAILED, str(e))
    
    return state

async def medium_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "medium_analyze", AnalysisStatus.IN_PROGRESS, "Analyzing Medium profile")
    
    try:
        resume = state["resume"]
        medium_profiles = [p for p in resume.social_profiles if p.platform == Platform.MEDIUM]
        
        if not medium_profiles:
            update_task_progress(state, "medium_analyze", AnalysisStatus.COMPLETED, "No Medium profile found")
            return state
        
        medium_service = MediumService()
        medium_url = str(medium_profiles[0].url)
        username = medium_url.split('@')[-1] if '@' in medium_url else medium_url.split('/')[-1]
        
        analysis = await medium_service.analyze_profile(username, state["job_description"].domain)
        state["medium_analysis"] = analysis
        
        update_task_progress(state, "medium_analyze", AnalysisStatus.COMPLETED, f"Medium analysis completed for {username}")
        
    except Exception as e:
        state["errors"].append(f"Medium analysis failed: {str(e)}")
        update_task_progress(state, "medium_analyze", AnalysisStatus.FAILED, str(e))
    
    return state

async def project_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "project_evaluate", AnalysisStatus.IN_PROGRESS, "Evaluating projects")
    
    try:
        resume = state["resume"]
        project_service = ProjectService()
        
        project_analyses = []
        for project in resume.projects:
            if project.get("url"):
                analysis = await project_service.evaluate_project(project)
                project_analyses.append(analysis)
        
        state["project_analyses"] = project_analyses
        update_task_progress(state, "project_evaluate", AnalysisStatus.COMPLETED, f"Evaluated {len(project_analyses)} projects")
        
    except Exception as e:
        state["errors"].append(f"Project evaluation failed: {str(e)}")
        update_task_progress(state, "project_evaluate", AnalysisStatus.FAILED, str(e))
    
    return state

async def company_researcher(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "company_research", AnalysisStatus.IN_PROGRESS, "Researching previous companies")
    
    try:
        resume = state["resume"]
        company_service = CompanyService()
        
        company_analyses = []
        for experience in resume.experience:
            if experience.get("company"):
                analysis = await company_service.research_company(
                    experience["company"], 
                    experience.get("role", "")
                )
                company_analyses.append(analysis)
        
        state["company_analyses"] = company_analyses
        update_task_progress(state, "company_research", AnalysisStatus.COMPLETED, f"Researched {len(company_analyses)} companies")
        
    except Exception as e:
        state["errors"].append(f"Company research failed: {str(e)}")
        update_task_progress(state, "company_research", AnalysisStatus.FAILED, str(e))
    
    return state

async def final_scorer(state: Dict[str, Any]) -> Dict[str, Any]:
    print(f"DEBUG: Final scorer entry point reached")
    update_task_progress(state, "final_score", AnalysisStatus.IN_PROGRESS, "Calculating final score")
    
    try:
        print(f"DEBUG: Final scorer starting - state keys: {list(state.keys())}")
        print(f"DEBUG: State resume_jd_score: {state.get('resume_jd_score')}")
        print(f"DEBUG: State github_analysis exists: {state.get('github_analysis') is not None}")
        print(f"DEBUG: State linkedin_analysis exists: {state.get('linkedin_analysis') is not None}")
        print(f"DEBUG: State errors: {state.get('errors', [])}")
        
        # Send initial thinking update
        print(f"DEBUG: Sending initial thinking update")
        await send_thinking_update(state, "### Final Scoring & Analysis\n\n🧮 **Calculating comprehensive candidate score...**")
        print(f"DEBUG: Initial thinking update sent")
        
        print(f"DEBUG: Getting weights from settings")
        weights = settings.get_default_weights()
        if state.get("custom_weights"):
            weights.update(state["custom_weights"])
        
        print(f"DEBUG: Using weights: {weights}")
        
        print(f"DEBUG: Starting score calculation")
        final_score = 0.0
        score_breakdown = {}
        detailed_scoring = "**Detailed Score Calculation:**\n"
        
        # Resume-JD Match Score (always available)
        print(f"DEBUG: Processing resume-JD match score")
        resume_score = state.get("resume_jd_score", 0)
        resume_contribution = resume_score * weights.get("resume_jd_match", 0.25)
        final_score += resume_contribution
        score_breakdown["resume_jd_match"] = {"score": resume_score, "weight": weights.get("resume_jd_match", 0.25), "contribution": resume_contribution}
        detailed_scoring += f"- **Resume-JD Match:** {resume_score}/100 × {weights.get('resume_jd_match', 0.25):.0%} = {resume_contribution:.1f} points\n"
        print(f"DEBUG: Resume score processed - contribution: {resume_contribution}")
        
        # GitHub Analysis
        print(f"DEBUG: Processing GitHub analysis")
        if state.get("github_analysis"):
            try:
                github_analysis = state["github_analysis"]
                print(f"DEBUG: GitHub analysis type: {type(github_analysis)}")
                print(f"DEBUG: GitHub analysis attributes: code_quality={getattr(github_analysis, 'code_quality_score', 'missing')}, complexity={getattr(github_analysis, 'project_complexity_score', 'missing')}, domain={getattr(github_analysis, 'domain_relevance_score', 'missing')}")
                
                github_score = (
                    getattr(github_analysis, 'code_quality_score', 0) * 0.4 +
                    getattr(github_analysis, 'project_complexity_score', 0) * 0.3 +
                    getattr(github_analysis, 'domain_relevance_score', 0) * 0.3
                )
                github_contribution = github_score * weights.get("github_analysis", 0.20)
                final_score += github_contribution
                score_breakdown["github_analysis"] = {"score": github_score, "weight": weights.get("github_analysis", 0.20), "contribution": github_contribution}
                detailed_scoring += f"- **GitHub:** {github_score:.1f}/100 × {weights.get('github_analysis', 0.20):.0%} = {github_contribution:.1f} points\n"
                print(f"DEBUG: GitHub score processed - contribution: {github_contribution}")
            except Exception as e:
                print(f"DEBUG: GitHub scoring error: {e}")
                import traceback
                print(f"DEBUG: GitHub error traceback: {traceback.format_exc()}")
                detailed_scoring += f"- **GitHub:** Error processing (0 points)\n"
        else:
            print(f"DEBUG: No GitHub analysis found")
            detailed_scoring += f"- **GitHub:** Not available (0 points)\n"
        
        # LinkedIn Analysis
        if state.get("linkedin_analysis"):
            try:
                linkedin_score = state["linkedin_analysis"].domain_relevance_score
                linkedin_contribution = linkedin_score * weights.get("linkedin_analysis", 0.10)
                final_score += linkedin_contribution
                score_breakdown["linkedin_analysis"] = {"score": linkedin_score, "weight": weights.get("linkedin_analysis", 0.10), "contribution": linkedin_contribution}
                detailed_scoring += f"- **LinkedIn:** {linkedin_score}/100 × {weights.get('linkedin_analysis', 0.10):.0%} = {linkedin_contribution:.1f} points\n"
            except Exception as e:
                print(f"DEBUG: LinkedIn scoring error: {e}")
                detailed_scoring += f"- **LinkedIn:** Error processing (0 points)\n"
        else:
            detailed_scoring += f"- **LinkedIn:** Not available (0 points)\n"
        
        # Medium Analysis
        if state.get("medium_analysis"):
            try:
                medium_score = state["medium_analysis"].domain_relevance_score
                medium_contribution = medium_score * weights.get("technical_blogs", 0.15)
                final_score += medium_contribution
                score_breakdown["medium_analysis"] = {"score": medium_score, "weight": weights.get("technical_blogs", 0.15), "contribution": medium_contribution}
                detailed_scoring += f"- **Medium:** {medium_score}/100 × {weights.get('technical_blogs', 0.15):.0%} = {medium_contribution:.1f} points\n"
            except Exception as e:
                print(f"DEBUG: Medium scoring error: {e}")
                detailed_scoring += f"- **Medium:** Error processing (0 points)\n"
        else:
            detailed_scoring += f"- **Medium:** Not available (0 points)\n"
        
        # Project Analysis
        if state.get("project_analyses") and len(state["project_analyses"]) > 0:
            try:
                total_project_score = 0
                for project in state["project_analyses"]:
                    project_score = getattr(project, 'complexity_score', 0)
                    if hasattr(project, 'performance_score'):
                        project_score += getattr(project, 'performance_score', 0)
                    elif hasattr(project, 'responsiveness_score'):
                        project_score += getattr(project, 'responsiveness_score', 0)
                    total_project_score += project_score
                
                avg_project_score = total_project_score / len(state["project_analyses"]) / 2
                project_contribution = avg_project_score * weights.get("project_quality", 0.15)
                final_score += project_contribution
                score_breakdown["project_analysis"] = {"score": avg_project_score, "weight": weights.get("project_quality", 0.15), "contribution": project_contribution}
                detailed_scoring += f"- **Projects:** {avg_project_score:.1f}/100 × {weights.get('project_quality', 0.15):.0%} = {project_contribution:.1f} points\n"
            except Exception as e:
                print(f"DEBUG: Project scoring error: {e}")
                detailed_scoring += f"- **Projects:** Error processing (0 points)\n"
        else:
            detailed_scoring += f"- **Projects:** Not available (0 points)\n"
        
        # Company Analysis
        if state.get("company_analyses") and len(state["company_analyses"]) > 0:
            try:
                avg_company_score = sum(getattr(c, 'difficulty_score', 0) for c in state["company_analyses"]) / len(state["company_analyses"])
                company_contribution = avg_company_score * weights.get("work_experience", 0.10)
                final_score += company_contribution
                score_breakdown["company_analysis"] = {"score": avg_company_score, "weight": weights.get("work_experience", 0.10), "contribution": company_contribution}
                detailed_scoring += f"- **Companies:** {avg_company_score:.1f}/100 × {weights.get('work_experience', 0.10):.0%} = {company_contribution:.1f} points\n"
            except Exception as e:
                print(f"DEBUG: Company scoring error: {e}")
                detailed_scoring += f"- **Companies:** Error processing (0 points)\n"
        else:
            detailed_scoring += f"- **Companies:** Not available (0 points)\n"
        
        print(f"DEBUG: Clamping final score")
        final_score = min(100, max(0, final_score))
        print(f"DEBUG: Final calculated score: {final_score}")
        
        # Determine recommendation
        print(f"DEBUG: Getting scoring thresholds")
        thresholds = settings.get_scoring_thresholds()
        print(f"DEBUG: Thresholds: {thresholds}")
        
        if final_score >= thresholds["excellent"]:
            recommendation = "Strong Hire"
        elif final_score >= thresholds["good"]:
            recommendation = "Hire"
        elif final_score >= thresholds["average"]:
            recommendation = "Maybe"
        else:
            recommendation = "No Hire"
        
        print(f"DEBUG: Recommendation: {recommendation}")
        
        # Send final results
        print(f"DEBUG: Building detailed scoring")
        detailed_scoring += f"\n**Total Score:** {final_score:.1f}/100\n**Recommendation:** {recommendation}"
        print(f"DEBUG: Sending detailed scoring thinking update")
        await send_thinking_update(state, detailed_scoring)
        print(f"DEBUG: Detailed scoring sent")
        
        # Generate LLM-based streaming analysis for final results
        print(f"DEBUG: Starting LLM streaming analysis for final results")
        try:
            candidate_name = getattr(state['resume'], 'candidate_name', 'Unknown Candidate')
            job_title = getattr(state['job_description'], 'title', 'Unknown Position')
            job_company = getattr(state['job_description'], 'company', 'Unknown Company')
            job_domain = getattr(state['job_description'], 'domain', 'General')
            
            # Generate comprehensive LLM analysis that streams to final results
            detailed_report = await generate_llm_streaming_analysis(
                state, candidate_name, job_title, job_company, job_domain, 
                final_score, recommendation
            )
            print(f"DEBUG: LLM streaming analysis completed")
            
            # Also stream to thinking section for debugging
            await stream_comprehensive_analysis(
                state, candidate_name, job_title, job_company, job_domain, 
                final_score, recommendation, detailed_scoring, score_breakdown
            )
            
        except Exception as e:
            print(f"DEBUG: Error in LLM streaming analysis: {e}")
            import traceback
            print(f"DEBUG: LLM streaming analysis error traceback: {traceback.format_exc()}")
            detailed_report = f"Analysis completed with score {final_score:.1f}/100 and recommendation: {recommendation}"
        
        print(f"DEBUG: Creating CandidateAnalysis object")
        try:
            final_analysis = CandidateAnalysis(
                resume=state["resume"],
                job_description=state["job_description"],
                resume_jd_match_score=state.get("resume_jd_score", 0),
                github_analysis=state.get("github_analysis"),
                linkedin_analysis=state.get("linkedin_analysis"),
                twitter_analysis=state.get("twitter_analysis"),
                medium_analysis=state.get("medium_analysis"),
                project_analyses=state.get("project_analyses", []),
                company_analyses=state.get("company_analyses", []),
                overall_score=final_score,
                recommendation=recommendation,
                detailed_report=detailed_report
            )
            print(f"DEBUG: CandidateAnalysis object created successfully")
        except Exception as e:
            print(f"DEBUG: Error creating CandidateAnalysis: {e}")
            import traceback
            print(f"DEBUG: CandidateAnalysis error traceback: {traceback.format_exc()}")
            raise
        
        print(f"DEBUG: Setting final analysis in state")
        print(f"DEBUG: Final analysis object type: {type(final_analysis)}")
        print(f"DEBUG: Final analysis has detailed_report: {hasattr(final_analysis, 'detailed_report')}")
        if hasattr(final_analysis, 'detailed_report'):
            print(f"DEBUG: Detailed report length: {len(getattr(final_analysis, 'detailed_report', ''))}")
        
        state["final_analysis"] = final_analysis
        state["score_breakdown"] = score_breakdown
        print(f"DEBUG: Final analysis set in state")
        print(f"DEBUG: State final_analysis key exists: {'final_analysis' in state}")
        
        print(f"DEBUG: Sending completion thinking update")
        # Send final completion message
        completion_message = f"""🎉 **ANALYSIS COMPLETE!**

## Final Results Summary
- **Candidate:** {getattr(state['resume'], 'candidate_name', 'Unknown')}
- **Position:** {getattr(state['job_description'], 'title', 'Unknown')}
- **Overall Score:** {final_score:.1f}/100
- **Recommendation:** {recommendation}

✅ Comprehensive analysis report generated successfully!
"""
        await send_thinking_update(state, completion_message)
        print(f"DEBUG: Completion thinking update sent")
        
        print(f"DEBUG: Updating task progress to completed")
        update_task_progress(state, "final_score", AnalysisStatus.COMPLETED, f"Final score: {final_score:.1f} - {recommendation}")
        print(f"DEBUG: Task progress updated to completed")
        
        print(f"DEBUG: Final scorer completed successfully")
        
    except Exception as e:
        print(f"DEBUG: Final scorer error: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        error_msg = f"❌ **Final scoring failed:** {str(e)}"
        await send_thinking_update(state, error_msg)
        state["errors"].append(f"Final scoring failed: {str(e)}")
        update_task_progress(state, "final_score", AnalysisStatus.FAILED, str(e))
    
    return state

