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
    from config.settings import settings
    llm = ChatOpenAI(model=settings.get_model(), temperature=0.1)
    
    system_message = SystemMessage(content="""You are an expert resume parser. Extract structured information from resume text and return it as valid JSON.

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON - no markdown, no explanations, no additional text
2. Use null for missing information, never leave fields undefined
3. Extract information accurately from the provided text
4. If a field cannot be determined, use the specified default value

REQUIRED JSON FORMAT:
{
    "candidate_name": "string or null",
    "email": "string or null", 
    "phone": "string or null",
    "experience_years": "integer or null",
    "skills": ["array of technical skills"],
    "experience": [
        {
            "company": "string",
            "role": "string", 
            "duration": "string",
            "description": "string"
        }
    ],
    "education": [
        {
            "degree": "string",
            "field": "string",
            "institution": "string", 
            "year": "string or null"
        }
    ],
    "projects": [
        {
            "name": "string",
            "description": "string",
            "technologies": ["array of strings"],
            "url": "string or null"
        }
    ],
    "social_profiles": ["array of URLs as strings"]
}

EXTRACTION GUIDELINES:
- candidate_name: Extract full name from header/contact section
- email: Find email address (format: user@domain.com)
- phone: Extract phone number (any format)
- experience_years: Calculate total years of professional experience (integer only)
- skills: Extract technical skills, programming languages, frameworks, tools
- experience: Work history with company, job title, duration, and key responsibilities
- education: Degrees, certifications, schools with graduation year if available
- projects: Personal/professional projects with technologies used and URLs if mentioned
- social_profiles: Any social media or professional URLs (GitHub, LinkedIn, Twitter, etc.)

EXAMPLE OUTPUT:
{
    "candidate_name": "John Smith",
    "email": "john.smith@email.com",
    "phone": "+1-555-123-4567", 
    "experience_years": 5,
    "skills": ["Python", "JavaScript", "React", "Node.js", "AWS"],
    "experience": [
        {
            "company": "Tech Corp",
            "role": "Senior Developer",
            "duration": "2020-2023",
            "description": "Led development of web applications using React and Node.js"
        }
    ],
    "education": [
        {
            "degree": "Bachelor of Science",
            "field": "Computer Science", 
            "institution": "University of Technology",
            "year": "2019"
        }
    ],
    "projects": [
        {
            "name": "E-commerce Platform",
            "description": "Built full-stack e-commerce solution",
            "technologies": ["React", "Node.js", "MongoDB"],
            "url": "https://github.com/user/ecommerce"
        }
    ],
    "social_profiles": ["https://github.com/johnsmith", "https://linkedin.com/in/johnsmith"]
}""")
    
    human_message = HumanMessage(content=f"Resume text:\n{resume_text}")
    
    try:
        response = await llm.ainvoke([system_message, human_message])
        response_content = response.content.strip()
        
        # Clean up response - remove markdown code blocks if present
        if response_content.startswith('```json'):
            response_content = response_content[7:]
        if response_content.startswith('```'):
            response_content = response_content[3:]
        if response_content.endswith('```'):
            response_content = response_content[:-3]
        
        response_content = response_content.strip()
        
        # Parse JSON with better error handling
        try:
            structured_data = json.loads(response_content)
        except json.JSONDecodeError as json_error:
            print(f"JSON parsing failed: {json_error}")
            print(f"Response content: {response_content[:500]}...")
            
            # Try to extract JSON from response if it's wrapped in other text
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                try:
                    structured_data = json.loads(json_match.group())
                except:
                    raise json_error
            else:
                raise json_error
        
        # Validate and clean the structured data
        structured_data = validate_and_clean_data(structured_data)
        
        # Process social profiles to detect platform types
        if 'social_profiles' in structured_data and structured_data['social_profiles']:
            processed_profiles = []
            for url in structured_data['social_profiles']:
                if url and isinstance(url, str):
                    platform = detect_platform(url)
                    processed_profiles.append({
                        "platform": platform,
                        "url": url
                    })
            structured_data['social_profiles'] = processed_profiles
        else:
            structured_data['social_profiles'] = []
        
        return structured_data
    
    except Exception as e:
        print(f"Resume parsing error: {e}")
        # Return basic extraction if AI parsing fails
        return extract_basic_info(resume_text)

def validate_and_clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean the parsed resume data"""
    # Ensure all required fields exist with proper defaults
    cleaned_data = {
        "candidate_name": data.get("candidate_name") or None,
        "email": data.get("email") or None,
        "phone": data.get("phone") or None,
        "experience_years": data.get("experience_years"),
        "skills": data.get("skills", []),
        "experience": data.get("experience", []),
        "education": data.get("education", []),
        "projects": data.get("projects", []),
        "social_profiles": data.get("social_profiles", [])
    }
    
    # Clean experience_years to ensure it's an integer or None
    if cleaned_data["experience_years"] is not None:
        try:
            cleaned_data["experience_years"] = int(cleaned_data["experience_years"])
        except (ValueError, TypeError):
            cleaned_data["experience_years"] = None
    
    # Ensure arrays are actually arrays
    for array_field in ["skills", "experience", "education", "projects", "social_profiles"]:
        if not isinstance(cleaned_data[array_field], list):
            cleaned_data[array_field] = []
    
    # Clean experience objects
    if cleaned_data["experience"]:
        cleaned_experience = []
        for exp in cleaned_data["experience"]:
            if isinstance(exp, dict):
                cleaned_exp = {
                    "company": str(exp.get("company", "")),
                    "role": str(exp.get("role", "")),
                    "duration": str(exp.get("duration", "")),
                    "description": str(exp.get("description", ""))
                }
                cleaned_experience.append(cleaned_exp)
        cleaned_data["experience"] = cleaned_experience
    
    # Clean education objects
    if cleaned_data["education"]:
        cleaned_education = []
        for edu in cleaned_data["education"]:
            if isinstance(edu, dict):
                cleaned_edu = {
                    "degree": str(edu.get("degree", "")),
                    "field": str(edu.get("field", "")),
                    "institution": str(edu.get("institution", "")),
                    "year": edu.get("year")
                }
                cleaned_education.append(cleaned_edu)
        cleaned_data["education"] = cleaned_education
    
    # Clean project objects
    if cleaned_data["projects"]:
        cleaned_projects = []
        for proj in cleaned_data["projects"]:
            if isinstance(proj, dict):
                cleaned_proj = {
                    "name": str(proj.get("name", "")),
                    "description": str(proj.get("description", "")),
                    "technologies": proj.get("technologies", []) if isinstance(proj.get("technologies"), list) else [],
                    "url": proj.get("url")
                }
                cleaned_projects.append(cleaned_proj)
        cleaned_data["projects"] = cleaned_projects
    
    return cleaned_data

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