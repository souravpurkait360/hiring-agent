# Hiring Agent Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
```bash
cp .env.example .env
```

Then edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Test Installation
```bash
python3 run_test.py
```

### 4. Start the Server
```bash
python3 start_server.py
```

or

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Open the Application
Navigate to: `http://localhost:8000`

## 📋 Features Demo

### Basic Usage
1. **Job Description**: Fill in the job title, company, requirements, and preferred skills
2. **Resume**: Add candidate details including social media profiles (GitHub, LinkedIn, etc.)
3. **Custom Weights**: Adjust the importance of different analysis factors
4. **Start Analysis**: Watch real-time progress as the AI analyzes the candidate
5. **View Results**: Get a comprehensive score and detailed report

### Advanced Features
- **Real-time Progress**: Live updates via WebSocket
- **Parallel Processing**: Multiple analysis agents run simultaneously
- **Customizable Scoring**: Adjust weights for different criteria
- **Comprehensive Analysis**: GitHub, LinkedIn, Twitter, Medium, projects, and company research

## 🔧 Configuration

### Scoring Weights (config/weights.yaml)
```yaml
default_weights:
  resume_jd_match: 0.25    # Resume-JD compatibility
  github_analysis: 0.20    # Code quality and projects
  linkedin_analysis: 0.10  # Professional content
  technical_blogs: 0.15    # Medium articles and expertise
  project_quality: 0.15    # Live projects assessment
  work_experience: 0.10    # Previous company difficulty
  social_presence: 0.05    # Overall social media presence
```

### API Keys (Optional for Enhanced Analysis)
- `GITHUB_TOKEN`: For detailed GitHub repository analysis
- `LINKEDIN_TOKEN`: For LinkedIn profile data
- `TWITTER_BEARER_TOKEN`: For Twitter/X content analysis
- `MEDIUM_TOKEN`: For Medium article analysis

## 🧪 Testing

### Basic Tests
```bash
python3 run_test.py
```

### Full Test Suite
```bash
pytest tests/
```

### Manual API Testing
```bash
# Health check
curl http://localhost:8000/api/health

# Start analysis
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d @sample_request.json
```

## 📁 Project Structure

```
hiring-agent/
├── app/                    # Backend application
│   ├── agents/            # LangGraph workflow
│   ├── api/               # WebSocket management
│   ├── models/            # Pydantic schemas
│   ├── services/          # Platform analysis
│   └── utils/             # Utilities
├── config/                # Configuration files
├── frontend/              # Web interface
├── tests/                 # Test files
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── run_test.py           # Test script
└── start_server.py       # Startup script
```

## 🔍 Analysis Process

1. **Resume-JD Matching** (Sequential)
   - AI-powered compatibility analysis
   - Skills and experience matching
   - Domain relevance assessment

2. **Platform Analysis** (Parallel)
   - **GitHub**: Code quality, project complexity, contribution patterns
   - **LinkedIn**: Technical posts, professional network, endorsements
   - **Twitter**: Technical discussions, engagement quality
   - **Medium**: Technical articles, domain expertise
   - **Projects**: Live site analysis (performance, SEO, responsiveness)
   - **Companies**: Previous work experience difficulty scoring

3. **Final Scoring** (Sequential)
   - Weighted score calculation
   - Recommendation generation
   - Detailed report compilation

## 📊 Scoring System

### Score Ranges
- **85-100**: Strong Hire (Excellent candidate)
- **70-84**: Hire (Good candidate)
- **55-69**: Maybe (Average candidate)
- **0-54**: No Hire (Below average)

### Customization
Modify `config/weights.yaml` to adjust scoring priorities based on your hiring criteria.

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI API Error**
   - Ensure `OPENAI_API_KEY` is set in `.env`
   - Check API key validity and credits

2. **Dependencies Issues**
   - Use Python 3.9+
   - Install with: `pip install -r requirements.txt`

3. **Server Won't Start**
   - Check port 8000 is available
   - Verify all dependencies are installed
   - Run `python3 run_test.py` first

4. **WebSocket Connection Failed**
   - Ensure server is running
   - Check browser console for errors
   - Try refreshing the page

### Getting Help
- Check the logs for detailed error messages
- Run the test script to verify setup
- Ensure all required environment variables are set

## 🔄 Development

### Adding New Analysis Agents
1. Create service in `app/services/`
2. Add node function in `app/agents/nodes.py`
3. Update workflow in `app/agents/graph.py`
4. Add progress tracking in frontend

### Frontend Customization
The frontend uses vanilla JavaScript and TailwindCSS, making it easy to:
- Migrate to React/Vue/Angular
- Customize styling and layout
- Add new features and components

### API Extensions
- Add new endpoints in `app/main.py`
- Create new Pydantic models in `app/models/schemas.py`
- Implement business logic in `app/services/`

## 📈 Production Deployment

### Recommended Setup
- Use a production WSGI server (Gunicorn)
- Set up reverse proxy (Nginx)
- Configure SSL certificates
- Use environment-specific configurations
- Implement proper logging and monitoring

### Environment Variables
```bash
OPENAI_API_KEY=your_production_key
GITHUB_TOKEN=your_github_token
LINKEDIN_TOKEN=your_linkedin_token
TWITTER_BEARER_TOKEN=your_twitter_token
MEDIUM_TOKEN=your_medium_token
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 License

This project is created for demonstration purposes. Please ensure you comply with the terms of service of all APIs used (OpenAI, GitHub, LinkedIn, Twitter, Medium).