import asyncio
import os
import re
import json
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
from app.agents.llm_streaming_analyzer import generate_llm_streaming_analysis

llm = ChatOpenAI(model=settings.get_model(), temperature=0.1)

async def send_thinking_update(state: Dict[str, Any], content: str):
    """Send thinking update to WebSocket if available"""
    try:
        from app.api.websocket_manager import manager
        analysis_id = state.get("analysis_id")
        if analysis_id:
            await manager.send_thinking_update(analysis_id, "thinking", content)
    except Exception as e:
        pass

def update_task_progress(state: Dict[str, Any], task_id: str, status: AnalysisStatus, message: str = None, score: float = None):
    for task in state["progress"]:
        if task.task_id == task_id:
            task.status = status
            task.message = message
            if score is not None:
                task.score = score
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
        
        system_message = SystemMessage(content="""You are an expert hiring analyst. Analyze how well a candidate's resume matches a job description.

🚨 CRITICAL RULE: You MUST ONLY evaluate the candidate against the exact skills, technologies, and requirements explicitly listed in the job description provided. DO NOT evaluate against any other skills, frameworks, or technologies not mentioned in the job requirements.

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON - no markdown, no explanations, no additional text
2. Provide a numerical score from 0-100 based on overall match quality
3. Include detailed analysis explaining the score
4. ONLY evaluate against skills/technologies/requirements EXPLICITLY listed in the job description
5. Do NOT mention any skills, technologies, or requirements that are not in the job description
6. Do NOT penalize for missing skills that are not listed in the job requirements
7. Do NOT assume additional skills are required beyond what is stated

REQUIRED JSON FORMAT:
{
    "score": 85,
    "analysis": "Detailed explanation of the match quality, highlighting strengths and gaps ONLY for requirements explicitly listed in the job description"
}

SCORING CRITERIA:
- Skills Match (40%): How well candidate's skills align with ONLY the requirements explicitly listed in the job description
- Experience Level (25%): Years of experience vs requirements stated in job description
- Domain Relevance (20%): Industry/domain experience match as specified in job description
- Education (10%): Educational background relevance to job requirements
- Projects (5%): Relevant project experience for the specific role

SCORING SCALE:
- 90-100: Exceptional match, meets all explicitly stated requirements
- 80-89: Strong match, meets most explicitly stated requirements
- 70-79: Good match, meets core explicitly stated requirements with minor gaps
- 60-69: Acceptable match, meets some explicitly stated requirements
- 50-59: Partial match, meets few explicitly stated requirements
- 0-49: Poor match, does not meet most explicitly stated requirements

FORBIDDEN ACTIONS:
❌ Do NOT mention skills like Java, Go, AWS, GCP, Redis unless they are explicitly listed in the job requirements
❌ Do NOT evaluate against "commonly expected" skills for the role type
❌ Do NOT assume additional technical requirements beyond what is stated
❌ Do NOT use phrases like "typically required for this role" or "standard for this position"

Example Output:
{
    "score": 78,
    "analysis": "Candidate demonstrates strong match with 4 out of 5 explicitly required skills listed in the job description: JavaScript, React, Node.js, and MongoDB. Experience level of 3 years meets the stated 2+ years requirement. Has relevant project experience with the specific technologies mentioned in the requirements. Only gap is in PostgreSQL which is listed as a requirement."
}""")
        
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
        
        # Clean up response content
        response_content = response.content.strip()
        
        # Remove markdown code blocks if present
        if response_content.startswith('```json'):
            response_content = response_content[7:]
        if response_content.startswith('```'):
            response_content = response_content[3:]
        if response_content.endswith('```'):
            response_content = response_content[:-3]
        
        response_content = response_content.strip()
        
        # Parse JSON with error handling
        try:
            result = json.loads(response_content)
        except json.JSONDecodeError as json_error:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except:
                    # Fallback with default values
                    result = {"score": 50, "analysis": "Failed to parse AI response, assigned default score"}
            else:
                result = {"score": 50, "analysis": "Failed to parse AI response, assigned default score"}
        
        # Validate result structure
        if not isinstance(result, dict) or "score" not in result:
            result = {"score": 50, "analysis": "Invalid response format, assigned default score"}
        
        # Ensure score is valid
        try:
            result["score"] = max(0, min(100, float(result["score"])))
        except (ValueError, TypeError):
            result["score"] = 50
        
        # Send detailed result
        result_thinking = f"""✅ **Resume-JD Match Analysis Complete**

**Final Score:** {result['score']}/100

**AI Analysis:** {result.get('analysis', 'No detailed analysis provided').strip()}"""
        
        await send_thinking_update(state, result_thinking)
        
        state["resume_jd_score"] = result["score"]
        update_task_progress(state, "resume_jd_match", AnalysisStatus.COMPLETED, f"Match score: {result['score']}", score=result["score"])
        
    except Exception as e:
        error_msg = f"❌ **Resume-JD matching failed:** {str(e)}"
        await send_thinking_update(state, error_msg)
        state["errors"].append(f"Resume-JD matching failed: {str(e)}")
        update_task_progress(state, "resume_jd_match", AnalysisStatus.FAILED, str(e))
    
    return state

async def github_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "github_analyze", AnalysisStatus.IN_PROGRESS, "Analyzing GitHub profile")
    
    try:
        resume = state["resume"]
        github_profiles = [p for p in resume.social_profiles if p.platform == Platform.GITHUB]
        
        if not github_profiles:
            no_profile_msg = "### GitHub Analysis\n\n❌ **No GitHub profile found** in candidate's social profiles"
            await send_thinking_update(state, no_profile_msg)
            update_task_progress(state, "github_analyze", AnalysisStatus.COMPLETED, "No GitHub profile found")
            return state
        
        github_url = str(github_profiles[0].url)
        username = github_url.split('/')[-1]
        
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
            await send_thinking_update(state, "❌ **GitHub service returned no data**")
            update_task_progress(state, "github_analyze", AnalysisStatus.FAILED, "Service returned no data")
            return state
        
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
        
        # Calculate overall GitHub score based on analysis metrics
        github_overall_score = (
            getattr(analysis, 'code_quality_score', 0) * 0.4 +
            getattr(analysis, 'project_complexity_score', 0) * 0.3 +
            getattr(analysis, 'domain_relevance_score', 0) * 0.3
        )
        
        update_task_progress(state, "github_analyze", AnalysisStatus.COMPLETED, f"GitHub analysis completed for {username}", score=github_overall_score)
        
    except Exception as e:
        import traceback
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
            update_task_progress(state, "linkedin_analyze", AnalysisStatus.COMPLETED, "No LinkedIn profile found", score=0)
            return state
        
        linkedin_service = LinkedInService()
        linkedin_url = str(linkedin_profiles[0].url)
        
        analysis = await linkedin_service.analyze_profile(linkedin_url, state["job_description"].domain)
        state["linkedin_analysis"] = analysis
        
        # Use domain relevance score as the main LinkedIn score, but ensure it's reasonable
        linkedin_score = getattr(analysis, 'domain_relevance_score', 0)
        
        # If no technical posts found, set score to 0
        technical_posts = getattr(analysis, 'technical_posts_count', 0)
        if technical_posts == 0:
            linkedin_score = 0
        
        update_task_progress(state, "linkedin_analyze", AnalysisStatus.COMPLETED, "LinkedIn analysis completed", score=linkedin_score)
        
    except Exception as e:
        state["errors"].append(f"LinkedIn analysis failed: {str(e)}")
        update_task_progress(state, "linkedin_analyze", AnalysisStatus.FAILED, str(e), score=0)
    
    return state

async def twitter_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "twitter_analyze", AnalysisStatus.IN_PROGRESS, "Analyzing Twitter profile")
    
    try:
        resume = state["resume"]
        twitter_profiles = [p for p in resume.social_profiles if p.platform == Platform.TWITTER]
        
        if not twitter_profiles:
            update_task_progress(state, "twitter_analyze", AnalysisStatus.COMPLETED, "No Twitter profile found", score=0)
            return state
        
        twitter_service = TwitterService()
        twitter_url = str(twitter_profiles[0].url)
        username = twitter_url.split('/')[-1]
        
        analysis = await twitter_service.analyze_profile(username, state["job_description"].domain)
        
        # Check if analysis is valid and has meaningful content
        if not analysis:
            twitter_score = 0
            state["twitter_analysis"] = None
        else:
            state["twitter_analysis"] = analysis
            
            # Use domain relevance score as the main Twitter score, but ensure it's reasonable
            twitter_score = getattr(analysis, 'domain_relevance_score', 0)
            
            # If no technical tweets found OR followers is 0, set score to 0
            technical_tweets = getattr(analysis, 'technical_tweets_count', 0)
            followers = getattr(analysis, 'followers', 0)
            if technical_tweets == 0 or followers == 0:
                twitter_score = 0
        
        update_task_progress(state, "twitter_analyze", AnalysisStatus.COMPLETED, f"Twitter analysis completed for @{username}", score=twitter_score)
        
    except Exception as e:
        state["errors"].append(f"Twitter analysis failed: {str(e)}")
        update_task_progress(state, "twitter_analyze", AnalysisStatus.FAILED, str(e), score=0)
    
    return state

async def medium_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "medium_analyze", AnalysisStatus.IN_PROGRESS, "Analyzing Medium profile")
    
    try:
        resume = state["resume"]
        medium_profiles = [p for p in resume.social_profiles if p.platform == Platform.MEDIUM]
        
        if not medium_profiles:
            update_task_progress(state, "medium_analyze", AnalysisStatus.COMPLETED, "No Medium profile found", score=0)
            return state
        
        medium_service = MediumService()
        medium_url = str(medium_profiles[0].url)
        username = medium_url.split('@')[-1] if '@' in medium_url else medium_url.split('/')[-1]
        
        analysis = await medium_service.analyze_profile(username, state["job_description"].domain)
        
        # Check if analysis is valid and has meaningful content
        if not analysis:
            medium_score = 0
            state["medium_analysis"] = None
        else:
            state["medium_analysis"] = analysis
            
            # Use domain relevance score as the main Medium score, but ensure it's reasonable
            medium_score = getattr(analysis, 'domain_relevance_score', 0)
            
            # If no articles found OR no domain relevant articles, set score to 0
            articles_count = getattr(analysis, 'articles_count', 0)
            domain_relevant_articles = getattr(analysis, 'domain_relevant_articles', 0)
            if articles_count == 0 or domain_relevant_articles == 0:
                medium_score = 0
        
        update_task_progress(state, "medium_analyze", AnalysisStatus.COMPLETED, f"Medium analysis completed for {username}", score=medium_score)
        
    except Exception as e:
        state["errors"].append(f"Medium analysis failed: {str(e)}")
        update_task_progress(state, "medium_analyze", AnalysisStatus.FAILED, str(e), score=0)
    
    return state

async def project_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "project_evaluate", AnalysisStatus.IN_PROGRESS, "Evaluating projects")
    
    try:
        resume = state["resume"]
        project_service = ProjectService()
        
        project_analyses = []
        projects_with_urls = 0
        total_projects = len(resume.projects)
        
        for project in resume.projects:
            if project.get("url"):
                analysis = await project_service.evaluate_project(project)
                project_analyses.append(analysis)
                projects_with_urls += 1
        
        state["project_analyses"] = project_analyses
        
        # Calculate average project score
        if project_analyses:
            project_scores = []
            for analysis in project_analyses:
                # Average of complexity, performance, responsiveness, and SEO scores
                avg_score = (
                    getattr(analysis, 'complexity_score', 0) +
                    getattr(analysis, 'performance_score', 0) + 
                    getattr(analysis, 'responsiveness_score', 0) +
                    getattr(analysis, 'seo_score', 0)
                ) / 4
                project_scores.append(avg_score)
            overall_project_score = sum(project_scores) / len(project_scores)
            
            # Give partial credit for projects without URLs (assume they're 50% as valuable)
            if total_projects > projects_with_urls:
                projects_without_urls = total_projects - projects_with_urls
                # Add 50% credit for projects without URLs
                overall_project_score = (overall_project_score * projects_with_urls + 25 * projects_without_urls) / total_projects
        elif total_projects > 0:
            # If no projects have URLs but projects exist, give some minimal credit
            overall_project_score = 25  # Basic project existence credit
        else:
            overall_project_score = 0
        
        update_task_progress(state, "project_evaluate", AnalysisStatus.COMPLETED, f"Evaluated {len(project_analyses)} projects", score=overall_project_score)
        
    except Exception as e:
        state["errors"].append(f"Project evaluation failed: {str(e)}")
        update_task_progress(state, "project_evaluate", AnalysisStatus.FAILED, str(e), score=0)
    
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
        
        # Calculate average company/work experience score
        if company_analyses:
            company_scores = []
            for analysis in company_analyses:
                difficulty_score = getattr(analysis, 'difficulty_score', 0)
                market_reputation = getattr(analysis, 'market_reputation', 0)
                company_tier = getattr(analysis, 'company_tier', 'Unknown')
                
                # If we got default values (50.0) and tier is Unknown, this indicates failed analysis
                if difficulty_score == 50.0 and market_reputation == 50.0 and company_tier == "Unknown":
                    # This is likely a failed analysis with default values, give it a low score
                    avg_score = 15.0
                else:
                    # Average of difficulty and reputation scores
                    avg_score = (difficulty_score + market_reputation) / 2
                
                company_scores.append(avg_score)
            overall_company_score = sum(company_scores) / len(company_scores)
        else:
            overall_company_score = 0
            
        update_task_progress(state, "company_research", AnalysisStatus.COMPLETED, f"Researched {len(company_analyses)} companies", score=overall_company_score)
        
    except Exception as e:
        state["errors"].append(f"Company research failed: {str(e)}")
        update_task_progress(state, "company_research", AnalysisStatus.FAILED, str(e), score=0)
    
    return state

async def final_scorer(state: Dict[str, Any]) -> Dict[str, Any]:
    update_task_progress(state, "final_score", AnalysisStatus.IN_PROGRESS, "Calculating final score")
    
    try:
        
        # Send initial thinking update
        await send_thinking_update(state, "### Final Scoring & Analysis\n\n🧮 **Calculating comprehensive candidate score...**")
        
        # Get weights based on the selected mode
        weight_mode = state.get("weight_mode", "professional")
        weights = settings.get_default_weights(weight_mode)
        if state.get("custom_weights"):
            weights.update(state["custom_weights"])
        
        
        final_score = 0.0
        score_breakdown = {}
        detailed_scoring = "**Detailed Score Calculation:**\n"
        
        # Resume-JD Match Score (always available)
        resume_score = state.get("resume_jd_score", 0)
        resume_contribution = resume_score * weights.get("resume_jd_match", 0.25)
        final_score += resume_contribution
        score_breakdown["resume_jd_match"] = {"score": resume_score, "weight": weights.get("resume_jd_match", 0.25), "contribution": resume_contribution}
        detailed_scoring += f"- **Resume-JD Match:** {resume_score}/100 × {weights.get('resume_jd_match', 0.25):.0%} = {resume_contribution:.1f} points\n"
        
        # GitHub Analysis
        if state.get("github_analysis"):
            try:
                github_analysis = state["github_analysis"]
                
                github_score = (
                    getattr(github_analysis, 'code_quality_score', 0) * 0.4 +
                    getattr(github_analysis, 'project_complexity_score', 0) * 0.3 +
                    getattr(github_analysis, 'domain_relevance_score', 0) * 0.3
                )
                github_contribution = github_score * weights.get("github_analysis", 0.20)
                final_score += github_contribution
                score_breakdown["github_analysis"] = {"score": github_score, "weight": weights.get("github_analysis", 0.20), "contribution": github_contribution}
                detailed_scoring += f"- **GitHub:** {github_score:.1f}/100 × {weights.get('github_analysis', 0.20):.0%} = {github_contribution:.1f} points\n"
            except Exception as e:
                import traceback
                detailed_scoring += f"- **GitHub:** Error processing (0 points)\n"
        else:
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
                detailed_scoring += f"- **Medium:** Error processing (0 points)\n"
        else:
            detailed_scoring += f"- **Medium:** Not available (0 points)\n"
        
        # Twitter Analysis (Social Presence)
        if state.get("twitter_analysis"):
            try:
                twitter_score = getattr(state["twitter_analysis"], 'domain_relevance_score', 0)
                twitter_contribution = twitter_score * weights.get("social_presence", 0.05)
                final_score += twitter_contribution
                score_breakdown["twitter_analysis"] = {"score": twitter_score, "weight": weights.get("social_presence", 0.05), "contribution": twitter_contribution}
                detailed_scoring += f"- **Twitter:** {twitter_score}/100 × {weights.get('social_presence', 0.05):.0%} = {twitter_contribution:.1f} points\n"
            except Exception as e:
                detailed_scoring += f"- **Twitter:** Error processing (0 points)\n"
        else:
            detailed_scoring += f"- **Twitter:** Not available (0 points)\n"
        
        # Project Analysis
        if state.get("project_analyses") and len(state["project_analyses"]) > 0:
            try:
                project_scores = []
                for analysis in state["project_analyses"]:
                    # Use the same logic as project_evaluator: average of all scores
                    avg_score = (
                        getattr(analysis, 'complexity_score', 0) +
                        getattr(analysis, 'performance_score', 0) + 
                        getattr(analysis, 'responsiveness_score', 0) +
                        getattr(analysis, 'seo_score', 0)
                    ) / 4
                    project_scores.append(avg_score)
                
                avg_project_score = sum(project_scores) / len(project_scores)
                project_contribution = avg_project_score * weights.get("project_quality", 0.15)
                final_score += project_contribution
                score_breakdown["project_analysis"] = {"score": avg_project_score, "weight": weights.get("project_quality", 0.15), "contribution": project_contribution}
                detailed_scoring += f"- **Projects:** {avg_project_score:.1f}/100 × {weights.get('project_quality', 0.15):.0%} = {project_contribution:.1f} points\n"
            except Exception as e:
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
                detailed_scoring += f"- **Companies:** Error processing (0 points)\n"
        else:
            detailed_scoring += f"- **Companies:** Not available (0 points)\n"
        
        final_score = min(100, max(0, final_score))
        
        # Determine recommendation
        thresholds = settings.get_scoring_thresholds()
        
        if final_score >= thresholds["excellent"]:
            recommendation = "Strong Hire"
        elif final_score >= thresholds["good"]:
            recommendation = "Hire"
        elif final_score >= thresholds["average"]:
            recommendation = "Maybe"
        else:
            recommendation = "No Hire"
        
        
        # Send final results
        detailed_scoring += f"\n**Total Score:** {final_score:.1f}/100\n**Recommendation:** {recommendation}"
        await send_thinking_update(state, detailed_scoring)
        
        # Generate comprehensive LLM report
        try:
            candidate_name = getattr(state['resume'], 'candidate_name', 'Unknown Candidate')
            job_title = getattr(state['job_description'], 'title', 'Unknown Position')
            job_company = getattr(state['job_description'], 'company', 'Unknown Company')
            job_domain = getattr(state['job_description'], 'domain', 'General')
            
            # Generate the comprehensive LLM report
            from app.agents.llm_streaming_analyzer import generate_llm_streaming_analysis
            detailed_report = await generate_llm_streaming_analysis(
                state, candidate_name, job_title, job_company, job_domain, 
                final_score, recommendation
            )
            
            
        except Exception as e:
            import traceback
            detailed_report = f"Analysis completed with score {final_score:.1f}/100 and recommendation: {recommendation}"
        
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
        except Exception as e:
            import traceback
            raise
        
        state["final_analysis"] = final_analysis
        state["score_breakdown"] = score_breakdown
        
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
        
        update_task_progress(state, "final_score", AnalysisStatus.COMPLETED, f"Final score: {final_score:.1f} - {recommendation}", score=final_score)
        
        
    except Exception as e:
        import traceback
        error_msg = f"❌ **Final scoring failed:** {str(e)}"
        await send_thinking_update(state, error_msg)
        state["errors"].append(f"Final scoring failed: {str(e)}")
        update_task_progress(state, "final_score", AnalysisStatus.FAILED, str(e))
    
    return state

