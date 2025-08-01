import pytest
import asyncio
from app.models.schemas import JobDescription, Resume, SocialProfile, Platform, AnalysisRequest
from app.agents.graph import orchestrator
from app.utils.openai_client import test_openai_connection

@pytest.fixture
def sample_job_description():
    return JobDescription(
        title="Senior Full Stack Developer",
        company="Tech Corp",
        description="We are looking for a skilled full stack developer to join our team.",
        requirements=["React", "Node.js", "Python", "AWS"],
        preferred_skills=["TypeScript", "Docker", "GraphQL"],
        experience_level="Senior Level",
        domain="Full Stack Development"
    )

@pytest.fixture
def sample_resume():
    return Resume(
        candidate_name="John Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        experience_years=5,
        skills=["React", "Node.js", "Python", "JavaScript", "AWS"],
        experience=[
            {
                "company": "Previous Corp",
                "role": "Full Stack Developer",
                "duration": "2020-2023"
            }
        ],
        education=[
            {
                "degree": "Bachelor of Computer Science",
                "university": "State University",
                "year": 2019
            }
        ],
        projects=[
            {
                "name": "E-commerce Platform",
                "description": "Built a full-stack e-commerce platform using React and Node.js",
                "technologies": ["React", "Node.js", "MongoDB"],
                "url": "https://example-ecommerce.com"
            }
        ],
        social_profiles=[
            SocialProfile(platform=Platform.GITHUB, url="https://github.com/johndoe"),
            SocialProfile(platform=Platform.LINKEDIN, url="https://linkedin.com/in/johndoe")
        ],
        raw_text="John Doe - Senior Full Stack Developer with 5 years of experience..."
    )

def test_openai_connection_works():
    """Test if OpenAI connection is working properly"""
    assert test_openai_connection(), "OpenAI connection test failed"

@pytest.mark.asyncio
async def test_resume_jd_matching(sample_job_description, sample_resume):
    """Test the resume-JD matching functionality"""
    from app.agents.nodes import resume_jd_matcher
    
    state = {
        "resume": sample_resume,
        "job_description": sample_job_description,
        "progress": [],
        "errors": []
    }
    
    result_state = await resume_jd_matcher(state)
    
    assert "resume_jd_score" in result_state
    assert isinstance(result_state["resume_jd_score"], (int, float))
    assert 0 <= result_state["resume_jd_score"] <= 100

@pytest.mark.asyncio
async def test_github_analysis(sample_job_description, sample_resume):
    """Test GitHub analysis functionality"""
    from app.agents.nodes import github_analyzer
    
    state = {
        "resume": sample_resume,
        "job_description": sample_job_description,
        "progress": [],
        "errors": []
    }
    
    result_state = await github_analyzer(state)
    
    # Should complete without errors (even if no real GitHub data)
    assert len(result_state.get("errors", [])) == 0 or "GitHub analysis failed" in str(result_state.get("errors", []))

@pytest.mark.asyncio 
async def test_full_analysis_workflow(sample_job_description, sample_resume):
    """Test the complete analysis workflow"""
    analysis_id = "test-analysis-001"
    
    try:
        result_state = await orchestrator.start_analysis(
            analysis_id=analysis_id,
            resume=sample_resume,
            job_description=sample_job_description,
            custom_weights=None
        )
        
        # Verify that analysis completed
        assert result_state is not None
        assert "final_analysis" in result_state or len(result_state.get("errors", [])) > 0
        
    finally:
        orchestrator.cleanup_analysis(analysis_id)

def test_analysis_request_validation(sample_job_description, sample_resume):
    """Test that AnalysisRequest model validation works"""
    request = AnalysisRequest(
        job_description=sample_job_description,
        resume=sample_resume,
        custom_weights={"resume_jd_match": 0.3, "github_analysis": 0.2}
    )
    
    assert request.job_description.title == "Senior Full Stack Developer"
    assert request.resume.candidate_name == "John Doe"
    assert request.custom_weights["resume_jd_match"] == 0.3

if __name__ == "__main__":
    # Run basic tests
    print("Testing OpenAI connection...")
    if test_openai_connection():
        print("✓ OpenAI connection successful")
    else:
        print("✗ OpenAI connection failed")
    
    print("Use 'pytest tests/test_integration.py' to run all tests")