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
        print("DEBUG: No analysis_id found for streaming")
        return "Analysis ID not found"
    
    try:
        print("DEBUG: Starting LLM streaming analysis")
        
        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4", temperature=0.3)
        
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
        context_data = f"""CANDIDATE ANALYSIS DATA:

BASIC INFO:
- Name: {candidate_name}
- Email: {getattr(resume, 'email', 'Not provided')}
- Experience: {getattr(resume, 'experience_years', 'Not specified')} years
- Skills: {', '.join(getattr(resume, 'skills', []))}

JOB REQUIREMENTS:
- Position: {job_title}
- Company: {job_company}
- Domain: {job_domain}
- Experience Level: {getattr(job_description, 'experience_level', 'Not specified')}
- Requirements: {', '.join(getattr(job_description, 'requirements', []))}
- Preferred Skills: {', '.join(getattr(job_description, 'preferred_skills', []))}

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
        print("DEBUG: Generating executive summary with LLM")
        await manager.send_final_analysis_stream(analysis_id, "# 📋 COMPREHENSIVE CANDIDATE ANALYSIS REPORT\n\n🔄 **Generating executive summary...**")
        
        executive_prompt = f"""Based on the following candidate data, write a comprehensive executive summary for a hiring decision report.

{context_data}

Write a professional executive summary that includes:
1. Candidate overview
2. Position fit assessment
3. Key qualifications
4. Overall recommendation

Keep it concise but informative. Use professional language suitable for hiring managers."""

        executive_response = await llm.ainvoke([
            SystemMessage(content="You are an expert hiring analyst. Write professional, concise analysis suitable for hiring decisions."),
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
        print("DEBUG: Generating technical assessment with LLM")
        await manager.send_final_analysis_stream(analysis_id, "🔄 **Analyzing technical capabilities...**")
        
        technical_prompt = f"""Based on the candidate's technical data, provide a detailed technical assessment:

{context_data}

Analyze:
1. Technical skill alignment with role requirements
2. Code quality and GitHub presence
3. Project portfolio strength
4. Programming language expertise
5. Technical complexity of work

Provide specific examples and scores where available. Be objective and detailed."""

        technical_response = await llm.ainvoke([
            SystemMessage(content="You are a technical hiring specialist. Analyze technical capabilities objectively."),
            HumanMessage(content=technical_prompt)
        ])
        
        technical_section = f"""## 💻 Technical Assessment

{technical_response.content.strip()}

---
"""
        
        await manager.send_final_analysis_stream(analysis_id, technical_section)
        await asyncio.sleep(0.8)
        
        # Stream Part 3: Professional Background
        print("DEBUG: Generating professional background analysis with LLM")
        await manager.send_final_analysis_stream(analysis_id, "🔄 **Evaluating professional background...**")
        
        professional_prompt = f"""Analyze the candidate's professional background and experience:

{context_data}

Focus on:
1. Work experience relevance
2. Career progression
3. Company quality and reputation
4. Role responsibilities alignment
5. Professional networking and presence

Provide insights on their career trajectory and professional maturity."""

        professional_response = await llm.ainvoke([
            SystemMessage(content="You are a professional background analyst. Evaluate career progression and experience quality."),
            HumanMessage(content=professional_prompt)
        ])
        
        professional_section = f"""## 🏢 Professional Background

{professional_response.content.strip()}

---
"""
        
        await manager.send_final_analysis_stream(analysis_id, professional_section)
        await asyncio.sleep(0.8)
        
        # Stream Part 4: Strengths and Weaknesses
        print("DEBUG: Generating strengths and weaknesses with LLM")
        await manager.send_final_analysis_stream(analysis_id, "🔄 **Identifying strengths and improvement areas...**")
        
        swot_prompt = f"""Provide a detailed SWOT-style analysis of this candidate:

{context_data}

Structure your response as:
1. **Key Strengths** - What makes them stand out
2. **Areas of Concern** - Potential weaknesses or gaps
3. **Improvement Recommendations** - Specific actionable advice
4. **Growth Potential** - Their potential for development

Be specific and provide actionable insights. Consider both technical and soft skills."""

        swot_response = await llm.ainvoke([
            SystemMessage(content="You are a talent assessment expert. Provide balanced, actionable strengths and weaknesses analysis."),
            HumanMessage(content=swot_prompt)
        ])
        
        swot_section = f"""## 💪 Strengths and Development Analysis

{swot_response.content.strip()}

---
"""
        
        await manager.send_final_analysis_stream(analysis_id, swot_section)
        await asyncio.sleep(0.8)
        
        # Stream Part 5: Hiring Recommendation
        print("DEBUG: Generating final hiring recommendation with LLM")
        await manager.send_final_analysis_stream(analysis_id, "🔄 **Formulating hiring recommendation...**")
        
        recommendation_prompt = f"""Provide a comprehensive hiring recommendation based on all analysis:

{context_data}

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
            SystemMessage(content="You are a senior hiring manager. Make clear, decisive hiring recommendations with full justification."),
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
        print("DEBUG: Generating analysis metadata")
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
        
        print("DEBUG: LLM streaming analysis completed successfully")
        
        # Return combined report for storage
        full_report = executive_summary + technical_section + professional_section + swot_section + recommendation_section + metadata_section
        return full_report
        
    except Exception as e:
        print(f"DEBUG: Error in LLM streaming analysis: {e}")
        import traceback
        print(f"DEBUG: LLM streaming error traceback: {traceback.format_exc()}")
        
        error_message = f"""# Analysis Report - Error

An error occurred while generating the LLM streaming analysis: {str(e)}

## Basic Results
- Score: {final_score:.1f}/100
- Recommendation: {recommendation}

Please try the analysis again or contact support if the issue persists."""
        
        if analysis_id:
            await manager.send_final_analysis_stream(analysis_id, error_message, is_complete=True)
        
        return error_message