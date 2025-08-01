#!/usr/bin/env python3
"""
Quick test script to verify the hiring agent setup and basic functionality.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.models.schemas import JobDescription, Resume, SocialProfile, Platform
from app.utils.openai_client import test_openai_connection

def test_environment_setup():
    """Test if all required environment variables are set"""
    required_vars = ["OPENAI_API_KEY"]
    optional_vars = ["GITHUB_TOKEN", "LINKEDIN_TOKEN", "TWITTER_BEARER_TOKEN", "MEDIUM_TOKEN"]
    
    print("=== Environment Setup Test ===")
    
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"✓ {var} is set")
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✓ {var} is set")
        else:
            print(f"⚠ {var} is not set (optional)")
    
    if missing_required:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_required)}")
        return False
    
    print("\n✅ Environment setup is valid")
    return True

def test_models():
    """Test if Pydantic models work correctly"""
    print("\n=== Models Test ===")
    
    try:
        # Test JobDescription model
        jd = JobDescription(
            title="Software Engineer",
            company="Test Corp",
            description="Test description",
            requirements=["Python", "React"],
            preferred_skills=["Docker"],
            experience_level="Mid Level",
            domain="Full Stack"
        )
        print("✓ JobDescription model works")
        
        # Test Resume model
        resume = Resume(
            candidate_name="Test User",
            email="test@example.com",
            skills=["Python", "JavaScript"],
            experience=[{"company": "Test Corp", "role": "Developer"}],
            education=[{"degree": "BS CS", "university": "Test Uni"}],
            projects=[{"name": "Test Project", "description": "Test"}],
            social_profiles=[
                SocialProfile(platform=Platform.GITHUB, url="https://github.com/test")
            ],
            raw_text="Test resume text"
        )
        print("✓ Resume model works")
        
        print("✅ All models are working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_openai():
    """Test OpenAI connection"""
    print("\n=== OpenAI Connection Test ===")
    
    if test_openai_connection():
        print("✅ OpenAI connection successful")
        return True
    else:
        print("❌ OpenAI connection failed")
        return False

async def test_basic_workflow():
    """Test basic workflow functionality"""
    print("\n=== Basic Workflow Test ===")
    
    try:
        from app.agents.nodes import resume_jd_matcher
        
        # Create test data
        jd = JobDescription(
            title="Python Developer",
            company="Test Corp",
            description="Looking for a Python developer",
            requirements=["Python", "Django"],
            preferred_skills=["FastAPI"],
            experience_level="Mid Level",
            domain="Backend Development"
        )
        
        resume = Resume(
            candidate_name="Test Candidate",
            email="candidate@example.com",
            skills=["Python", "Django", "FastAPI"],
            experience=[{"company": "Previous Corp", "role": "Python Developer"}],
            education=[{"degree": "BS CS", "university": "State Uni"}],
            projects=[{"name": "Web API", "description": "Built using FastAPI"}],
            social_profiles=[],
            raw_text="Experienced Python developer with Django and FastAPI skills"
        )
        
        # Test resume-JD matching
        state = {
            "resume": resume,
            "job_description": jd,
            "progress": [],
            "errors": []
        }
        
        result = await resume_jd_matcher(state)
        
        if "resume_jd_score" in result and isinstance(result["resume_jd_score"], (int, float)):
            print(f"✓ Resume-JD matching works (Score: {result['resume_jd_score']})")
            print("✅ Basic workflow test passed")
            return True
        else:
            print("❌ Resume-JD matching failed")
            return False
            
    except Exception as e:
        print(f"❌ Basic workflow test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Hiring Agent Tests\n")
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Models", test_models),
        ("OpenAI Connection", test_openai),
        ("Basic Workflow", test_basic_workflow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The hiring agent is ready to use.")
        print("\nNext steps:")
        print("1. Start the server: uvicorn app.main:app --reload")
        print("2. Open http://localhost:8000 in your browser")
        print("3. Fill in the job description and resume")
        print("4. Start analysis and watch the real-time progress")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        if not os.getenv("OPENAI_API_KEY"):
            print("\n💡 Make sure to set your OPENAI_API_KEY in the .env file")

if __name__ == "__main__":
    asyncio.run(main())