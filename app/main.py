import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import uuid
import json
from datetime import datetime
from typing import Dict, List
import asyncio

from app.models.schemas import AnalysisRequest, AnalysisResponse, AnalysisStatus
from app.agents.graph import orchestrator
from app.api.websocket_manager import manager

app = FastAPI(title="Hiring Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve individual frontend files directly
@app.get("/app.js")
async def get_app_js():
    return FileResponse("frontend/app.js")

@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")

@app.post("/api/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest):
    analysis_id = str(uuid.uuid4())
    
    response = AnalysisResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.PENDING,
        progress=[]
    )
    
    async def progress_callback(analysis_id: str, state: Dict):
        await manager.send_progress_update(analysis_id, state)
    
    asyncio.create_task(
        orchestrator.start_analysis(
            analysis_id=analysis_id,
            resume=request.resume,
            job_description=request.job_description,
            custom_weights=request.custom_weights,
            progress_callback=progress_callback
        )
    )
    
    return response

@app.get("/api/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_status(analysis_id: str):
    state = orchestrator.get_analysis_progress(analysis_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    status = AnalysisStatus.COMPLETED if state.get("final_analysis") else AnalysisStatus.IN_PROGRESS
    
    return AnalysisResponse(
        analysis_id=analysis_id,
        status=status,
        progress=state.get("progress", []),
        result=state.get("final_analysis"),
        error_message="; ".join(state.get("errors", []))
    )

@app.websocket("/ws/{analysis_id}")
async def websocket_endpoint(websocket: WebSocket, analysis_id: str):
    await manager.connect(websocket, analysis_id)
    try:
        while True:
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, analysis_id)

@app.post("/api/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    """Parse uploaded resume file and extract text content"""
    try:
        # Read file content
        content = await file.read()
        
        # Parse based on file type
        if file.filename.lower().endswith('.pdf'):
            from app.utils.resume_parser import parse_pdf_resume
            resume_text = parse_pdf_resume(content)
        elif file.filename.lower().endswith(('.doc', '.docx')):
            from app.utils.resume_parser import parse_docx_resume
            resume_text = parse_docx_resume(content)
        elif file.filename.lower().endswith('.txt'):
            resume_text = content.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOC, DOCX, or TXT files.")
        
        # Extract structured data from resume text using AI
        from app.utils.resume_parser import extract_resume_data
        structured_data = await extract_resume_data(resume_text)
        
        return {
            "filename": file.filename,
            "raw_text": resume_text,
            "structured_data": structured_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)