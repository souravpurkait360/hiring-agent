import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    return ChatOpenAI(
        model="gpt-4",
        temperature=0.1,
        openai_api_key=api_key
    )

def test_openai_connection():
    try:
        client = get_openai_client()
        response = client.invoke("Hello, this is a test message. Please respond with 'Connection successful'.")
        return "Connection successful" in response.content
    except Exception as e:
        print(f"OpenAI connection test failed: {e}")
        return False