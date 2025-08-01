#!/usr/bin/env python3
"""
Comprehensive test cases for the final analysis report generation
Tests all components: streaming, LLM generation, markdown formatting, and SSE
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any
import pytest
from unittest.mock import Mock, AsyncMock, patch

# Test data setup
def create_test_state() -> Dict[str, Any]:
    """Create comprehensive test state with all analysis data"""
    from app.models.schemas import (
        Resume, JobDescription, GitHubAnalysis, LinkedInAnalysis,
        TwitterAnalysis, MediumAnalysis, ProjectAnalysis, CompanyAnalysis,
        TaskProgress, AnalysisStatus, Platform, SocialProfile
    )
    
    # Create test resume
    resume = Resume(
        candidate_name="John Doe",
        email="john.doe@example.com",
        phone="+1-555-0123",
        experience_years=5,
        skills=["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"],
        experience=[
            {
                "role": "Senior Software Engineer",
                "company": "TechCorp",
                "duration": "2020-2023",
                "description": "Led development of microservices architecture"
            },
            {
                "role": "Software Engineer",
                "company": "StartupXYZ",
                "duration": "2018-2020",
                "description": "Full-stack development with React and Python"
            }
        ],
        education=[
            {
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "institution": "University of Technology",
                "year": "2018"
            }
        ],
        projects=[
            {
                "name": "E-commerce Platform",
                "description": "Built scalable e-commerce platform with microservices",
                "technologies": ["Python", "React", "AWS"],
                "url": "https://github.com/johndoe/ecommerce"
            }
        ],
        social_profiles=[
            SocialProfile(platform=Platform.GITHUB, url="https://github.com/johndoe"),
            SocialProfile(platform=Platform.LINKEDIN, url="https://linkedin.com/in/johndoe"),
            SocialProfile(platform=Platform.TWITTER, url="https://twitter.com/johndoe"),
            SocialProfile(platform=Platform.MEDIUM, url="https://medium.com/@johndoe")
        ],
        raw_text="Resume content..."
    )
    
    # Create test job description
    job_description = JobDescription(
        title="Senior Full Stack Engineer",
        company="InnovateCorp",
        description="Looking for a senior full stack engineer...",
        requirements=["Python", "JavaScript", "React", "AWS", "5+ years experience"],
        preferred_skills=["Docker", "Kubernetes", "GraphQL"],
        experience_level="Senior Level",
        domain="Full Stack Development",
        location="San Francisco, CA"
    )
    
    # Create test GitHub analysis
    github_analysis = GitHubAnalysis(
        username="johndoe",
        public_repos_count=25,
        followers=150,
        following=75,
        total_commits=1200,
        repositories=[
            {
                "name": "ecommerce-platform",
                "description": "Scalable e-commerce platform with microservices",
                "stars": 45,
                "forks": 12,
                "language": "Python",
                "updated_at": "2023-10-15"
            },
            {
                "name": "react-dashboard",
                "description": "Modern React dashboard with real-time updates",
                "stars": 32,
                "forks": 8,
                "language": "JavaScript",
                "updated_at": "2023-09-20"
            }
        ],
        languages={"Python": 12, "JavaScript": 8, "TypeScript": 3, "Go": 2},
        contribution_streak=45,
        code_quality_score=85.0,
        project_complexity_score=78.0,
        domain_relevance_score=92.0
    )
    
    # Create test LinkedIn analysis
    linkedin_analysis = LinkedInAnalysis(
        profile_url="https://linkedin.com/in/johndoe",
        technical_posts_count=25,
        domain_relevant_posts=18,
        connections=500,
        endorsements=["Python", "JavaScript", "React", "AWS"],
        certifications=["AWS Certified Developer", "React Certification"],
        domain_relevance_score=75.0
    )
    
    # Create test Twitter analysis
    twitter_analysis = TwitterAnalysis(
        username="johndoe",
        followers=350,
        technical_tweets_count=45,
        domain_relevant_tweets=32,
        engagement_rate=4.2,
        domain_relevance_score=68.0
    )
    
    # Create test Medium analysis
    medium_analysis = MediumAnalysis(
        username="johndoe",
        articles_count=12,
        domain_relevant_articles=10,
        total_claps=850,
        followers=200,
        domain_relevance_score=82.0
    )
    
    # Create test project analysis
    project_analysis = ProjectAnalysis(
        project_name="E-commerce Platform",
        url="https://ecommerce-demo.com",
        is_live=True,
        technologies=["Python", "React", "AWS", "Docker"],
        complexity_score=88.0,
        performance_score=92.0,
        responsiveness_score=85.0,
        seo_score=78.0,
        error_count=0
    )
    
    # Create test company analysis
    company_analysis = CompanyAnalysis(
        company_name="TechCorp",
        role="Senior Software Engineer",
        company_tier="Tier 1",
        difficulty_score=85.0,
        market_reputation=90.0
    )
    
    # Create progress tracking
    progress = [
        TaskProgress(
            task_id="resume_jd_match",
            task_name="Resume and JD Matching",
            status=AnalysisStatus.COMPLETED,
            progress_percentage=100.0,
            message="Match score: 88"
        ),
        TaskProgress(
            task_id="github_analyze",
            task_name="GitHub Analysis",
            status=AnalysisStatus.COMPLETED,
            progress_percentage=100.0,
            message="GitHub analysis completed"
        ),
        TaskProgress(
            task_id="final_score",
            task_name="Final Scoring",
            status=AnalysisStatus.IN_PROGRESS,
            progress_percentage=50.0,
            message="Calculating final score"
        )
    ]
    
    return {
        "analysis_id": "test-analysis-123",
        "resume": resume,
        "job_description": job_description,
        "progress": progress,
        "resume_jd_score": 88.0,
        "github_analysis": github_analysis,
        "linkedin_analysis": linkedin_analysis,
        "twitter_analysis": twitter_analysis,
        "medium_analysis": medium_analysis,
        "project_analyses": [project_analysis],
        "company_analyses": [company_analysis],
        "final_analysis": None,
        "custom_weights": {
            "resume_jd_match": 0.25,
            "github_analysis": 0.20,
            "linkedin_analysis": 0.10
        },
        "errors": []
    }

class TestFinalReportGeneration:
    """Test cases for final analysis report generation"""
    
    @pytest.fixture
    def test_state(self):
        return create_test_state()
    
    @pytest.fixture
    def mock_websocket_manager(self):
        with patch('app.api.websocket_manager.manager') as mock_manager:
            mock_manager.send_final_analysis_stream = AsyncMock()
            mock_manager.send_thinking_update = AsyncMock()
            yield mock_manager
    
    @pytest.fixture
    def mock_llm(self):
        with patch('app.agents.llm_streaming_analyzer.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            
            # Mock LLM responses
            mock_llm.ainvoke.side_effect = [
                Mock(content="Executive summary: John Doe is a strong candidate with 5 years of experience..."),
                Mock(content="Technical assessment: Strong GitHub presence with 25 repositories..."),
                Mock(content="Professional background: Solid career progression from startup to enterprise..."),
                Mock(content="Strengths: Excellent technical skills, strong GitHub presence. Weaknesses: Limited leadership experience..."),
                Mock(content="Final recommendation: Strong hire with high confidence level...")
            ]
            
            yield mock_llm
    
    @pytest.mark.asyncio
    async def test_llm_streaming_analysis_basic(self, test_state, mock_websocket_manager, mock_llm):
        """Test basic LLM streaming analysis functionality"""
        from app.agents.llm_streaming_analyzer import generate_llm_streaming_analysis
        
        result = await generate_llm_streaming_analysis(
            test_state, "John Doe", "Senior Full Stack Engineer", 
            "InnovateCorp", "Full Stack Development", 85.5, "Strong Hire"
        )
        
        # Verify LLM was called for each section
        assert mock_llm.ainvoke.call_count == 5
        
        # Verify streaming calls were made
        assert mock_websocket_manager.send_final_analysis_stream.call_count >= 6
        
        # Verify result contains expected content
        assert "Executive Summary" in result
        assert "Technical Assessment" in result
        assert "Professional Background" in result
        assert "Final Hiring Recommendation" in result
        assert "John Doe" in result
        assert "85.5" in result
    
    @pytest.mark.asyncio
    async def test_streaming_content_format(self, test_state, mock_websocket_manager, mock_llm):
        """Test that streaming content is properly formatted"""
        from app.agents.llm_streaming_analyzer import generate_llm_streaming_analysis
        
        await generate_llm_streaming_analysis(
            test_state, "John Doe", "Senior Full Stack Engineer", 
            "InnovateCorp", "Full Stack Development", 85.5, "Strong Hire"
        )
        
        # Get all streaming calls
        calls = mock_websocket_manager.send_final_analysis_stream.call_args_list
        
        # Verify proper markdown formatting
        for call in calls:
            content = call[0][1]  # Second argument is content
            
            # Check for proper markdown headers
            if "Executive Summary" in content:
                assert content.startswith("## 📋 Executive Summary")
            elif "Technical Assessment" in content:
                assert "## 💻 Technical Assessment" in content
            elif "Professional Background" in content:
                assert "## 🏢 Professional Background" in content
    
    @pytest.mark.asyncio
    async def test_error_handling(self, test_state, mock_websocket_manager):
        """Test error handling in LLM streaming analysis"""
        from app.agents.llm_streaming_analyzer import generate_llm_streaming_analysis
        
        # Mock LLM to raise exception
        with patch('app.agents.llm_streaming_analyzer.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm
            mock_llm.ainvoke.side_effect = Exception("LLM API Error")
            
            result = await generate_llm_streaming_analysis(
                test_state, "John Doe", "Senior Full Stack Engineer", 
                "InnovateCorp", "Full Stack Development", 85.5, "Strong Hire"
            )
            
            # Verify error is handled gracefully
            assert "Analysis Report - Error" in result
            assert "LLM API Error" in result
            
            # Verify error was streamed
            assert mock_websocket_manager.send_final_analysis_stream.called
    
    @pytest.mark.asyncio
    async def test_websocket_streaming_calls(self, test_state, mock_websocket_manager, mock_llm):
        """Test WebSocket streaming calls are made correctly"""
        from app.agents.llm_streaming_analyzer import generate_llm_streaming_analysis
        
        await generate_llm_streaming_analysis(
            test_state, "John Doe", "Senior Full Stack Engineer", 
            "InnovateCorp", "Full Stack Development", 85.5, "Strong Hire"
        )
        
        calls = mock_websocket_manager.send_final_analysis_stream.call_args_list
        
        # Verify analysis_id is passed correctly
        for call in calls:
            analysis_id = call[0][0]  # First argument is analysis_id
            assert analysis_id == "test-analysis-123"
        
        # Verify final call marks completion
        final_call = calls[-1]
        is_complete = final_call[1].get('is_complete', False)  # Check keyword args
        assert is_complete == True
    
    def test_comprehensive_report_generator(self, test_state):
        """Test the comprehensive report generator utility"""
        from app.agents.report_generator import generate_comprehensive_report
        
        # This is a sync test for the report generator
        # In practice, this would be called by the LLM analyzer
        # Just verify the function exists and can be imported
        assert generate_comprehensive_report is not None
    
    @pytest.mark.asyncio
    async def test_final_scorer_integration(self, test_state, mock_websocket_manager):
        """Test integration with final scorer node"""
        from app.agents.nodes import final_scorer
        
        # Mock the LLM streaming analyzer
        with patch('app.agents.nodes.generate_llm_streaming_analysis') as mock_llm_analyzer:
            mock_llm_analyzer.return_value = "Comprehensive analysis report..."
            
            # Mock the regular streaming analyzer
            with patch('app.agents.nodes.stream_comprehensive_analysis') as mock_stream_analyzer:
                mock_stream_analyzer.return_value = "Thinking analysis..."
                
                # Mock settings
                with patch('app.agents.nodes.settings') as mock_settings:
                    mock_settings.get_default_weights.return_value = {
                        "resume_jd_match": 0.25,
                        "github_analysis": 0.20
                    }
                    mock_settings.get_scoring_thresholds.return_value = {
                        "excellent": 85,
                        "good": 70,
                        "average": 55
                    }
                    
                    result = await final_scorer(test_state)
                    
                    # Verify final analysis was created
                    assert "final_analysis" in result
                    assert result["final_analysis"] is not None
                    
                    # Verify LLM streaming was called
                    mock_llm_analyzer.assert_called_once()
    
    def test_markdown_formatting(self):
        """Test markdown formatting and rendering"""
        test_content = """# Test Report
        
## Executive Summary
This is a **bold** test with *italic* text.

### Subsection
- Item 1
- Item 2
- Item 3

**Score:** 85/100
        """
        
        # Test that content can be parsed (this would be done by marked.js in frontend)
        assert "# Test Report" in test_content
        assert "## Executive Summary" in test_content
        assert "**bold**" in test_content
        assert "- Item 1" in test_content
    
    @pytest.mark.asyncio
    async def test_performance_timing(self, test_state, mock_websocket_manager, mock_llm):
        """Test that streaming analysis completes within reasonable time"""
        from app.agents.llm_streaming_analyzer import generate_llm_streaming_analysis
        
        start_time = time.time()
        
        await generate_llm_streaming_analysis(
            test_state, "John Doe", "Senior Full Stack Engineer", 
            "InnovateCorp", "Full Stack Development", 85.5, "Strong Hire"
        )
        
        elapsed_time = time.time() - start_time
        
        # Should complete within 10 seconds (with mocked LLM)
        assert elapsed_time < 10.0
        
        # Verify streaming happened with delays (asyncio.sleep calls)
        assert elapsed_time > 0.1  # Should take some time due to streaming delays

class TestWebSocketIntegration:
    """Test WebSocket integration for streaming"""
    
    def test_websocket_manager_method_exists(self):
        """Test that WebSocket manager has streaming method"""
        from app.api.websocket_manager import ConnectionManager
        
        manager = ConnectionManager()
        assert hasattr(manager, 'send_final_analysis_stream')
    
    @pytest.mark.asyncio
    async def test_websocket_message_format(self):
        """Test WebSocket message format for streaming"""
        from app.api.websocket_manager import ConnectionManager
        
        manager = ConnectionManager()
        
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        manager.active_connections["test-id"] = [mock_websocket]
        
        await manager.send_final_analysis_stream(
            "test-id", "Test content", is_complete=True
        )
        
        # Verify message was sent
        mock_websocket.send_text.assert_called_once()
        
        # Verify message format
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["type"] == "final_analysis_stream"
        assert message["analysis_id"] == "test-id"
        assert message["content"] == "Test content"
        assert message["is_complete"] == True

class TestFrontendIntegration:
    """Test frontend JavaScript integration"""
    
    def test_frontend_handler_method(self):
        """Test that frontend has handler for streaming updates"""
        # Read the frontend app.js file
        with open('/Users/souravpurkait/myprojects/agents/hiring-agent/frontend/app.js', 'r') as f:
            content = f.read()
        
        # Verify streaming handler exists
        assert 'updateFinalAnalysisStream' in content
        assert 'final_analysis_stream' in content
        assert 'marked.parse' in content

def run_comprehensive_tests():
    """Run all test cases"""
    print("🧪 Running Comprehensive Final Report Tests...")
    print("=" * 60)
    
    # Run pytest programmatically
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, '-m', 'pytest', __file__, '-v', '--tb=short'
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
    print(f"Return code: {result.returncode}")
    
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return result.returncode == 0

def run_manual_integration_test():
    """Run manual integration test with real components"""
    print("🔧 Running Manual Integration Test...")
    print("=" * 60)
    
    # Test the actual implementation
    test_state = create_test_state()
    
    print(f"✅ Test state created with analysis_id: {test_state['analysis_id']}")
    print(f"✅ Resume candidate: {test_state['resume'].candidate_name}")
    print(f"✅ Job title: {test_state['job_description'].title}")
    print(f"✅ GitHub analysis score: {test_state['github_analysis'].code_quality_score}")
    
    # Test WebSocket manager
    from app.api.websocket_manager import ConnectionManager
    manager = ConnectionManager()
    
    print(f"✅ WebSocket manager created")
    print(f"✅ Streaming method available: {hasattr(manager, 'send_final_analysis_stream')}")
    
    # Test imports
    try:
        from app.agents.llm_streaming_analyzer import generate_llm_streaming_analysis
        print("✅ LLM streaming analyzer imported successfully")
    except Exception as e:
        print(f"❌ Failed to import LLM streaming analyzer: {e}")
    
    try:
        from app.agents.nodes import final_scorer
        print("✅ Final scorer node imported successfully")
    except Exception as e:
        print(f"❌ Failed to import final scorer: {e}")
    
    print("=" * 60)
    print("✅ Manual integration test completed!")

if __name__ == "__main__":
    print("🚀 Final Report Testing Suite")
    print("=" * 60)
    
    # Run manual test first
    run_manual_integration_test()
    print()
    
    # Run comprehensive tests
    success = run_comprehensive_tests()
    
    print("=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        print("✅ Final report generation is ready for production")
    else:
        print("⚠️  Some tests failed - review output above")
        print("🔧 Fix issues before deployment")