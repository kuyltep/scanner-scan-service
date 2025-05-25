#!/usr/bin/env python3
"""
VulnApk Service API
FastAPI wrapper for integrating VulnApk scanner into existing services
"""

import asyncio
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
import shutil
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import VulnApk components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vulnapk'))

from vulnapk.main import VulnApk
import vulnapk.logger as vulnapk_logger


# Pydantic Models
class AnalysisRequest(BaseModel):
    """Request model for APK analysis"""
    apk_url: Optional[str] = Field(None, description="URL to download APK from")
    package_name: Optional[str] = Field(None, description="Android package name to download")
    included_plugins: Optional[List[str]] = Field(None, description="Specific plugins to run")
    excluded_plugins: Optional[List[str]] = Field(None, description="Plugins to exclude")
    priority: str = Field("normal", description="Analysis priority: low, normal, high")


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    analysis_id: str
    status: str  # pending, running, completed, failed
    apk_info: Optional[Dict] = None
    total_issues: int = 0
    issues: List[Dict] = []
    plugins_used: List[str] = []
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class AnalysisStatus(BaseModel):
    """Status model for analysis tracking"""
    analysis_id: str
    status: str
    progress: int = 0  # 0-100
    message: str = ""


# Global storage for analysis results (use Redis/DB in production)
analysis_results: Dict[str, AnalysisResponse] = {}
analysis_status: Dict[str, AnalysisStatus] = {}


# FastAPI App
app = FastAPI(
    title="VulnApk Security Scanner API",
    description="REST API for Android APK security analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Initialize logging
vulnapk_logger.init(logging.INFO)
logger = logging.getLogger(__name__)


class VulnApkService:
    """Service class for VulnApk operations"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "vulnapk_service"
        self.temp_dir.mkdir(exist_ok=True)
        self.reports_dir = self.temp_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    async def analyze_apk_file(
        self, 
        apk_file: Path, 
        analysis_id: str,
        included_plugins: Optional[List[str]] = None,
        excluded_plugins: Optional[List[str]] = None
    ) -> AnalysisResponse:
        """Analyze APK file and return results"""
        
        try:
            # Update status
            analysis_status[analysis_id].status = "running"
            analysis_status[analysis_id].progress = 10
            analysis_status[analysis_id].message = "Initializing analysis..."
            
            # Create VulnApk instance
            vulnapk = VulnApk(
                files=[str(apk_file)],
                included_plugins=included_plugins,
                excluded_plugins=excluded_plugins,
                output_reports=str(self.reports_dir / analysis_id)
            )
            
            analysis_status[analysis_id].progress = 30
            analysis_status[analysis_id].message = "Running security plugins..."
            
            # Run analysis
            results = vulnapk.start()
            
            analysis_status[analysis_id].progress = 90
            analysis_status[analysis_id].message = "Finalizing results..."
            
            # Create response
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                apk_info={"file_path": str(apk_file)},
                total_issues=len(results),
                issues=results,
                plugins_used=[p.__class__.__module__ for p in vulnapk.plugins],
                created_at=analysis_results[analysis_id].created_at,
                completed_at=datetime.now()
            )
            
            analysis_status[analysis_id].status = "completed"
            analysis_status[analysis_id].progress = 100
            analysis_status[analysis_id].message = "Analysis completed"
            
            return response
            
        except Exception as e:
            logger.error(f"Analysis failed for {analysis_id}: {str(e)}")
            
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="failed",
                created_at=analysis_results[analysis_id].created_at,
                completed_at=datetime.now(),
                error_message=str(e)
            )
            
            analysis_status[analysis_id].status = "failed"
            analysis_status[analysis_id].message = f"Analysis failed: {str(e)}"
            
            return response
    
    async def analyze_package(
        self,
        package_name: str,
        analysis_id: str,
        included_plugins: Optional[List[str]] = None,
        excluded_plugins: Optional[List[str]] = None
    ) -> AnalysisResponse:
        """Download and analyze APK by package name"""
        
        try:
            analysis_status[analysis_id].status = "running"
            analysis_status[analysis_id].progress = 10
            analysis_status[analysis_id].message = "Downloading APK..."
            
            vulnapk = VulnApk(
                packages=[package_name],
                included_plugins=included_plugins,
                excluded_plugins=excluded_plugins,
                output_reports=str(self.reports_dir / analysis_id)
            )
            
            analysis_status[analysis_id].progress = 50
            analysis_status[analysis_id].message = "Running security analysis..."
            
            results = vulnapk.start()
            
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                apk_info={"package_name": package_name},
                total_issues=len(results),
                issues=results,
                plugins_used=[p.__class__.__module__ for p in vulnapk.plugins],
                created_at=analysis_results[analysis_id].created_at,
                completed_at=datetime.now()
            )
            
            analysis_status[analysis_id].status = "completed"
            analysis_status[analysis_id].progress = 100
            
            return response
            
        except Exception as e:
            logger.error(f"Package analysis failed for {analysis_id}: {str(e)}")
            
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="failed",
                created_at=analysis_results[analysis_id].created_at,
                completed_at=datetime.now(),
                error_message=str(e)
            )
            
            analysis_status[analysis_id].status = "failed"
            analysis_status[analysis_id].message = f"Analysis failed: {str(e)}"
            
            return response


# Service instance
vulnapk_service = VulnApkService()


# Background task for analysis
async def run_analysis_task(
    analysis_id: str,
    apk_file: Optional[Path] = None,
    package_name: Optional[str] = None,
    included_plugins: Optional[List[str]] = None,
    excluded_plugins: Optional[List[str]] = None
):
    """Background task to run APK analysis"""
    
    try:
        if apk_file:
            result = await vulnapk_service.analyze_apk_file(
                apk_file, analysis_id, included_plugins, excluded_plugins
            )
        elif package_name:
            result = await vulnapk_service.analyze_package(
                package_name, analysis_id, included_plugins, excluded_plugins
            )
        else:
            raise ValueError("Either apk_file or package_name must be provided")
        
        analysis_results[analysis_id] = result
        
    except Exception as e:
        logger.error(f"Background analysis failed: {str(e)}")
        analysis_results[analysis_id].status = "failed"
        analysis_results[analysis_id].error_message = str(e)


# API Endpoints
@app.post("/analyze/upload", response_model=Dict[str, str])
async def analyze_uploaded_apk(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    included_plugins: Optional[str] = None,
    excluded_plugins: Optional[str] = None
):
    """Upload and analyze APK file"""
    
    # Validate file
    if not file.filename.endswith('.apk'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an APK file"
        )
    
    # Generate analysis ID
    analysis_id = str(uuid.uuid4())
    
    # Save uploaded file
    apk_path = vulnapk_service.temp_dir / f"{analysis_id}.apk"
    with open(apk_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Parse plugin lists
    included_list = included_plugins.split(',') if included_plugins else None
    excluded_list = excluded_plugins.split(',') if excluded_plugins else None
    
    # Initialize analysis record
    analysis_results[analysis_id] = AnalysisResponse(
        analysis_id=analysis_id,
        status="pending",
        created_at=datetime.now()
    )
    
    analysis_status[analysis_id] = AnalysisStatus(
        analysis_id=analysis_id,
        status="pending",
        message="Analysis queued"
    )
    
    # Start background analysis
    background_tasks.add_task(
        run_analysis_task,
        analysis_id=analysis_id,
        apk_file=apk_path,
        included_plugins=included_list,
        excluded_plugins=excluded_list
    )
    
    return {"analysis_id": analysis_id, "status": "pending"}


@app.post("/analyze/package", response_model=Dict[str, str])
async def analyze_package_name(
    background_tasks: BackgroundTasks,
    request: AnalysisRequest
):
    """Analyze APK by package name"""
    
    if not request.package_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="package_name is required"
        )
    
    analysis_id = str(uuid.uuid4())
    
    # Initialize analysis record
    analysis_results[analysis_id] = AnalysisResponse(
        analysis_id=analysis_id,
        status="pending",
        created_at=datetime.now()
    )
    
    analysis_status[analysis_id] = AnalysisStatus(
        analysis_id=analysis_id,
        status="pending",
        message="Analysis queued"
    )
    
    # Start background analysis
    background_tasks.add_task(
        run_analysis_task,
        analysis_id=analysis_id,
        package_name=request.package_name,
        included_plugins=request.included_plugins,
        excluded_plugins=request.excluded_plugins
    )
    
    return {"analysis_id": analysis_id, "status": "pending"}


@app.get("/analyze/{analysis_id}/status", response_model=AnalysisStatus)
async def get_analysis_status(analysis_id: str):
    """Get analysis status"""
    
    if analysis_id not in analysis_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return analysis_status[analysis_id]


@app.get("/analyze/{analysis_id}/results", response_model=AnalysisResponse)
async def get_analysis_results(analysis_id: str):
    """Get analysis results"""
    
    if analysis_id not in analysis_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    result = analysis_results[analysis_id]
    
    if result.status == "pending" or result.status == "running":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Analysis still in progress"
        )
    
    return result


@app.get("/analyze", response_model=List[AnalysisResponse])
async def list_analyses(limit: int = 10, offset: int = 0):
    """List all analyses"""
    
    all_results = list(analysis_results.values())
    return all_results[offset:offset + limit]


@app.delete("/analyze/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete analysis results"""
    
    if analysis_id not in analysis_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    # Clean up files
    apk_path = vulnapk_service.temp_dir / f"{analysis_id}.apk"
    if apk_path.exists():
        apk_path.unlink()
    
    report_dir = vulnapk_service.reports_dir / analysis_id
    if report_dir.exists():
        shutil.rmtree(report_dir)
    
    # Remove from memory
    del analysis_results[analysis_id]
    if analysis_id in analysis_status:
        del analysis_status[analysis_id]
    
    return {"message": "Analysis deleted successfully"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vulnapk-api"}


@app.get("/plugins")
async def list_plugins():
    """List available security plugins"""
    
    try:
        # Create temporary VulnApk instance to get plugins
        temp_vulnapk = VulnApk(files=["dummy.apk"])
    except:
        pass
    
    # Read plugins from directory
    plugins_dir = Path(__file__).parent / "vulnapk" / "plugins"
    available_plugins = []
    
    if plugins_dir.exists():
        for plugin_file in plugins_dir.glob("*.py"):
            if plugin_file.name != "base_plugin.py":
                available_plugins.append(plugin_file.stem)
    
    return {"available_plugins": available_plugins}


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "vulnapk_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 