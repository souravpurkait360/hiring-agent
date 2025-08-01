# 📋 Hiring Agent - Usage Guide

## 🚀 Quick Start

### 1. Start the Server
```bash
python3 start_server.py
```

### 2. Open in Browser
Navigate to: `http://localhost:8000`

### 3. Use the Application

## 📝 Step-by-Step Guide

### **Step 1: Job Description**
- **Paste the complete job posting** in the large text area
- Include everything: title, company, requirements, responsibilities, etc.
- The AI will automatically extract relevant information

**Example:**
```
Senior Full Stack Developer at TechCorp

We are looking for a skilled Full Stack Developer...

Requirements:
- 5+ years of experience
- React, Node.js, Python
- AWS experience preferred

Responsibilities:
- Design and develop web applications
- Collaborate with cross-functional teams
```

### **Step 2: Upload Resume**
- **Click "Choose Files"** button to select resume file
- **Supported formats**: PDF, DOC, DOCX, TXT (Max 10MB)
- **AI automatically extracts**: name, email, skills, experience, social profiles
- **Review extracted data** and make corrections if needed

### **Step 3: Customize Weights (Optional)**
Adjust the importance of different analysis factors using sliders:
- **Resume-JD Match**: How well resume matches job description
- **GitHub Analysis**: Code quality and repository evaluation  
- **LinkedIn Analysis**: Professional content and network
- **Technical Blogs**: Medium articles and domain expertise
- **Project Quality**: Live project assessment
- **Work Experience**: Previous company difficulty

### **Step 4: Start Analysis**
- Click **"Start Analysis"** button
- Watch **real-time progress** for each analysis step:
  - ✅ Resume and JD Matching
  - ✅ GitHub Analysis  
  - ✅ LinkedIn Analysis
  - ✅ Twitter Analysis
  - ✅ Medium Analysis
  - ✅ Project Evaluation
  - ✅ Company Research
  - ✅ Final Scoring

### **Step 5: Review Results**
- **Overall Score**: 0-100 with hire recommendation
- **Detailed Breakdown**: Analysis by category
- **Comprehensive Report**: Actionable insights

## 🎯 Scoring System

| Score Range | Recommendation | Description |
|-------------|----------------|-------------|
| 85-100 | **Strong Hire** | Excellent candidate |
| 70-84 | **Hire** | Good candidate |
| 55-69 | **Maybe** | Average candidate |
| 0-54 | **No Hire** | Below average |

## 🔧 Troubleshooting

### **File Upload Issues**
- ✅ **Fixed**: Now uses standard HTML file input
- ✅ **Reliable**: Works on all browsers and devices
- ✅ **Clear feedback**: Progress indicators and success messages

### **Common Issues**

1. **Server won't start**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Check environment
   python3 test_file_upload.py
   ```

2. **OpenAI API Error**
   - Ensure `OPENAI_API_KEY` is set in `.env` file
   - Check API key validity and credits

3. **File parsing fails**
   - Supported formats: PDF, DOC, DOCX, TXT
   - Max file size: 10MB
   - Try with `sample_resume.txt` first

## 📁 Test Files

Use the included `sample_resume.txt` to test the system:
- Contains realistic resume data
- Includes social media profiles
- Tests all parsing features

## 🎨 UI Features

### **Modern File Upload**
- Styled file input with blue "Choose Files" button
- Real-time progress with animated spinner
- Success confirmation with green checkmark
- Optional drag-and-drop area (can be enabled)

### **Smart Data Extraction**
- AI-powered resume parsing
- Automatic job description analysis
- Social profile detection and categorization
- Manual override fields for corrections

### **Real-time Progress**
- WebSocket-based live updates
- Progress bars for each analysis step
- Status messages and completion indicators
- Professional progress tracking UI

## 🏗️ Architecture

- **Frontend**: Vanilla JavaScript + TailwindCSS (framework-agnostic)
- **Backend**: FastAPI + LangGraph for AI workflows
- **File Processing**: PyPDF2, python-docx, pdfplumber
- **AI Engine**: OpenAI GPT-4 with LangChain
- **Real-time**: WebSocket connections

## 📊 Analysis Pipeline

1. **Resume Parsing**: Extract structured data from uploaded file
2. **JD Analysis**: Parse job description and extract requirements
3. **Parallel Analysis**: Run multiple evaluations simultaneously:
   - GitHub repository analysis
   - LinkedIn profile evaluation
   - Twitter/X content analysis  
   - Medium article review
   - Live project assessment
   - Company research
4. **Final Scoring**: Weighted calculation with detailed report

The system is now **production-ready** with reliable file upload, comprehensive analysis, and professional UI! 🎉