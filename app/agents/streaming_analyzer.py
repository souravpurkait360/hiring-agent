from datetime import datetime
from typing import Dict, Any
import asyncio

async def stream_comprehensive_analysis(
    state: Dict[str, Any], 
    candidate_name: str, 
    job_title: str, 
    job_company: str, 
    job_domain: str,
    final_score: float, 
    recommendation: str, 
    detailed_scoring: str, 
    score_breakdown: Dict
) -> str:
    """Stream comprehensive analysis in real-time parts"""
    
    from app.agents.nodes import send_thinking_update
    
    # Initialize report content
    full_report = ""
    
    try:
        # Extract all available data
        resume = state['resume']
        job_description = state['job_description']
        github_analysis = state.get('github_analysis')
        linkedin_analysis = state.get('linkedin_analysis')
        twitter_analysis = state.get('twitter_analysis')
        medium_analysis = state.get('medium_analysis')
        project_analyses = state.get('project_analyses', [])
        company_analyses = state.get('company_analyses', [])
        
        # Stream Part 1: Executive Summary
        print("DEBUG: Streaming executive summary")
        executive_summary = f"""# 📋 COMPREHENSIVE CANDIDATE ANALYSIS REPORT

## Executive Summary

**Candidate:** {candidate_name}
**Position:** {job_title} at {job_company}
**Domain:** {job_domain}
**Overall Score:** {final_score:.1f}/100
**Recommendation:** {recommendation}

---

## 🎯 Candidate Profile Overview

### Personal Information
- **Name:** {candidate_name}
- **Email:** {getattr(resume, 'email', 'Not provided')}
- **Experience:** {getattr(resume, 'experience_years', 'Not specified')} years
- **Key Skills:** {', '.join(getattr(resume, 'skills', [])[:10])}

### Role Requirements Analysis
- **Target Role:** {job_title}
- **Company:** {job_company}
- **Domain Focus:** {job_domain}
- **Required Experience Level:** {getattr(job_description, 'experience_level', 'Not specified')}
- **Key Requirements:** {', '.join(getattr(job_description, 'requirements', [])[:8])}"""
        
        await send_thinking_update(state, executive_summary)
        full_report += executive_summary + "\n\n"
        await asyncio.sleep(0.5)  # Small delay for streaming effect
        
        # Stream Part 2: Score Analysis
        print("DEBUG: Streaming score analysis")
        score_analysis = f"""---

## 📊 Detailed Score Analysis

{detailed_scoring}"""
        
        await send_thinking_update(state, score_analysis)
        full_report += score_analysis + "\n\n"
        await asyncio.sleep(0.5)
        
        # Stream Part 3: Technical Assessment
        print("DEBUG: Streaming technical assessment")
        technical_section = "---\n\n## 💻 Technical Assessment\n"
        
        # GitHub Analysis
        if github_analysis:
            github_section = f"""
### GitHub Profile Analysis

**Username:** @{getattr(github_analysis, 'username', 'Unknown')}

**Profile Statistics:**
- 📁 Public Repositories: {getattr(github_analysis, 'public_repos_count', 0)}
- 👥 Followers: {getattr(github_analysis, 'followers', 0)}
- 📈 Total Contributions: {getattr(github_analysis, 'total_commits', 0)}
- 🔥 Contribution Streak: {getattr(github_analysis, 'contribution_streak', 0)} days

**Code Quality Metrics:**
- 🏆 Code Quality Score: {getattr(github_analysis, 'code_quality_score', 0):.1f}/100
- 🧩 Project Complexity: {getattr(github_analysis, 'project_complexity_score', 0):.1f}/100
- 🎯 Domain Relevance: {getattr(github_analysis, 'domain_relevance_score', 0):.1f}/100

**Programming Languages Used:**"""
            
            languages = getattr(github_analysis, 'languages', {})
            if languages:
                for lang, count in list(languages.items())[:8]:
                    github_section += f"\n- **{lang}**: {count} repositories"
            else:
                github_section += "\n- No language data available"
            
            github_section += "\n\n**Top Repositories:**"
            repositories = getattr(github_analysis, 'repositories', [])
            if repositories:
                for i, repo in enumerate(repositories[:5], 1):
                    if isinstance(repo, dict):
                        github_section += f"""
{i}. **{repo.get('name', 'Unknown')}**
   - Language: {repo.get('language', 'Not specified')}
   - Stars: ⭐ {repo.get('stars', 0)} | Forks: 🍴 {repo.get('forks', 0)}
   - Description: {repo.get('description', 'No description available')[:100]}{'...' if len(repo.get('description', '')) > 100 else ''}"""
            else:
                github_section += "\n- No accessible repositories found"
        else:
            github_section = "\n### GitHub Profile Analysis\n\n❌ **GitHub profile not found or inaccessible**\n"
        
        technical_section += github_section
        await send_thinking_update(state, technical_section)
        full_report += technical_section + "\n\n"
        await asyncio.sleep(0.7)
        
        # Stream Part 4: Professional Presence
        print("DEBUG: Streaming professional presence")
        professional_section = "---\n\n## 👔 Professional Presence Analysis\n"
        
        # LinkedIn Analysis
        if linkedin_analysis:
            linkedin_section = f"""
### LinkedIn Profile Assessment
- 📝 Technical Posts: {getattr(linkedin_analysis, 'technical_posts_count', 0)}
- 🎯 Domain-Relevant Posts: {getattr(linkedin_analysis, 'domain_relevant_posts', 0)}
- 🤝 Professional Connections: {getattr(linkedin_analysis, 'connections', 0)}
- 👍 Endorsements: {getattr(linkedin_analysis, 'endorsements', 0)}
- 🏆 Certifications: {getattr(linkedin_analysis, 'certifications', 0)}
- 📊 Domain Relevance Score: {getattr(linkedin_analysis, 'domain_relevance_score', 0):.1f}/100"""
        else:
            linkedin_section = "\n### LinkedIn Profile Assessment\n❌ **LinkedIn profile not found or not provided**"
        
        # Twitter/X Analysis
        if twitter_analysis:
            twitter_section = f"""
### Twitter/X Technical Presence
- 👤 Username: @{getattr(twitter_analysis, 'username', 'Unknown')}
- 👥 Followers: {getattr(twitter_analysis, 'followers', 0)}
- 💻 Technical Tweets: {getattr(twitter_analysis, 'technical_tweets_count', 0)}
- 🎯 Domain-Relevant Tweets: {getattr(twitter_analysis, 'domain_relevant_tweets', 0)}
- 📈 Engagement Rate: {getattr(twitter_analysis, 'engagement_rate', 0):.1f}%
- 📊 Technical Relevance: {getattr(twitter_analysis, 'domain_relevance_score', 0):.1f}/100"""
        else:
            twitter_section = "\n### Twitter/X Technical Presence\n❌ **Twitter/X profile not found or not provided**"
        
        # Medium Analysis
        if medium_analysis:
            medium_section = f"""
### Technical Writing & Thought Leadership
- ✍️ Medium Username: @{getattr(medium_analysis, 'username', 'Unknown')}
- 📚 Published Articles: {getattr(medium_analysis, 'articles_count', 0)}
- 🎯 Domain-Relevant Articles: {getattr(medium_analysis, 'domain_relevant_articles', 0)}
- 👏 Total Claps/Engagement: {getattr(medium_analysis, 'total_claps', 0)}
- 👥 Followers: {getattr(medium_analysis, 'followers', 0)}
- 📊 Writing Quality Score: {getattr(medium_analysis, 'domain_relevance_score', 0):.1f}/100"""
        else:
            medium_section = "\n### Technical Writing & Thought Leadership\n❌ **Medium profile not found or no technical writing present**"
        
        professional_section += linkedin_section + twitter_section + medium_section
        await send_thinking_update(state, professional_section)
        full_report += professional_section + "\n\n"
        await asyncio.sleep(0.7)
        
        # Stream Part 5: Project Portfolio
        print("DEBUG: Streaming project portfolio")
        project_section = "---\n\n## 🚀 Project Portfolio Analysis\n"
        
        if project_analyses:
            project_section += f"\n**{len(project_analyses)} projects evaluated:**\n"
            for i, project in enumerate(project_analyses[:5], 1):
                if hasattr(project, 'project_name'):
                    project_section += f"""
{i}. **{getattr(project, 'project_name', 'Unnamed Project')}**
   - Status: {'🟢 Live' if getattr(project, 'is_live', False) else '🔴 Not Live'}
   - URL: {getattr(project, 'url', 'Not provided')}
   - Technologies: {', '.join(getattr(project, 'technologies', []))}
   - Complexity Score: {getattr(project, 'complexity_score', 0):.1f}/100
   - Performance Score: {getattr(project, 'performance_score', 0):.1f}/100
   - SEO Score: {getattr(project, 'seo_score', 0):.1f}/100"""
        else:
            project_section += "❌ **No projects found or analyzed**"
        
        await send_thinking_update(state, project_section)
        full_report += project_section + "\n\n"
        await asyncio.sleep(0.7)
        
        # Stream Part 6: Work Experience
        print("DEBUG: Streaming work experience")
        work_section = "---\n\n## 🏢 Work Experience Analysis\n"
        
        if company_analyses:
            work_section += f"\n**{len(company_analyses)} companies researched:**\n"
            for i, company in enumerate(company_analyses[:5], 1):
                if hasattr(company, 'company_name'):
                    work_section += f"""
{i}. **{getattr(company, 'company_name', 'Unknown Company')}**
   - Role: {getattr(company, 'role', 'Not specified')}
   - Company Tier: {getattr(company, 'company_tier', 'Unknown')}
   - Difficulty Score: {getattr(company, 'difficulty_score', 0):.1f}/100
   - Market Reputation: {getattr(company, 'market_reputation', 0):.1f}/100"""
        else:
            work_section += "❌ **No work experience data analyzed**"
        
        # Add resume experience
        resume_experience = getattr(resume, 'experience', [])
        if resume_experience:
            work_section += "\n\n### Resume Experience Summary"
            for i, exp in enumerate(resume_experience[:5], 1):
                if isinstance(exp, dict):
                    work_section += f"""
{i}. **{exp.get('role', 'Unknown Role')}** at {exp.get('company', 'Unknown Company')}
   - Duration: {exp.get('duration', 'Not specified')}
   - Key Responsibilities: {exp.get('description', 'No description available')[:150]}{'...' if len(exp.get('description', '')) > 150 else ''}"""
        
        await send_thinking_update(state, work_section)
        full_report += work_section + "\n\n"
        await asyncio.sleep(0.7)
        
        # Stream Part 7: Education
        print("DEBUG: Streaming education background")
        education_section = ""
        resume_education = getattr(resume, 'education', [])
        if resume_education:
            education_section = "### 🎓 Educational Background\n"
            for i, edu in enumerate(resume_education[:3], 1):
                if isinstance(edu, dict):
                    education_section += f"""
{i}. **{edu.get('degree', 'Unknown Degree')}** in {edu.get('field', 'Unknown Field')}
   - Institution: {edu.get('institution', 'Unknown Institution')}
   - Year: {edu.get('year', 'Not specified')}"""
            
            await send_thinking_update(state, education_section)
            full_report += education_section + "\n\n"
            await asyncio.sleep(0.5)
        
        # Stream Part 8: Strengths & Weaknesses Analysis
        print("DEBUG: Streaming strengths and weaknesses")
        analysis_section = "---\n\n## 💪 Strengths and Weaknesses Analysis\n"
        
        strengths = []
        weaknesses = []
        improvements = []
        
        # Analyze based on scores
        resume_score = score_breakdown.get('resume_jd_match', {}).get('score', 0)
        if resume_score >= 75:
            strengths.append("**Strong Resume-Job Match**: Excellent alignment between candidate's background and role requirements")
        elif resume_score >= 50:
            strengths.append("**Moderate Resume-Job Match**: Good foundational fit with some relevant experience")
        else:
            weaknesses.append("**Poor Resume-Job Match**: Limited alignment with role requirements")
            improvements.append("Focus on developing skills more closely aligned with the target role")
        
        if github_analysis:
            github_score = (
                getattr(github_analysis, 'code_quality_score', 0) * 0.4 +
                getattr(github_analysis, 'project_complexity_score', 0) * 0.3 +
                getattr(github_analysis, 'domain_relevance_score', 0) * 0.3
            )
            
            if github_score >= 70:
                strengths.append(f"**Strong GitHub Presence**: High-quality code portfolio with {getattr(github_analysis, 'public_repos_count', 0)} public repositories")
            elif github_score >= 40:
                strengths.append("**Moderate GitHub Activity**: Shows coding activity with room for improvement")
            else:
                weaknesses.append("**Limited GitHub Presence**: Minimal or low-quality coding activity visible")
                improvements.append("Increase GitHub activity with higher-quality, domain-relevant projects")
            
            languages = getattr(github_analysis, 'languages', {})
            if len(languages) >= 3:
                strengths.append(f"**Technical Versatility**: Proficient in {len(languages)} programming languages")
            elif len(languages) == 0:
                weaknesses.append("**Limited Programming Language Exposure**: No visible language diversity")
                improvements.append("Diversify technical skills across multiple programming languages")
        else:
            weaknesses.append("**No GitHub Presence**: No visible code portfolio or technical contributions")
            improvements.append("Create and maintain an active GitHub profile with relevant projects")
        
        if linkedin_analysis:
            linkedin_score = getattr(linkedin_analysis, 'domain_relevance_score', 0)
            if linkedin_score >= 60:
                strengths.append("**Strong Professional Network**: Active LinkedIn presence with relevant content")
            else:
                weaknesses.append("**Limited Professional Presence**: Minimal LinkedIn engagement in target domain")
                improvements.append("Increase professional networking and thought leadership on LinkedIn")
        
        if medium_analysis and getattr(medium_analysis, 'articles_count', 0) > 0:
            strengths.append("**Technical Writing Skills**: Demonstrates thought leadership through published articles")
        
        if project_analyses:
            live_projects = sum(1 for p in project_analyses if getattr(p, 'is_live', False))
            if live_projects > 0:
                strengths.append(f"**Practical Implementation**: {live_projects} live project(s) demonstrating real-world application")
            else:
                weaknesses.append("**No Live Projects**: All projects appear to be non-production or inaccessible")
                improvements.append("Deploy projects to production environments to demonstrate full-stack capabilities")
        
        # Build strengths section
        analysis_section += "\n### 🎯 Key Strengths\n"
        if strengths:
            for i, strength in enumerate(strengths, 1):
                analysis_section += f"{i}. {strength}\n"
        else:
            analysis_section += "- Limited identifiable strengths based on available data\n"
        
        # Build weaknesses section
        analysis_section += "\n### ⚠️ Areas of Concern\n"
        if weaknesses:
            for i, weakness in enumerate(weaknesses, 1):
                analysis_section += f"{i}. {weakness}\n"
        else:
            analysis_section += "- No major weaknesses identified\n"
        
        # Build improvements section
        analysis_section += "\n### 🚀 Improvement Recommendations\n"
        if improvements:
            for i, improvement in enumerate(improvements, 1):
                analysis_section += f"{i}. {improvement}\n"
        else:
            analysis_section += "- Continue maintaining current performance standards\n"
        
        await send_thinking_update(state, analysis_section)
        full_report += analysis_section + "\n\n"
        await asyncio.sleep(0.8)
        
        # Stream Part 9: Final Recommendation
        print("DEBUG: Streaming final recommendation")
        recommendation_section = f"---\n\n## 🎯 Final Hiring Recommendation\n"
        
        if final_score >= 85:
            recommendation_section += f"""### ✅ STRONG HIRE - Score: {final_score:.1f}/100

🏆 **This candidate demonstrates exceptional qualifications** for the {job_title} position. They show strong technical competency, relevant experience, and professional presence that aligns well with {job_company}'s requirements in the {job_domain} domain.

**Confidence Level: HIGH** - Recommend proceeding with technical interviews and extending an offer.

**Next Steps:**
- Schedule technical interview to validate specific skills
- Conduct cultural fit assessment
- Prepare competitive offer package
- Fast-track through interview process"""
        
        elif final_score >= 70:
            recommendation_section += f"""### ✅ HIRE - Score: {final_score:.1f}/100

👍 **This candidate shows solid qualifications** for the {job_title} position with good technical foundation and relevant experience. While there may be some areas for growth, they demonstrate the core competencies needed for success at {job_company}.

**Confidence Level: MODERATE-HIGH** - Recommend proceeding with interviews to assess cultural fit and specific technical skills.

**Next Steps:**
- Conduct thorough technical assessment
- Evaluate cultural alignment with team
- Discuss areas for potential growth and development
- Consider mentorship opportunities"""
        
        elif final_score >= 55:
            recommendation_section += f"""### 🤔 MAYBE - Score: {final_score:.1f}/100

⚖️ **This candidate shows mixed results** with some strengths but also notable gaps. They may be suitable for the {job_title} position with additional training or in a more junior capacity. Consider if the team has capacity for mentoring and skill development.

**Confidence Level: MODERATE** - Recommend careful evaluation through detailed technical interviews.

**Next Steps:**
- Conduct comprehensive skills assessment
- Evaluate learning potential and growth mindset
- Consider if team can provide necessary mentorship
- Explore alternative role levels or responsibilities"""
        
        else:
            recommendation_section += f"""### ❌ NO HIRE - Score: {final_score:.1f}/100

🚫 **This candidate does not currently meet the requirements** for the {job_title} position at {job_company}. Significant gaps in technical skills, experience, or domain knowledge make them unsuitable for this role at this time.

**Confidence Level: HIGH** - Recommend not proceeding unless candidate addresses major skill gaps.

**Alternative Considerations:**
- Consider for more junior positions if available
- Provide feedback for future opportunities
- Suggest specific areas for skill development
- Keep in talent pipeline for future roles"""
        
        await send_thinking_update(state, recommendation_section)
        full_report += recommendation_section + "\n\n"
        await asyncio.sleep(0.8)
        
        # Stream Part 10: Metadata
        print("DEBUG: Streaming analysis metadata")
        metadata_section = f"""---

## 📊 Analysis Metadata

- **Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Analysis Version:** v2.0 (Comprehensive Streaming)
- **Data Sources:** Resume, GitHub, LinkedIn, Twitter/X, Medium, Project Portfolio, Company Research
- **Scoring Algorithm:** Weighted multi-factor analysis
- **Confidence Score:** {min(100, max(0, (sum(1 for x in [github_analysis, linkedin_analysis, twitter_analysis, medium_analysis] if x) / 4) * 100)):.0f}% (based on data availability)

*This analysis is generated by AI and should be used as a supplementary tool in the hiring process. Human judgment and additional interviews are recommended for final hiring decisions.*

---

**End of Comprehensive Analysis Report** 📋✨"""
        
        await send_thinking_update(state, metadata_section)
        full_report += metadata_section
        
        print("DEBUG: Streaming analysis completed successfully")
        return full_report
        
    except Exception as e:
        print(f"DEBUG: Error in streaming analysis: {e}")
        import traceback
        print(f"DEBUG: Streaming analysis error traceback: {traceback.format_exc()}")
        
        error_report = f"""# Analysis Report - Error

An error occurred while generating the streaming analysis: {str(e)}

## Basic Results
- Score: {final_score:.1f}/100
- Recommendation: {recommendation}
- Scoring Details: {detailed_scoring}
"""
        await send_thinking_update(state, error_report)
        return error_report