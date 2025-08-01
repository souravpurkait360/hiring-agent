import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.responses import Response
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
            weight_mode=request.weight_mode,
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

@app.get("/api/weights")
async def get_weights():
    """Get current weight configuration from config/weights.yaml"""
    try:
        from config.settings import settings
        return {
            "weight_modes": settings.get_weight_modes(),
            "default_mode": settings.get_default_mode(),
            "platform_weights": settings.weights_config.get("platform_weights", {}),
            "scoring_thresholds": settings.get_scoring_thresholds()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading weights: {str(e)}")

@app.get("/api/weights/modes")
async def get_weight_modes():
    """Get available weight modes"""
    try:
        from config.settings import settings
        return {
            "modes": settings.get_weight_modes(),
            "default_mode": settings.get_default_mode()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading weight modes: {str(e)}")

@app.get("/api/weights/mode/{mode}")
async def get_weight_mode(mode: str):
    """Get weights for a specific mode"""
    try:
        from config.settings import settings
        mode_info = settings.get_weight_mode_info(mode)
        if not mode_info:
            raise HTTPException(status_code=404, detail=f"Weight mode '{mode}' not found")
        return mode_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading weight mode: {str(e)}")

@app.get("/api/analysis/{analysis_id}/stream")
async def stream_final_analysis(analysis_id: str):
    """Stream final analysis results using Server-Sent Events"""
    
    async def generate_sse_stream():
        """Generate SSE stream for final analysis"""
        try:
            import asyncio
            
            # Wait for analysis to complete with timeout
            max_wait_time = 300  # 5 minutes
            wait_interval = 2    # Check every 2 seconds
            waited_time = 0
            
            analysis_state = None
            
            # Send initial message
            yield f"data: {json.dumps({'type': 'message', 'content': 'Starting analysis connection...', 'is_complete': False})}\n\n"
            
            while waited_time < max_wait_time:
                analysis_state = orchestrator.get_analysis_progress(analysis_id)
                
                if not analysis_state:
                    if waited_time > 30:  # Wait at least 30 seconds for analysis to start
                        yield f"data: {json.dumps({'error': 'Analysis not found or failed to start'})}\n\n"
                        return
                    # Send progress updates while waiting for analysis to start
                    if waited_time % 10 == 0:  # Every 10 seconds
                        yield f"data: {json.dumps({'type': 'message', 'content': f'Waiting for analysis to start... ({waited_time}s)', 'is_complete': False})}\n\n"
                else:
                    # Analysis exists, check for completion
                    if analysis_state.get('final_analysis'):
                        # Analysis is complete, break out of waiting loop
                        break
                        
                    # Check if analysis has at least some progress
                    progress_tasks = analysis_state.get('progress', [])
                    completed_tasks = [t for t in progress_tasks if hasattr(t, 'status') and t.status.value == 'completed']
                    final_task_completed = any(t.task_id == 'final_score' and t.status.value == 'completed' for t in progress_tasks)
                    
                    
                    if final_task_completed or len(completed_tasks) >= 7:  # All tasks including final score completed
                        break
                    
                    # Send progress updates while waiting for completion
                    if waited_time % 10 == 0:  # Every 10 seconds
                        yield f"data: {json.dumps({'type': 'message', 'content': f'Analysis in progress... ({len(completed_tasks)}/7 tasks completed)', 'is_complete': False})}\n\n"
                
                await asyncio.sleep(wait_interval)
                waited_time += wait_interval
            
            if not analysis_state:
                yield f"data: {json.dumps({'error': 'Analysis timed out or not found'})}\n\n"
                return
                
                
            # Stream the analysis using a simplified approach
            
            final_analysis = analysis_state.get('final_analysis')
            if final_analysis and hasattr(final_analysis, 'detailed_report'):
                # Send the detailed report in chunks with proper timing
                detailed_report = final_analysis.detailed_report
                
                # Split report into meaningful sections for streaming effect
                sections = detailed_report.split('\n\n')
                
                for i, section in enumerate(sections):
                    if section.strip():
                        content = section + '\n\n'
                        is_final = (i == len(sections) - 1)
                        yield f"data: {json.dumps({'type': 'message', 'content': content, 'is_complete': is_final})}\n\n"
                        if not is_final:
                            await asyncio.sleep(0.5)  # Appropriate delay for streaming effect
                
            else:
                # Fallback - create basic report
                candidate_name = getattr(analysis_state.get('resume'), 'candidate_name', 'Unknown')
                job_title = getattr(analysis_state.get('job_description'), 'title', 'Unknown Position')
                overall_score = getattr(final_analysis, 'overall_score', 0) if final_analysis else 0
                recommendation = getattr(final_analysis, 'recommendation', 'Unknown') if final_analysis else 'Unknown'
                
                simple_report = f"""# Analysis Report

## Candidate: {candidate_name}
## Position: {job_title}

### Final Results
- **Overall Score:** {overall_score:.1f}/100
- **Recommendation:** {recommendation}

### Summary
Analysis completed successfully. Detailed breakdown available in the progress tracking above.
"""
                
                yield f"data: {json.dumps({'type': 'message', 'content': simple_report, 'is_complete': True})}\n\n"
            
                
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Streaming error: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)