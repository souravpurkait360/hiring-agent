from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class Platform(str, Enum):
    GITHUB = "github"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    MEDIUM = "medium"
    PERSONAL_WEBSITE = "personal_website"
    OTHER = "other"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskProgress(BaseModel):
    task_id: str
    task_name: str
    status: AnalysisStatus
    progress_percentage: float = 0.0
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class SocialProfile(BaseModel):
    platform: Platform
    url: HttpUrl
    username: Optional[str] = None

class JobDescription(BaseModel):
    title: str
    company: str
    description: str
    requirements: List[str]
    preferred_skills: List[str]
    experience_level: str
    domain: str

class Resume(BaseModel):
    candidate_name: str
    email: str
    phone: Optional[str] = None
    experience_years: Optional[int] = None
    skills: List[str]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    social_profiles: List[SocialProfile] = []
    raw_text: str

class GitHubAnalysis(BaseModel):
    username: str
    public_repos_count: int
    followers: int
    following: int
    total_commits: int
    repositories: List[Dict[str, Any]]
    languages: Dict[str, int]
    contribution_streak: int
    code_quality_score: float
    project_complexity_score: float
    domain_relevance_score: float

class LinkedInAnalysis(BaseModel):
    profile_url: str
    technical_posts_count: int
    domain_relevant_posts: int
    connections: Optional[int] = None
    endorsements: List[str] = []
    certifications: List[str] = []
    domain_relevance_score: float

class TwitterAnalysis(BaseModel):
    username: str
    followers: int
    technical_tweets_count: int
    domain_relevant_tweets: int
    engagement_rate: float
    domain_relevance_score: float

class MediumAnalysis(BaseModel):
    username: str
    articles_count: int
    domain_relevant_articles: int
    total_claps: int
    followers: int
    domain_relevance_score: float

class ProjectAnalysis(BaseModel):
    project_name: str
    is_live: bool
    url: Optional[HttpUrl] = None
    technologies: List[str]
    complexity_score: float
    responsiveness_score: float
    seo_score: float
    performance_score: float
    error_count: int

class CompanyAnalysis(BaseModel):
    company_name: str
    role: str
    difficulty_score: float
    company_tier: str
    market_reputation: float

class CandidateAnalysis(BaseModel):
    resume: Resume
    job_description: JobDescription
    resume_jd_match_score: float
    github_analysis: Optional[GitHubAnalysis] = None
    linkedin_analysis: Optional[LinkedInAnalysis] = None
    twitter_analysis: Optional[TwitterAnalysis] = None
    medium_analysis: Optional[MediumAnalysis] = None
    project_analyses: List[ProjectAnalysis] = []
    company_analyses: List[CompanyAnalysis] = []
    overall_score: float
    recommendation: str
    detailed_report: str
    analysis_timestamp: datetime = Field(default_factory=datetime.now)

class AnalysisRequest(BaseModel):
    job_description: JobDescription
    resume: Resume
    custom_weights: Optional[Dict[str, float]] = None

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    progress: List[TaskProgress]
    result: Optional[CandidateAnalysis] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)