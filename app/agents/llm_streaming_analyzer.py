from datetime import datetime
from typing import Dict, Any
import asyncio
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

async def generate_llm_streaming_analysis(
    state: Dict[str, Any], 
    candidate_name: str, 
    job_title: str, 
    job_company: str, 
    job_domain: str,
    final_score: float, 
    recommendation: str
) -> str:
    """Generate comprehensive LLM-based streaming analysis"""
    
    from app.api.websocket_manager import manager
    analysis_id = state.get("analysis_id")
    
    if not analysis_id:
        return "Analysis ID not found"
    
    try:
        
        # Initialize LLM
        from config.settings import settings
        llm = ChatOpenAI(model=settings.get_model(), temperature=0.3)
        
        # Extract all available data for context
        resume = state['resume']
        job_description = state['job_description']
        github_analysis = state.get('github_analysis')
        linkedin_analysis = state.get('linkedin_analysis')
        twitter_analysis = state.get('twitter_analysis')
        medium_analysis = state.get('medium_analysis')
        project_analyses = state.get('project_analyses', [])
        company_analyses = state.get('company_analyses', [])
        
        # Build comprehensive data context for LLM
        job_requirements = getattr(job_description, 'requirements', [])
        job_preferred_skills = getattr(job_description, 'preferred_skills', [])
        
        context_data = f"""CANDIDATE ANALYSIS DATA:

BASIC INFO:
- Name: {candidate_name}
- Email: {getattr(resume, 'email', 'Not provided')}
- Experience: {getattr(resume, 'experience_years', 'Not specified')} years
- Skills: {', '.join(getattr(resume, 'skills', []))}

JOB REQUIREMENTS (ONLY EVALUATE AGAINST THESE):
- Position: {job_title}
- Company: {job_company}
- Domain: {job_domain}
- Experience Level: {getattr(job_description, 'experience_level', 'Not specified')}
- REQUIRED SKILLS/TECHNOLOGIES: {', '.join(job_requirements) if job_requirements else 'None specified'}
- PREFERRED SKILLS/TECHNOLOGIES: {', '.join(job_preferred_skills) if job_preferred_skills else 'None specified'}

⚠️ CRITICAL: Only evaluate the candidate against the REQUIRED and PREFERRED skills listed above. Do NOT mention or evaluate against any technologies, frameworks, or skills that are not explicitly listed in the job requirements above.

TECHNICAL ANALYSIS:"""

        if github_analysis:
            context_data += f"""
GITHUB PROFILE:
- Username: {getattr(github_analysis, 'username', 'Unknown')}
- Public Repositories: {getattr(github_analysis, 'public_repos_count', 0)}
- Followers: {getattr(github_analysis, 'followers', 0)}
- Code Quality Score: {getattr(github_analysis, 'code_quality_score', 0)}/100
- Project Complexity: {getattr(github_analysis, 'project_complexity_score', 0)}/100
- Domain Relevance: {getattr(github_analysis, 'domain_relevance_score', 0)}/100
- Languages: {', '.join(list(getattr(github_analysis, 'languages', {}).keys())[:5])}"""
        
        if linkedin_analysis:
            context_data += f"""
LINKEDIN PROFILE:
- Technical Posts: {getattr(linkedin_analysis, 'technical_posts_count', 0)}
- Domain-Relevant Posts: {getattr(linkedin_analysis, 'domain_relevant_posts', 0)}
- Connections: {getattr(linkedin_analysis, 'connections', 0)}
- Domain Relevance: {getattr(linkedin_analysis, 'domain_relevance_score', 0)}/100"""
        
        if project_analyses:
            context_data += f"\nPROJECTS: {len(project_analyses)} projects analyzed"
            for project in project_analyses[:3]:
                if hasattr(project, 'project_name'):
                    context_data += f"\n- {getattr(project, 'project_name', 'Unknown')}: {'Live' if getattr(project, 'is_live', False) else 'Not Live'}"
        
        context_data += f"""

SCORING RESULTS:
- Overall Score: {final_score}/100
- Recommendation: {recommendation}

RESUME EXPERIENCE:"""
        
        resume_experience = getattr(resume, 'experience', [])
        for exp in resume_experience[:3]:
            if isinstance(exp, dict):
                context_data += f"\n- {exp.get('role', 'Unknown Role')} at {exp.get('company', 'Unknown Company')}"
        
        # Stream Part 1: Executive Summary
        await manager.send_final_analysis_stream(analysis_id, """# 📋 COMPREHENSIVE CANDIDATE ANALYSIS REPORT

🔄 **Generating executive summary...**""")
        
        executive_prompt = f"""Based on the following candidate data, write a comprehensive executive summary for a hiring decision report. Format your response in clear, well-structured markdown.

🚨 CRITICAL RULE: You MUST ONLY evaluate the candidate against the exact skills, technologies, and requirements explicitly listed in the job description. DO NOT evaluate against any other skills, frameworks, or technologies not mentioned in the job requirements.

{context_data}

**FORBIDDEN ACTIONS - DO NOT DO THESE:**
❌ Do NOT mention skills like Java, Go, AWS, GCP, Redis, Docker, Kubernetes unless they are explicitly listed in the job requirements above
❌ Do NOT evaluate against "commonly expected" skills for the role type
❌ Do NOT assume additional technical requirements beyond what is stated in the job description
❌ Do NOT penalize the candidate for not having skills that aren't required for the job
❌ Do NOT mention ANY technology, framework, or skill that is not explicitly listed in the REQUIRED or PREFERRED skills above

**CRITICAL FORMATTING REQUIREMENTS:**
- Use proper markdown headers with proper spacing (## Header Name)
- Include bullet points and numbered lists where appropriate
- Use **bold** for key metrics and important points
- Use *italic* for emphasis
- Include relevant scores and metrics
- Make it scannable and professional
- Ensure proper line breaks between sections
- Start each section with a clear markdown header

**Content Structure:**
1. **Candidate Overview** - Brief introduction with key stats
2. **Position Fit Assessment** - How well they match the role based ONLY on job requirements listed
3. **Key Strengths** - Top 3-4 strengths with evidence relevant to job requirements
4. **Qualification Summary** - Technical and professional qualifications relevant to job requirements
5. **Initial Recommendation** - Preliminary hiring decision based on job requirements

Keep each section concise but detailed with specific evidence from the analysis. Only discuss skills and technologies mentioned in the job requirements."""

        executive_response = await llm.ainvoke([
            SystemMessage(content="You are an expert hiring analyst. Write professional, concise analysis suitable for hiring decisions. 🚨 CRITICAL: Only evaluate the candidate against the exact skills and requirements explicitly listed in the job description. DO NOT mention skills like Java, Go, AWS, GCP, Redis unless they are explicitly listed in the job requirements. DO NOT evaluate against commonly expected skills or assume additional requirements. Format all responses in clean, well-structured markdown with proper headers, bullet points, and line breaks."),
            HumanMessage(content=executive_prompt)
        ])
        
        executive_summary = f"""## 📋 Executive Summary

{executive_response.content.strip()}

**Overall Score:** {final_score:.1f}/100  
**Recommendation:** {recommendation}

---
"""
        
        await manager.send_final_analysis_stream(analysis_id, executive_summary)
        await asyncio.sleep(0.8)
        
        # Stream Part 2: Technical Assessment
        await manager.send_final_analysis_stream(analysis_id, "🔄 **Analyzing technical capabilities...**")
        
        technical_prompt = f"""Based on the candidate's technical data, provide a detailed technical assessment. Format your response in clear, well-structured markdown.

🚨 CRITICAL RULE: You MUST ONLY evaluate the candidate against the exact skills, technologies, and requirements explicitly listed in the job description. DO NOT evaluate against any other skills, frameworks, or technologies not mentioned in the job requirements.

{context_data}

**FORBIDDEN ACTIONS - DO NOT DO THESE:**
❌ Do NOT mention skills like Java, Go, AWS, GCP, Redis, Docker, Kubernetes unless they are explicitly listed in the job requirements above
❌ Do NOT evaluate against "commonly expected" skills for the role type
❌ Do NOT assume additional technical requirements beyond what is stated in the job description
❌ Do NOT use phrases like "typically required for this role" or "standard for this position"
❌ Do NOT mention ANY technology, framework, or skill that is not explicitly listed in the REQUIRED or PREFERRED skills above

**CRITICAL FORMATTING REQUIREMENTS:**
- Use proper markdown headers (##, ###)
- Include bullet points and numbered lists
- Use **bold** for scores, metrics, and key technologies
- Use code blocks for languages/tech stacks
- Make technical data easily scannable

**Content Structure:**
### 🔧 Technical Skills Analysis
- **Primary Languages**: Only mention languages from candidate's profile that are also in job requirements
- **Frameworks & Tools**: Only mention tools/frameworks from candidate's profile that are also in job requirements
- **Architecture Experience**: Only discuss relevant to job requirements

### 💻 Code Quality Assessment
- **GitHub Statistics**: Repos, commits, followers
- **Code Quality Score**: {getattr(github_analysis, 'code_quality_score', 'N/A') if github_analysis else 'N/A'}/100
- **Project Complexity**: Evidence of development in technologies mentioned in job requirements

### 🏗️ Project Portfolio Review
- **Live Projects**: Only evaluate projects using technologies mentioned in job requirements
- **Technical Complexity**: Only assess complexity in context of job requirements
- **Innovation Factor**: Only mention modern practices relevant to job requirements

### 📊 Skills vs Requirements Matrix
**MANDATORY APPROACH**: Create a table/list that ONLY includes the exact skills/technologies listed in the job requirements section above.

For EACH requirement listed in the job description:
- **Required Skill X**: [Yes/No] - [Evidence from candidate's profile if available]

For EACH preferred skill listed in the job description:
- **Preferred Skill Y**: [Yes/No] - [Evidence from candidate's profile if available]

**EXAMPLE FORMAT:**
- **JavaScript** (Required): Yes - Demonstrated in 3 GitHub projects
- **React** (Required): Yes - Used in portfolio projects  
- **Node.js** (Preferred): No - No evidence found

DO NOT ADD ANY SKILLS NOT EXPLICITLY LISTED IN THE JOB REQUIREMENTS ABOVE."""

        technical_response = await llm.ainvoke([
            SystemMessage(content="You are a technical hiring specialist. 🚨 CRITICAL: Analyze technical capabilities objectively against ONLY the specific skills and technologies mentioned in the job requirements. DO NOT mention skills like Java, Go, AWS, GCP, Redis unless they are explicitly listed in the job requirements. DO NOT evaluate against commonly expected skills or assume additional requirements. Format all responses in clean, well-structured markdown with proper headers, bullet points, and line breaks."),
            HumanMessage(content=technical_prompt)
        ])
        
        technical_section = f"""## 💻 Technical Assessment

{technical_response.content.strip()}

---
"""
        
        await manager.send_final_analysis_stream(analysis_id, technical_section)
        await asyncio.sleep(0.8)
        
        # Stream Part 3: Professional Background
        await manager.send_final_analysis_stream(analysis_id, "🔄 **Evaluating professional background...**")
        
        professional_prompt = f"""Analyze the candidate's professional background and experience. Format your response in clear, well-structured markdown.

{context_data}

**CRITICAL FORMATTING REQUIREMENTS:**
- Use proper markdown headers (##, ###)
- Include bullet points and numbered lists
- Use **bold** for company names, titles, and key metrics
- Use tables for career progression timeline
- Include LinkedIn stats and professional metrics
- Make career data easily scannable

**Content Structure:**
### 💼 Career Progression Analysis
- **Current Role & Company**: Position and organization quality
- **Career Trajectory**: Growth pattern and advancement
- **Industry Experience**: Domain expertise and transitions

### 🏢 Company & Role Quality Assessment
- **Organization Tiers**: Startup, mid-size, enterprise experience
- **Role Complexity**: Responsibilities and impact scope
- **Market Reputation**: Employer brand and industry standing

### 🤝 Professional Networking & Presence
- **LinkedIn Activity**: Technical posts and engagement
- **Industry Connections**: Network quality and size
- **Thought Leadership**: Professional content and visibility

### 📈 Experience Alignment Score
Rate how well their background matches the target role requirements.

Be specific with company names, role details, and measurable professional achievements."""

        professional_response = await llm.ainvoke([
            SystemMessage(content="You are a professional background analyst. Evaluate career progression and experience quality. Format all responses in clean, well-structured markdown with proper headers, bullet points, and line breaks."),
            HumanMessage(content=professional_prompt)
        ])
        
        professional_section = f"""## 🏢 Professional Background

{professional_response.content.strip()}

---
"""
        
        await manager.send_final_analysis_stream(analysis_id, professional_section)
        await asyncio.sleep(0.8)
        
        # Stream Part 4: Strengths and Weaknesses
        await manager.send_final_analysis_stream(analysis_id, "🔄 **Identifying strengths and improvement areas...**")
        
        swot_prompt = f"""Provide a detailed SWOT-style analysis of this candidate. Format your response in clear, well-structured markdown.

🚨 CRITICAL RULE: You MUST ONLY evaluate the candidate against the exact skills, technologies, and requirements explicitly listed in the job description. DO NOT evaluate against any other skills, frameworks, or technologies not mentioned in the job requirements.

{context_data}

**FORBIDDEN ACTIONS - DO NOT DO THESE:**
❌ Do NOT mention skills like Java, Go, AWS, GCP, Redis, Docker, Kubernetes unless they are explicitly listed in the job requirements above
❌ Do NOT evaluate against "commonly expected" skills for the role type
❌ Do NOT assume additional technical requirements beyond what is stated in the job description
❌ Do NOT use phrases like "typically required for this role" or "standard for this position"
❌ Do NOT mention ANY technology, framework, or skill that is not explicitly listed in the REQUIRED or PREFERRED skills above
❌ Do NOT create "technical gaps" for skills not mentioned in the job requirements

**CRITICAL FORMATTING REQUIREMENTS:**
- Use proper markdown headers (##, ###)
- Include bullet points and numbered lists with specific examples
- Use **bold** for key strengths and critical gaps
- Use ✅ for strengths, ⚠️ for concerns, 📈 for opportunities
- Include priority levels (High/Medium/Low) for recommendations
- Make actionable insights clearly identifiable

**Content Structure:**
### ✅ Key Strengths & Competitive Advantages
1. **Technical Excellence**: Only mention technical capabilities relevant to job requirements
2. **Professional Experience**: Career highlights and achievements relevant to job requirements
3. **Domain Expertise**: Industry knowledge and specializations mentioned in job requirements
4. **Soft Skills**: Communication, leadership, collaboration as relevant to the specific role

### ⚠️ Areas of Concern & Risk Factors
1. **Technical Gaps**: ONLY mention missing skills that are explicitly listed in the job requirements above
2. **Experience Limitations**: Role or industry experience gaps relative to specific job requirements
3. **Portfolio Weaknesses**: Project or code quality concerns relevant to the technologies mentioned in job requirements
4. **Professional Risks**: Potential culture or performance risks specific to this exact role

**MANDATORY RULE**: Only mention missing skills if they are explicitly listed in the job requirements. Do not create gaps for technologies not mentioned in the job description.

### 🎯 Development Recommendations
1. **Immediate Priorities** (High): Critical skills to develop
2. **Medium-term Goals** (Medium): Growth opportunities  
3. **Long-term Potential** (Low): Future development areas

### 📈 Growth Potential Assessment
Evaluate their capacity for learning, adaptation, and advancement in the role.

Be specific with examples, priorities, and actionable development paths."""

        swot_response = await llm.ainvoke([
            SystemMessage(content="You are a talent assessment expert. 🚨 CRITICAL: Provide balanced, actionable strengths and weaknesses analysis. ONLY evaluate against the specific skills and requirements mentioned in the job description. DO NOT mention skills like Java, Go, AWS, GCP, Redis unless they are explicitly listed in the job requirements. DO NOT create technical gaps for skills not mentioned in the job requirements. Format all responses in clean, well-structured markdown with proper headers, bullet points, and line breaks."),
            HumanMessage(content=swot_prompt)
        ])
        
        swot_section = f"""## 💪 Strengths and Development Analysis

{swot_response.content.strip()}

---
"""
        
        await manager.send_final_analysis_stream(analysis_id, swot_section)
        await asyncio.sleep(0.8)
        
        # Stream Part 5: Hiring Recommendation
        await manager.send_final_analysis_stream(analysis_id, "🔄 **Formulating hiring recommendation...**")
        
        recommendation_prompt = f"""Provide a comprehensive hiring recommendation based on all analysis:

🚨 CRITICAL RULE: You MUST ONLY evaluate the candidate against the exact skills, technologies, and requirements explicitly listed in the job description. DO NOT evaluate against any other skills, frameworks, or technologies not mentioned in the job requirements.

{context_data}

**FORBIDDEN ACTIONS - DO NOT DO THESE:**
❌ Do NOT mention skills like Java, Go, AWS, GCP, Redis, Docker, Kubernetes unless they are explicitly listed in the job requirements above
❌ Do NOT evaluate against "commonly expected" skills for the role type
❌ Do NOT assume additional technical requirements beyond what is stated in the job description
❌ Do NOT penalize the candidate for not having skills that aren't required for the job
❌ Do NOT mention ANY technology, framework, or skill that is not explicitly listed in the REQUIRED or PREFERRED skills above

Current Score: {final_score}/100
Current Recommendation: {recommendation}

Provide:
1. **Final Hiring Decision** with rationale
2. **Confidence Level** and reasoning
3. **Next Steps** for the hiring process
4. **Risk Assessment** - potential concerns
5. **Onboarding Considerations** - what support they might need
6. **Alternative Recommendations** - other role levels or positions

Be decisive but balanced. Consider both current capabilities and growth potential."""

        recommendation_response = await llm.ainvoke([
            SystemMessage(content="You are a senior hiring manager. 🚨 CRITICAL: Make clear, decisive hiring recommendations with full justification. Base your assessment ONLY on the specific skills and requirements mentioned in the job description. DO NOT mention skills like Java, Go, AWS, GCP, Redis unless they are explicitly listed in the job requirements. DO NOT penalize candidates for not having skills that aren't required for the job. Format all responses in clean, well-structured markdown with proper headers, bullet points, and line breaks."),
            HumanMessage(content=recommendation_prompt)
        ])
        
        recommendation_section = f"""## 🎯 Final Hiring Recommendation

{recommendation_response.content.strip()}

**Analysis Score:** {final_score:.1f}/100  
**Decision:** {recommendation}

---
"""
        
        await manager.send_final_analysis_stream(analysis_id, recommendation_section)
        await asyncio.sleep(0.8)
        
        # Stream Part 6: Metadata and Completion
        metadata_section = f"""## 📊 Analysis Metadata

- **Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Analysis Type:** LLM-Enhanced Comprehensive Review
- **AI Model:** GPT-4 with Multi-Agent Analysis
- **Data Sources:** Resume, GitHub, LinkedIn, Twitter/X, Medium, Projects, Company Research
- **Confidence:** High (AI-Generated with Human Review Recommended)

---

**🎉 Analysis Complete!** This comprehensive report has been generated using advanced AI analysis across multiple data sources. Use this as a supplementary tool alongside human judgment for final hiring decisions.

*End of Report* ✨"""
        
        await manager.send_final_analysis_stream(analysis_id, metadata_section, is_complete=True)
        
        
        # Return combined report for storage
        full_report = executive_summary + technical_section + professional_section + swot_section + recommendation_section + metadata_section
        return full_report
        
    except Exception as e:
        import traceback
        
        error_message = f"""# Analysis Report - Error

An error occurred while generating the LLM streaming analysis: {str(e)}

## Basic Results
- Score: {final_score:.1f}/100
- Recommendation: {recommendation}

Please try the analysis again or contact support if the issue persists."""
        
        if analysis_id:
            await manager.send_final_analysis_stream(analysis_id, error_message, is_complete=True)
        
        return error_message