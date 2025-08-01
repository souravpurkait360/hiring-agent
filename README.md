# Hiring Agent 🤖

An AI-powered hiring agent that analyzes job descriptions and resumes, then performs comprehensive candidate evaluation across multiple platforms with **real-time progress tracking**.

## ✨ Features

### Core Analysis
- **Smart Resume Parsing**: Drag-and-drop file upload (PDF, DOC, DOCX, TXT) with AI-powered data extraction
- **Free-form Job Description**: Simply paste the entire job posting - AI extracts all relevant details
- **Resume-JD Matching**: AI-powered compatibility analysis with detailed scoring

### Multi-Platform Evaluation (Parallel Processing)
- 🔧 **GitHub Analysis**: Code quality, project complexity, contribution patterns
- 💼 **LinkedIn Analysis**: Technical content, professional network, endorsements  
- 🐦 **Twitter/X Analysis**: Technical discussions, engagement quality
- 📝 **Medium Analysis**: Technical articles, domain expertise
- 🚀 **Live Project Evaluation**: Performance, SEO, responsiveness analysis
- 🏢 **Company Research**: Previous work experience difficulty scoring

### Advanced Features
- 📊 **Real-time Progress**: Live WebSocket updates with progress bars
- ⚙️ **Customizable Weights**: Adjust importance of different analysis factors
- 📈 **Comprehensive Scoring**: 0-100 scale with hire/no-hire recommendations
- 📋 **Detailed Reports**: In-depth analysis with actionable insights

## 🛠️ Tech Stack

- **Backend**: FastAPI, LangGraph, Pydantic
- **Frontend**: HTML, TailwindCSS, Vanilla JavaScript (framework-agnostic)
- **AI Engine**: OpenAI GPT-4 with LangChain
- **Real-time**: WebSockets for live updates
- **File Processing**: PyPDF2, python-docx, pdfplumber

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Add your OPENAI_API_KEY
   ```

3. **Test installation:**
   ```bash
   python3 run_test.py
   ```

4. **Start the application:**
   ```bash
   python3 start_server.py
   ```
   or
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Open in browser:**
   ```
   http://localhost:8000
   ```

## 📋 How to Use

### 1. Job Description
- Paste the complete job posting in the large text area
- AI automatically extracts: title, company, requirements, skills, experience level, domain

### 2. Resume Upload
- **Drag & drop** or click to upload resume (PDF, DOC, DOCX, TXT)
- AI extracts: name, email, skills, experience, education, projects, social profiles
- Review and manually correct any extracted information if needed

### 3. Customize Analysis (Optional)
- Adjust scoring weights using sliders
- Default weights favor technical skills and code quality

### 4. Start Analysis
- Click "Start Analysis" to begin comprehensive evaluation
- Watch **real-time progress** with live updates for each analysis step

### 5. Review Results
- Get overall score (0-100) with hire recommendation
- Review detailed breakdown by analysis category
- Access comprehensive report with actionable insights

## Project Structure

```
hiring-agent/
├── app/                    # Backend FastAPI application
│   ├── agents/            # LangGraph agents
│   ├── api/               # API endpoints
│   ├── models/            # Pydantic models
│   ├── services/          # Business logic
│   └── utils/             # Utilities
├── config/                # Configuration files
├── frontend/              # Frontend application
├── tests/                 # Test files
└── requirements.txt       # Python dependencies
```