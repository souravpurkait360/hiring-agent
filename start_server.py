#!/usr/bin/env python3
"""
Startup script for the Hiring Agent application.
"""

import os
import sys

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except ImportError:
    print("⚠️  python-dotenv not available, using system environment variables")

# Verify OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY is not set")
    print("Please set your OpenAI API key:")
    print("Option 1: Create .env file with: OPENAI_API_KEY=your_api_key_here")
    print("Option 2: Export environment variable: export OPENAI_API_KEY=your_api_key_here")
    sys.exit(1)

print("🚀 Starting Hiring Agent server...")

# Import and run the FastAPI app
try:
    import uvicorn
    
    if __name__ == "__main__":
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("Please install dependencies with: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting server: {e}")
    sys.exit(1)