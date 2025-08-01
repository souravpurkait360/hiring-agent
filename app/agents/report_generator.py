from datetime import datetime
from typing import Dict, Any

async def generate_comprehensive_report(
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
    """Generate a comprehensive analysis report with detailed insights"""
    
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
        
        # Build comprehensive report
        report = f"""# Comprehensive Candidate Analysis Report

## 📋 Executive Summary

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
- **Key Requirements:** {', '.join(getattr(job_description, 'requirements', [])[:8])}

---

## 📊 Detailed Score Analysis

{detailed_scoring}

---

## 💻 Technical Assessment
"""
        
        # GitHub Analysis Section
        if github_analysis:
            report += f"""
### GitHub Profile Analysis

**Username:** @{getattr(github_analysis, 'username', 'Unknown')}
**Profile Statistics:**
- Public Repositories: {getattr(github_analysis, 'public_repos_count', 0)}
- Followers: {getattr(github_analysis, 'followers', 0)}
- Total Contributions: {getattr(github_analysis, 'total_commits', 0)}
- Contribution Streak: {getattr(github_analysis, 'contribution_streak', 0)} days

**Code Quality Metrics:**
- Code Quality Score: {getattr(github_analysis, 'code_quality_score', 0):.1f}/100
- Project Complexity: {getattr(github_analysis, 'project_complexity_score', 0):.1f}/100
- Domain Relevance: {getattr(github_analysis, 'domain_relevance_score', 0):.1f}/100

**Programming Languages:**
"""
            languages = getattr(github_analysis, 'languages', {})
            if languages:
                for lang, count in list(languages.items())[:8]:
                    report += f"- {lang}: {count} repositories\n"
            else:
                report += "- No language data available\n"
            
            report += "\n**Top Repositories:**\n"
            repositories = getattr(github_analysis, 'repositories', [])
            if repositories:
                for i, repo in enumerate(repositories[:5], 1):
                    if isinstance(repo, dict):
                        report += f"""{i}. **{repo.get('name', 'Unknown')}**
   - Language: {repo.get('language', 'Not specified')}
   - Stars: ⭐ {repo.get('stars', 0)} | Forks: 🍴 {repo.get('forks', 0)}
   - Description: {repo.get('description', 'No description available')[:100]}{'...' if len(repo.get('description', '')) > 100 else ''}

"""
            else:
                report += "- No accessible repositories found\n"
        else:
            report += "\n### GitHub Profile Analysis\n\n❌ **GitHub profile not found or inaccessible**\n\n"
        
        # Professional Presence Analysis
        report += "\n---\n\n## 👔 Professional Presence Analysis\n"
        
        # LinkedIn Analysis
        if linkedin_analysis:
            report += f"""
### LinkedIn Profile Assessment
- Technical Posts: {getattr(linkedin_analysis, 'technical_posts_count', 0)}
- Domain-Relevant Posts: {getattr(linkedin_analysis, 'domain_relevant_posts', 0)}
- Professional Connections: {getattr(linkedin_analysis, 'connections', 0)}
- Endorsements: {getattr(linkedin_analysis, 'endorsements', 0)}
- Certifications: {getattr(linkedin_analysis, 'certifications', 0)}
- Domain Relevance Score: {getattr(linkedin_analysis, 'domain_relevance_score', 0):.1f}/100
"""
        else:
            report += "\n### LinkedIn Profile Assessment\n❌ **LinkedIn profile not found or not provided**\n"
        
        # Twitter/X Analysis
        if twitter_analysis:
            report += f"""
### Twitter/X Technical Presence
- Username: @{getattr(twitter_analysis, 'username', 'Unknown')}
- Followers: {getattr(twitter_analysis, 'followers', 0)}
- Technical Tweets: {getattr(twitter_analysis, 'technical_tweets_count', 0)}
- Domain-Relevant Tweets: {getattr(twitter_analysis, 'domain_relevant_tweets', 0)}
- Engagement Rate: {getattr(twitter_analysis, 'engagement_rate', 0):.1f}%
- Technical Relevance: {getattr(twitter_analysis, 'domain_relevance_score', 0):.1f}/100
"""
        else:
            report += "\n### Twitter/X Technical Presence\n❌ **Twitter/X profile not found or not provided**\n"
        
        # Technical Writing Analysis
        if medium_analysis:
            report += f"""
### Technical Writing & Thought Leadership
- Medium Username: @{getattr(medium_analysis, 'username', 'Unknown')}
- Published Articles: {getattr(medium_analysis, 'articles_count', 0)}
- Domain-Relevant Articles: {getattr(medium_analysis, 'domain_relevant_articles', 0)}
- Total Claps/Engagement: {getattr(medium_analysis, 'total_claps', 0)}
- Followers: {getattr(medium_analysis, 'followers', 0)}
- Writing Quality Score: {getattr(medium_analysis, 'domain_relevance_score', 0):.1f}/100
"""
        else:
            report += "\n### Technical Writing & Thought Leadership\n❌ **Medium profile not found or no technical writing present**\n"
        
        # Project Portfolio Analysis
        report += "\n---\n\n## 🚀 Project Portfolio Analysis\n"
        
        if project_analyses:
            report += f"\n**{len(project_analyses)} projects evaluated:**\n\n"
            for i, project in enumerate(project_analyses[:5], 1):
                if hasattr(project, 'project_name'):
                    report += f"""{i}. **{getattr(project, 'project_name', 'Unnamed Project')}**
   - Status: {'🟢 Live' if getattr(project, 'is_live', False) else '🔴 Not Live'}
   - URL: {getattr(project, 'url', 'Not provided')}
   - Technologies: {', '.join(getattr(project, 'technologies', []))}
   - Complexity Score: {getattr(project, 'complexity_score', 0):.1f}/100
   - Performance Score: {getattr(project, 'performance_score', 0):.1f}/100
   - SEO Score: {getattr(project, 'seo_score', 0):.1f}/100

"""
        else:
            report += "❌ **No projects found or analyzed**\n"
        
        # Work Experience Analysis
        report += "\n---\n\n## 🏢 Work Experience Analysis\n"
        
        if company_analyses:
            report += f"\n**{len(company_analyses)} companies researched:**\n\n"
            for i, company in enumerate(company_analyses[:5], 1):
                if hasattr(company, 'company_name'):
                    report += f"""{i}. **{getattr(company, 'company_name', 'Unknown Company')}**
   - Role: {getattr(company, 'role', 'Not specified')}
   - Company Tier: {getattr(company, 'company_tier', 'Unknown')}
   - Difficulty Score: {getattr(company, 'difficulty_score', 0):.1f}/100
   - Market Reputation: {getattr(company, 'market_reputation', 0):.1f}/100

"""
        else:
            report += "❌ **No work experience data analyzed**\n"
        
        # Resume Experience Details
        resume_experience = getattr(resume, 'experience', [])
        if resume_experience:
            report += "\n### Resume Experience Summary\n"
            for i, exp in enumerate(resume_experience[:5], 1):
                if isinstance(exp, dict):
                    report += f"""{i}. **{exp.get('role', 'Unknown Role')}** at {exp.get('company', 'Unknown Company')}
   - Duration: {exp.get('duration', 'Not specified')}
   - Description: {exp.get('description', 'No description available')[:150]}{'...' if len(exp.get('description', '')) > 150 else ''}

"""
        
        # Educational Background
        resume_education = getattr(resume, 'education', [])
        if resume_education:
            report += "\n### Educational Background\n"
            for i, edu in enumerate(resume_education[:3], 1):
                if isinstance(edu, dict):
                    report += f"""{i}. **{edu.get('degree', 'Unknown Degree')}** in {edu.get('field', 'Unknown Field')}
   - Institution: {edu.get('institution', 'Unknown Institution')}
   - Year: {edu.get('year', 'Not specified')}

"""
        
        # Strengths and Weaknesses Analysis
        report += "\n---\n\n## 💪 Strengths and Weaknesses Analysis\n"
        
        strengths = []
        weaknesses = []
        improvements = []
        
        # Analyze strengths based on scores
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
                strengths.append(f"**Strong GitHub Presence**: High-quality code with {getattr(github_analysis, 'public_repos_count', 0)} public repositories")
            elif github_score >= 40:
                strengths.append("**Moderate GitHub Activity**: Shows coding activity with room for improvement")
            else:
                weaknesses.append("**Limited GitHub Presence**: Minimal or low-quality coding activity visible")
                improvements.append("Increase GitHub activity with higher-quality, domain-relevant projects")
            
            # Language diversity analysis
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
        
        if medium_analysis:
            if getattr(medium_analysis, 'articles_count', 0) > 0:
                strengths.append("**Technical Writing Skills**: Demonstrates thought leadership through published articles")
            else:
                improvements.append("Consider writing technical articles to showcase domain expertise")
        
        if project_analyses:
            live_projects = sum(1 for p in project_analyses if getattr(p, 'is_live', False))
            if live_projects > 0:
                strengths.append(f"**Practical Implementation**: {live_projects} live project(s) demonstrating real-world application")
            else:
                weaknesses.append("**No Live Projects**: All projects appear to be non-production or inaccessible")
                improvements.append("Deploy projects to production environments to demonstrate full-stack capabilities")
        
        # Add strengths section
        report += "\n### 🎯 Key Strengths\n"
        if strengths:
            for i, strength in enumerate(strengths, 1):
                report += f"{i}. {strength}\n"
        else:
            report += "- Limited identifiable strengths based on available data\n"
        
        # Add weaknesses section
        report += "\n### ⚠️ Areas of Concern\n"
        if weaknesses:
            for i, weakness in enumerate(weaknesses, 1):
                report += f"{i}. {weakness}\n"
        else:
            report += "- No major weaknesses identified\n"
        
        # Add improvement recommendations
        report += "\n### 🚀 Improvement Recommendations\n"
        if improvements:
            for i, improvement in enumerate(improvements, 1):
                report += f"{i}. {improvement}\n"
        else:
            report += "- Continue maintaining current performance standards\n"
        
        # Final recommendation section
        report += f"\n---\n\n## 🎯 Final Hiring Recommendation\n"
        
        if final_score >= 85:
            report += f"""### ✅ STRONG HIRE - Score: {final_score:.1f}/100

This candidate demonstrates exceptional qualifications for the {job_title} position. They show strong technical competency, relevant experience, and professional presence that aligns well with {job_company}'s requirements in the {job_domain} domain.

**Confidence Level: HIGH** - Recommend proceeding with technical interviews and extending an offer."""
        
        elif final_score >= 70:
            report += f"""### ✅ HIRE - Score: {final_score:.1f}/100

This candidate shows solid qualifications for the {job_title} position with good technical foundation and relevant experience. While there may be some areas for growth, they demonstrate the core competencies needed for success at {job_company}.

**Confidence Level: MODERATE-HIGH** - Recommend proceeding with interviews to assess cultural fit and specific technical skills."""
        
        elif final_score >= 55:
            report += f"""### 🤔 MAYBE - Score: {final_score:.1f}/100

This candidate shows mixed results with some strengths but also notable gaps. They may be suitable for the {job_title} position with additional training or in a more junior capacity. Consider if the team has capacity for mentoring and skill development.

**Confidence Level: MODERATE** - Recommend careful evaluation through detailed technical interviews."""
        
        else:
            report += f"""### ❌ NO HIRE - Score: {final_score:.1f}/100

This candidate does not currently meet the requirements for the {job_title} position at {job_company}. Significant gaps in technical skills, experience, or domain knowledge make them unsuitable for this role at this time.

**Confidence Level: HIGH** - Recommend not proceeding unless candidate addresses major skill gaps."""
        
        report += f"\n\n---\n\n## 📊 Analysis Metadata\n\n- **Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n- **Analysis Version:** v2.0 (Comprehensive)\n- **Data Sources:** Resume, GitHub, LinkedIn, Twitter/X, Medium, Project Portfolio, Company Research\n- **Scoring Algorithm:** Weighted multi-factor analysis\n- **Confidence Score:** {min(100, max(0, (sum(1 for x in [github_analysis, linkedin_analysis, twitter_analysis, medium_analysis] if x) / 4) * 100)):.0f}% (based on data availability)\n\n*This analysis is generated by AI and should be used as a supplementary tool in the hiring process. Human judgment and additional interviews are recommended for final hiring decisions.*\n"
        
        return report
        
    except Exception as e:
        print(f"DEBUG: Error in comprehensive report generation: {e}")
        import traceback
        print(f"DEBUG: Report generation traceback: {traceback.format_exc()}")
        return f"""# Analysis Report - Error

An error occurred while generating the comprehensive report: {str(e)}

## Basic Results
- Score: {final_score:.1f}/100
- Recommendation: {recommendation}
- Scoring Details: {detailed_scoring}
"""