import io
import re
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json

def parse_pdf_resume(content: bytes) -> str:
    """Parse PDF resume content and extract text"""
    try:
        import PyPDF2
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except ImportError:
        # Fallback if PyPDF2 is not available
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except ImportError:
            raise Exception("PDF parsing libraries not available. Please install PyPDF2 or pdfplumber.")

def parse_docx_resume(content: bytes) -> str:
    """Parse DOCX resume content and extract text"""
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    except ImportError:
        raise Exception("DOCX parsing library not available. Please install python-docx.")

async def extract_resume_data(resume_text: str) -> Dict[str, Any]:
    """Extract structured data from resume text using AI"""
    llm = ChatOpenAI(model="gpt-4", temperature=0.1)
    
    system_message = SystemMessage(content="""
    Extract structured information from the resume text and return it as JSON.
    Include the following fields:
    - candidate_name: Full name
    - email: Email address
    - phone: Phone number
    - experience_years: Estimated years of experience (integer)
    - skills: Array of technical skills
    - experience: Array of work experience objects with company, role, duration, description
    - education: Array of education objects with degree, university, year
    - projects: Array of project objects with name, description, technologies, url (if mentioned)
    - social_profiles: Array of social media URLs found in the resume
    
    Return valid JSON only, no additional text.
    """)
    
    human_message = HumanMessage(content=f"Resume text:\n{resume_text}")
    
    try:
        response = await llm.ainvoke([system_message, human_message])
        structured_data = json.loads(response.content)
        
        # Process social profiles to detect platform types
        if 'social_profiles' in structured_data:
            processed_profiles = []
            for url in structured_data['social_profiles']:
                platform = detect_platform(url)
                processed_profiles.append({
                    "platform": platform,
                    "url": url
                })
            structured_data['social_profiles'] = processed_profiles
        
        return structured_data
    
    except Exception as e:
        # Return basic extraction if AI parsing fails
        return extract_basic_info(resume_text)

def detect_platform(url: str) -> str:
    """Detect social media platform from URL"""
    url_lower = url.lower()
    if 'github.com' in url_lower:
        return 'github'
    elif 'linkedin.com' in url_lower:
        return 'linkedin'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    elif 'medium.com' in url_lower:
        return 'medium'
    else:
        return 'other'

def extract_basic_info(resume_text: str) -> Dict[str, Any]:
    """Basic regex-based extraction as fallback"""
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, resume_text)
    
    # Extract phone numbers
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, resume_text)
    
    # Extract URLs
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
    urls = re.findall(url_pattern, resume_text)
    
    # Process social profiles
    social_profiles = []
    for url in urls:
        platform = detect_platform(url)
        social_profiles.append({
            "platform": platform,
            "url": url
        })
    
    return {
        "candidate_name": "Unknown",
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "experience_years": None,
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "social_profiles": social_profiles
    }