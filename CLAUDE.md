# Hiring Agent - Claude Code Context

This is an AI-powered hiring agent that analyzes job descriptions and resumes, then performs comprehensive candidate evaluation across multiple platforms.

## Project Overview

The Hiring Agent is a sophisticated system that:
- Matches resumes against job descriptions
- Analyzes candidates' GitHub repositories for code quality and relevance
- Evaluates LinkedIn profiles for professional content
- Reviews Twitter/X accounts for technical discussions
- Analyzes Medium articles for domain expertise
- Evaluates live projects for technical quality
- Researches previous work experience and company difficulty
- Provides real-time progress updates via WebSocket
- Offers customizable scoring weights

## Architecture

### Backend (FastAPI + LangGraph)
- **app/main.py**: Main FastAPI application with API endpoints
- **app/agents/graph.py**: LangGraph workflow orchestration
- **app/agents/nodes.py**: Individual analysis agents/nodes
- **app/models/schemas.py**: Pydantic data models
- **app/services/**: Analysis services for each platform
- **app/api/websocket_manager.py**: WebSocket connection management
- **config/**: Configuration files including customizable weights

### Frontend (Vanilla JS + TailwindCSS)
- **frontend/index.html**: Main UI with form and progress tracking
- **frontend/app.js**: JavaScript application logic and WebSocket handling

## Key Features

1. **Parallel Processing**: Multiple agents run concurrently for faster analysis
2. **Real-time Updates**: WebSocket-based progress tracking with live checkboxes
3. **Customizable Weights**: YAML-based configuration for scoring weights
4. **Comprehensive Analysis**: 8 different analysis dimensions
5. **Production-Ready**: Proper error handling, logging, and structure

## API Endpoints

- `POST /api/analyze`: Start new candidate analysis
- `GET /api/analysis/{id}`: Get analysis status and results
- `WebSocket /ws/{id}`: Real-time progress updates
- `GET /api/health`: Health check endpoint

## Environment Variables

Required:
- `OPENAI_API_KEY`: OpenAI API key for LLM analysis

Optional (for enhanced analysis):
- `GITHUB_TOKEN`: GitHub API token
- `LINKEDIN_TOKEN`: LinkedIn API token  
- `TWITTER_BEARER_TOKEN`: Twitter API bearer token
- `MEDIUM_TOKEN`: Medium API token

## Development Workflow

1. **Setup**: Install dependencies with `pip install -r requirements.txt`
2. **Configuration**: Copy `.env.example` to `.env` and add API keys
3. **Testing**: Run `python run_test.py` to verify setup
4. **Development**: Start with `uvicorn app.main:app --reload`
5. **Frontend**: Access at `http://localhost:8000`

## Key Components

### LangGraph Workflow
The analysis follows a directed graph:
1. Resume-JD matching (sequential)
2. Platform analyses (parallel): GitHub, LinkedIn, Twitter, Medium, Projects, Companies
3. Final scoring (sequential)

### Scoring System
- Resume-JD Match: 25% (default)
- GitHub Analysis: 20% (default)
- LinkedIn Analysis: 10% (default)
- Technical Blogs: 15% (default)
- Project Quality: 15% (default)
- Work Experience: 10% (default)
- Social Presence: 5% (default)

### Real-time Progress
WebSocket updates provide:
- Task status (pending/in_progress/completed/failed)
- Progress percentages
- Status messages
- Final analysis results

## Testing

- **run_test.py**: Comprehensive test script
- **tests/test_integration.py**: Pytest integration tests
- Tests cover: environment setup, models, OpenAI connection, basic workflow

## Deployment Considerations

- Frontend can be easily migrated to React/Vue/Angular
- Backend is stateless and horizontally scalable
- WebSocket connections are managed per analysis
- Configuration is externalized for environment-specific settings

## Customization

- **Weights**: Modify `config/weights.yaml`
- **Scoring Thresholds**: Adjust in weights configuration
- **Platform Analysis**: Extend services in `app/services/`
- **UI**: Customize frontend styling and layout

This system provides a comprehensive, production-ready solution for AI-powered candidate evaluation with real-time feedback and extensive customization options.