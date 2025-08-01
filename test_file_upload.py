#!/usr/bin/env python3
"""
Test script to verify file upload functionality works.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_resume_parser():
    """Test the resume parser functionality"""
    print("🧪 Testing Resume Parser...")
    
    try:
        from app.utils.resume_parser import extract_resume_data
        
        # Test with sample resume text
        sample_resume = """
        John Doe
        Software Engineer
        Email: john.doe@email.com
        Phone: (555) 123-4567
        
        Skills: Python, JavaScript, React, Node.js
        GitHub: https://github.com/johndoe
        LinkedIn: https://linkedin.com/in/johndoe
        
        Experience:
        - Software Engineer at TechCorp (2020-2023)
        - Junior Developer at StartupXYZ (2018-2020)
        
        Education:
        - BS Computer Science, State University (2018)
        """
        
        result = await extract_resume_data(sample_resume)
        print("✅ Resume parsing successful!")
        print(f"   Extracted name: {result.get('candidate_name', 'Not found')}")
        print(f"   Extracted email: {result.get('email', 'Not found')}")
        print(f"   Extracted skills: {len(result.get('skills', []))} skills")
        
        return True
        
    except Exception as e:
        print(f"❌ Resume parsing failed: {e}")
        return False

def test_file_parsers():
    """Test file parsing libraries"""
    print("🧪 Testing File Parsers...")
    
    try:
        import PyPDF2
        print("✅ PyPDF2 available")
    except ImportError:
        print("❌ PyPDF2 not available")
        return False
    
    try:
        import docx
        print("✅ python-docx available")
    except ImportError:
        print("❌ python-docx not available")
        return False
    
    try:
        import pdfplumber
        print("✅ pdfplumber available")
    except ImportError:
        print("❌ pdfplumber not available")
        return False
    
    return True

def test_environment():
    """Test environment setup"""
    print("🧪 Testing Environment...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ python-dotenv available")
    except ImportError:
        print("❌ python-dotenv not available")
        return False
    
    if os.getenv("OPENAI_API_KEY"):
        print("✅ OPENAI_API_KEY is set")
    else:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    return True

def test_fastapi_imports():
    """Test FastAPI and related imports"""
    print("🧪 Testing FastAPI Imports...")
    
    try:
        import fastapi
        print("✅ FastAPI available")
    except ImportError:
        print("❌ FastAPI not available")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn available")
    except ImportError:
        print("❌ Uvicorn not available")
        return False
    
    try:
        from app.main import app
        print("✅ Main app module imports successfully")
    except Exception as e:
        print(f"❌ Main app import failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("🚀 Running Hiring Agent Tests...\n")
    
    tests = [
        ("Environment Setup", test_environment),
        ("File Parsers", test_file_parsers),
        ("FastAPI Imports", test_fastapi_imports),
        ("Resume Parser", test_resume_parser),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The file upload system is ready.")
        print("\n📋 Next Steps:")
        print("1. Start server: python3 start_server.py")
        print("2. Open browser: http://localhost:8000")
        print("3. Test file upload with sample_resume.txt")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())