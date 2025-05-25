#!/usr/bin/env python3
"""
VulnApk Integration Examples
Comprehensive examples showing different ways to integrate VulnApk into existing services
"""

import asyncio
import os
import sys
from typing import Dict, List, Any
import logging
import requests
import json

# Add VulnApk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vulnapk'))

from vulnapk_client import VulnApkClient, quick_analyze, quick_analyze_async


# ============================================================================
# Example 1: Direct Integration into Existing Service
# ============================================================================

class MyExistingService:
    """Example of integrating VulnApk directly into an existing service"""
    
    def __init__(self):
        self.vulnapk_client = VulnApkClient(
            temp_dir="/tmp/my_service_vulnapk",
            log_level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)
    
    def process_uploaded_apk(self, apk_file_path: str, user_id: str) -> Dict[str, Any]:
        """Process an uploaded APK file with security analysis"""
        
        try:
            # Your existing business logic
            self.logger.info(f"Processing APK upload for user {user_id}")
            
            # Run security analysis
            analysis_result = self.vulnapk_client.analyze_apk(
                apk_path=apk_file_path,
                included_plugins=["hardcode_secrets", "unsafe_crypto"]
            )
            
            # Integrate results into your business logic
            if analysis_result['success']:
                security_score = self._calculate_security_score(analysis_result)
                
                # Store results in your database
                self._store_analysis_results(user_id, apk_file_path, analysis_result)
                
                # Send notifications if critical issues found
                if self._has_critical_issues(analysis_result):
                    self._send_security_alert(user_id, analysis_result)
                
                return {
                    'status': 'success',
                    'security_score': security_score,
                    'issues_found': analysis_result['total_issues'],
                    'analysis_id': f"analysis_{user_id}_{int(time.time())}"
                }
            else:
                self.logger.error(f"Analysis failed: {analysis_result['error']}")
                return {
                    'status': 'error',
                    'message': 'Security analysis failed'
                }
                
        except Exception as e:
            self.logger.error(f"APK processing failed: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _calculate_security_score(self, analysis_result: Dict[str, Any]) -> int:
        """Calculate security score based on analysis results"""
        base_score = 100
        issues = analysis_result.get('issues', [])
        
        for issue in issues:
            severity = issue.get('severity', 'LOW')
            if severity == 'CRITICAL':
                base_score -= 25
            elif severity == 'HIGH':
                base_score -= 15
            elif severity == 'MEDIUM':
                base_score -= 10
            elif severity == 'LOW':
                base_score -= 5
        
        return max(0, base_score)
    
    def _has_critical_issues(self, analysis_result: Dict[str, Any]) -> bool:
        """Check if analysis found critical security issues"""
        issues = analysis_result.get('issues', [])
        return any(issue.get('severity') == 'CRITICAL' for issue in issues)
    
    def _store_analysis_results(self, user_id: str, apk_path: str, results: Dict[str, Any]):
        """Store analysis results in database (mock implementation)"""
        # Your database storage logic here
        self.logger.info(f"Stored analysis results for user {user_id}")
    
    def _send_security_alert(self, user_id: str, results: Dict[str, Any]):
        """Send security alert to user (mock implementation)"""
        # Your notification logic here
        self.logger.warning(f"Sent security alert to user {user_id}")


# ============================================================================
# Example 2: Async Integration with FastAPI
# ============================================================================

from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="My Service with VulnApk Integration")

class AnalysisResult(BaseModel):
    analysis_id: str
    status: str
    security_score: int = 0
    issues_count: int = 0

# Global VulnApk client
vulnapk_client = VulnApkClient()

@app.post("/upload-apk", response_model=AnalysisResult)
async def upload_and_analyze_apk(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload APK and run security analysis in background"""
    
    # Save uploaded file
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Generate analysis ID
    import uuid
    analysis_id = str(uuid.uuid4())
    
    # Start background analysis
    background_tasks.add_task(
        run_background_analysis,
        analysis_id=analysis_id,
        apk_path=file_path
    )
    
    return AnalysisResult(
        analysis_id=analysis_id,
        status="pending"
    )

async def run_background_analysis(analysis_id: str, apk_path: str):
    """Background task for APK analysis"""
    
    try:
        # Run async analysis
        result = await vulnapk_client.analyze_apk_async(apk_path)
        
        # Process results
        if result['success']:
            # Store in database, send notifications, etc.
            print(f"Analysis {analysis_id} completed: {result['total_issues']} issues found")
        else:
            print(f"Analysis {analysis_id} failed: {result['error']}")
            
    except Exception as e:
        print(f"Background analysis failed: {str(e)}")


# ============================================================================
# Example 3: HTTP Client Integration (Microservice Architecture)
# ============================================================================

class VulnApkHttpClient:
    """HTTP client for VulnApk service integration"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def analyze_apk_file(self, apk_file_path: str, plugins: List[str] = None) -> Dict[str, Any]:
        """Upload and analyze APK via HTTP API"""
        
        url = f"{self.base_url}/analyze/upload"
        
        with open(apk_file_path, 'rb') as f:
            files = {'file': f}
            data = {}
            
            if plugins:
                data['included_plugins'] = ','.join(plugins)
            
            response = self.session.post(url, files=files, data=data)
            response.raise_for_status()
            
            return response.json()
    
    def get_analysis_status(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis status"""
        
        url = f"{self.base_url}/analyze/{analysis_id}/status"
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis results"""
        
        url = f"{self.base_url}/analyze/{analysis_id}/results"
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def wait_for_analysis(self, analysis_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for analysis to complete and return results"""
        
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_analysis_status(analysis_id)
            
            if status['status'] == 'completed':
                return self.get_analysis_results(analysis_id)
            elif status['status'] == 'failed':
                raise Exception(f"Analysis failed: {status.get('message', 'Unknown error')}")
            
            time.sleep(5)  # Poll every 5 seconds
        
        raise TimeoutError(f"Analysis {analysis_id} did not complete within {timeout} seconds")


# ============================================================================
# Example 4: Batch Processing Integration
# ============================================================================

class BatchAPKProcessor:
    """Batch processor for multiple APK files"""
    
    def __init__(self):
        self.vulnapk_client = VulnApkClient()
        self.logger = logging.getLogger(__name__)
    
    def process_apk_directory(self, directory_path: str) -> Dict[str, Any]:
        """Process all APK files in a directory"""
        
        self.logger.info(f"Starting batch processing of directory: {directory_path}")
        
        # Analyze all APKs in directory
        results = self.vulnapk_client.analyze_directory(
            directory_path=directory_path,
            included_plugins=["hardcode_secrets", "unsafe_crypto", "sharedprefs"]
        )
        
        # Generate summary report
        summary = self._generate_batch_summary(results)
        
        # Export results
        self._export_batch_results(results, summary)
        
        return summary
    
    async def process_apk_directory_async(self, directory_path: str) -> Dict[str, Any]:
        """Process APK directory asynchronously"""
        
        # Find all APK files
        apk_files = []
        for file in os.listdir(directory_path):
            if file.endswith('.apk'):
                apk_files.append(os.path.join(directory_path, file))
        
        # Run parallel analysis
        results = await self.vulnapk_client.analyze_multiple_apks_async(apk_files)
        
        # Process results
        summary = self._generate_batch_summary(results)
        return summary
    
    def _generate_batch_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary from batch results"""
        
        total_apks = len(results)
        successful_analyses = sum(1 for r in results if r.get('success', False))
        total_issues = sum(r.get('total_issues', 0) for r in results if r.get('success', False))
        
        # Categorize issues by severity
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for result in results:
            if result.get('success', False):
                for issue in result.get('issues', []):
                    severity = issue.get('severity', 'LOW')
                    severity_counts[severity] += 1
        
        return {
            'total_apks_processed': total_apks,
            'successful_analyses': successful_analyses,
            'failed_analyses': total_apks - successful_analyses,
            'total_issues_found': total_issues,
            'severity_breakdown': severity_counts,
            'average_issues_per_apk': total_issues / successful_analyses if successful_analyses > 0 else 0
        }
    
    def _export_batch_results(self, results: List[Dict[str, Any]], summary: Dict[str, Any]):
        """Export batch results to files"""
        
        # Export detailed results
        with open('batch_analysis_detailed.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Export summary
        with open('batch_analysis_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info("Batch results exported to JSON files")


# ============================================================================
# Example 5: Django Integration
# ============================================================================

# Django models example
"""
# models.py
from django.db import models

class APKAnalysis(models.Model):
    analysis_id = models.CharField(max_length=100, unique=True)
    apk_file = models.FileField(upload_to='apks/')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending')
    total_issues = models.IntegerField(default=0)
    security_score = models.IntegerField(default=0)
    analysis_results = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class SecurityIssue(models.Model):
    analysis = models.ForeignKey(APKAnalysis, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    severity = models.CharField(max_length=20)
    file_path = models.CharField(max_length=500)
    line_number = models.IntegerField(null=True)
    description = models.TextField()
    recommendation = models.TextField()
"""

# Django views example
"""
# views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from vulnapk_client import VulnApkClient

class APKAnalysisView(View):
    def __init__(self):
        super().__init__()
        self.vulnapk_client = VulnApkClient()
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        if 'apk_file' not in request.FILES:
            return JsonResponse({'error': 'No APK file provided'}, status=400)
        
        apk_file = request.FILES['apk_file']
        
        # Save file temporarily
        temp_path = f'/tmp/{apk_file.name}'
        with open(temp_path, 'wb') as f:
            for chunk in apk_file.chunks():
                f.write(chunk)
        
        # Run analysis
        result = self.vulnapk_client.analyze_apk(temp_path)
        
        if result['success']:
            # Create database record
            analysis = APKAnalysis.objects.create(
                analysis_id=f"analysis_{request.user.id}_{int(time.time())}",
                apk_file=apk_file,
                user=request.user,
                status='completed',
                total_issues=result['total_issues'],
                analysis_results=result
            )
            
            return JsonResponse({
                'analysis_id': analysis.analysis_id,
                'total_issues': result['total_issues'],
                'status': 'completed'
            })
        else:
            return JsonResponse({'error': result['error']}, status=500)
"""


# ============================================================================
# Example Usage and Testing
# ============================================================================

def main():
    """Example usage of different integration patterns"""
    
    print("🔍 VulnApk Integration Examples")
    print("=" * 50)
    
    # Example 1: Direct integration
    print("\n1. Direct Service Integration:")
    service = MyExistingService()
    # result = service.process_uploaded_apk("example.apk", "user123")
    # print(f"   Result: {result}")
    
    # Example 2: HTTP client integration
    print("\n2. HTTP Client Integration:")
    http_client = VulnApkHttpClient()
    # analysis = http_client.analyze_apk_file("example.apk")
    # print(f"   Analysis ID: {analysis['analysis_id']}")
    
    # Example 3: Batch processing
    print("\n3. Batch Processing:")
    batch_processor = BatchAPKProcessor()
    # summary = batch_processor.process_apk_directory("/path/to/apks")
    # print(f"   Processed {summary['total_apks_processed']} APKs")
    
    # Example 4: Quick analysis
    print("\n4. Quick Analysis:")
    # result = quick_analyze("example.apk", plugins=["hardcode_secrets"])
    # print(f"   Found {result['total_issues']} issues")
    
    print("\n✅ All integration examples ready!")
    print("\nChoose the integration pattern that best fits your architecture:")
    print("- Direct integration: For monolithic applications")
    print("- HTTP client: For microservice architecture")
    print("- Async integration: For high-performance applications")
    print("- Batch processing: For bulk analysis workflows")


if __name__ == "__main__":
    main() 