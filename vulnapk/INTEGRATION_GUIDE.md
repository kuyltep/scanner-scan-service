# 🚀 VulnApk Service Integration Guide

Complete guide for integrating VulnApk security scanner into your existing services and applications.

## 📋 Table of Contents

1. [Integration Options](#integration-options)
2. [Quick Start](#quick-start)
3. [Direct Integration](#direct-integration)
4. [REST API Service](#rest-api-service)
5. [Microservice Architecture](#microservice-architecture)
6. [Docker Deployment](#docker-deployment)
7. [Production Considerations](#production-considerations)
8. [Examples](#examples)

## 🎯 Integration Options

### Option 1: Direct Library Integration
**Best for:** Monolithic applications, simple use cases
- Import VulnApk directly into your Python code
- Synchronous and asynchronous support
- Full control over analysis process

### Option 2: REST API Service
**Best for:** Microservice architecture, language-agnostic integration
- FastAPI-based HTTP service
- Background processing with job queues
- Scalable and language-independent

### Option 3: Containerized Microservice
**Best for:** Cloud-native applications, Kubernetes deployments
- Docker containers with all dependencies
- Horizontal scaling capabilities
- Production-ready with monitoring

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Service dependencies (for API integration)
pip install -r service_requirements.txt

# Install smaliflow
pip install -e ../smaliflow
```

### 2. Verify Installation

```python
from vulnapk_client import VulnApkClient

# Test client
client = VulnApkClient()
print(f"Available plugins: {client.get_available_plugins()}")
```

### 3. Quick Analysis

```python
from vulnapk_client import quick_analyze

# Analyze APK file
result = quick_analyze("your_app.apk")
print(f"Found {result['total_issues']} security issues")
```

## 🔧 Direct Integration

### Step 1: Add VulnApk to Your Project

```python
# your_service.py
import sys
import os
sys.path.insert(0, '/path/to/vulnapk')

from vulnapk_client import VulnApkClient
```

### Step 2: Initialize Client

```python
class YourService:
    def __init__(self):
        self.vulnapk_client = VulnApkClient(
            temp_dir="/tmp/your_service_vulnapk",
            log_level=logging.INFO
        )
```

### Step 3: Integrate Analysis

```python
def process_apk_upload(self, apk_file_path: str, user_id: str):
    """Process uploaded APK with security analysis"""
    
    # Run security analysis
    result = self.vulnapk_client.analyze_apk(
        apk_path=apk_file_path,
        included_plugins=["hardcode_secrets", "unsafe_crypto"]
    )
    
    if result['success']:
        # Process results
        security_score = self.calculate_security_score(result)
        self.store_results(user_id, result)
        
        return {
            'status': 'success',
            'security_score': security_score,
            'issues_found': result['total_issues']
        }
    else:
        return {'status': 'error', 'message': result['error']}
```

### Step 4: Async Integration (Optional)

```python
async def process_apk_async(self, apk_file_path: str):
    """Async APK processing"""
    
    result = await self.vulnapk_client.analyze_apk_async(apk_file_path)
    return result
```

## 🌐 REST API Service

### Step 1: Start VulnApk Service

```bash
# Development
python vulnapk_service.py

# Production with Gunicorn
gunicorn vulnapk_service:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Step 2: Use HTTP Client

```python
from integration_examples import VulnApkHttpClient

# Initialize client
client = VulnApkHttpClient("http://localhost:8000")

# Upload and analyze APK
analysis = client.analyze_apk_file("your_app.apk")
analysis_id = analysis['analysis_id']

# Wait for results
results = client.wait_for_analysis(analysis_id)
print(f"Analysis completed: {results['total_issues']} issues found")
```

### Step 3: API Endpoints

```bash
# Upload APK file
curl -X POST "http://localhost:8000/analyze/upload" \
     -F "file=@your_app.apk" \
     -F "included_plugins=hardcode_secrets,unsafe_crypto"

# Check status
curl "http://localhost:8000/analyze/{analysis_id}/status"

# Get results
curl "http://localhost:8000/analyze/{analysis_id}/results"

# List available plugins
curl "http://localhost:8000/plugins"
```

## 🐳 Docker Deployment

### Step 1: Build Docker Image

```bash
# Build image
docker build -t vulnapk-scanner .

# Or use docker-compose
docker-compose build
```

### Step 2: Run Container

```bash
# Simple run
docker run -p 8000:8000 vulnapk-scanner

# With docker-compose (recommended)
docker-compose up -d
```

### Step 3: Scale Services

```bash
# Scale API service
docker-compose up -d --scale vulnapk-api=3

# Check status
docker-compose ps
```

### Step 4: Production Deployment

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  vulnapk-api:
    image: vulnapk-scanner:latest
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@postgres:5432/vulnapk
```

## 🏗️ Microservice Architecture

### Service Communication

```python
# In your main service
import httpx

class YourMainService:
    def __init__(self):
        self.vulnapk_url = "http://vulnapk-service:8000"
        self.http_client = httpx.AsyncClient()
    
    async def analyze_user_apk(self, user_id: str, apk_data: bytes):
        """Analyze APK via microservice"""
        
        # Upload to VulnApk service
        files = {'file': ('app.apk', apk_data, 'application/vnd.android.package-archive')}
        response = await self.http_client.post(
            f"{self.vulnapk_url}/analyze/upload",
            files=files
        )
        
        analysis_data = response.json()
        analysis_id = analysis_data['analysis_id']
        
        # Store analysis ID for tracking
        await self.store_analysis_tracking(user_id, analysis_id)
        
        return analysis_id
    
    async def get_analysis_results(self, analysis_id: str):
        """Get analysis results"""
        
        response = await self.http_client.get(
            f"{self.vulnapk_url}/analyze/{analysis_id}/results"
        )
        
        return response.json()
```

### Event-Driven Integration

```python
# Using Redis pub/sub for event-driven communication
import redis
import json

class EventDrivenIntegration:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
    
    async def on_analysis_complete(self, analysis_id: str, results: dict):
        """Handle analysis completion event"""
        
        # Publish event
        event_data = {
            'event_type': 'analysis_complete',
            'analysis_id': analysis_id,
            'results': results
        }
        
        self.redis_client.publish('vulnapk_events', json.dumps(event_data))
    
    def subscribe_to_events(self):
        """Subscribe to VulnApk events"""
        
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('vulnapk_events')
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                event_data = json.loads(message['data'])
                self.handle_event(event_data)
```

## 🔒 Production Considerations

### 1. Security

```python
# Add authentication
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/analyze/upload")
async def analyze_apk(
    file: UploadFile = File(...),
    token: str = Depends(security)
):
    # Validate token
    if not validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    # Process analysis...
```

### 2. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/analyze/upload")
@limiter.limit("5/minute")
async def analyze_apk(request: Request, file: UploadFile = File(...)):
    # Analysis logic...
```

### 3. Resource Management

```python
# Configure resource limits
import resource

# Set memory limit (2GB)
resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, -1))

# Set CPU time limit (5 minutes per analysis)
resource.setrlimit(resource.RLIMIT_CPU, (300, -1))
```

### 4. Monitoring

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
analysis_counter = Counter('vulnapk_analyses_total', 'Total analyses performed')
analysis_duration = Histogram('vulnapk_analysis_duration_seconds', 'Analysis duration')

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    if request.url.path.startswith("/analyze"):
        analysis_counter.inc()
        analysis_duration.observe(time.time() - start_time)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 📊 Examples

### Django Integration

```python
# models.py
from django.db import models

class APKAnalysis(models.Model):
    analysis_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    apk_file = models.FileField(upload_to='apks/')
    status = models.CharField(max_length=20, default='pending')
    total_issues = models.IntegerField(default=0)
    security_score = models.IntegerField(default=0)
    analysis_results = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

# views.py
from django.http import JsonResponse
from vulnapk_client import VulnApkClient

def upload_apk(request):
    if request.method == 'POST':
        apk_file = request.FILES['apk_file']
        
        # Save file
        analysis = APKAnalysis.objects.create(
            user=request.user,
            apk_file=apk_file,
            analysis_id=f"analysis_{request.user.id}_{int(time.time())}"
        )
        
        # Run analysis
        client = VulnApkClient()
        result = client.analyze_apk(analysis.apk_file.path)
        
        # Update record
        analysis.status = 'completed' if result['success'] else 'failed'
        analysis.total_issues = result.get('total_issues', 0)
        analysis.analysis_results = result
        analysis.save()
        
        return JsonResponse({
            'analysis_id': analysis.analysis_id,
            'status': analysis.status,
            'total_issues': analysis.total_issues
        })
```

### Flask Integration

```python
from flask import Flask, request, jsonify
from vulnapk_client import VulnApkClient

app = Flask(__name__)
vulnapk_client = VulnApkClient()

@app.route('/analyze', methods=['POST'])
def analyze_apk():
    if 'apk_file' not in request.files:
        return jsonify({'error': 'No APK file provided'}), 400
    
    file = request.files['apk_file']
    
    # Save file temporarily
    temp_path = f'/tmp/{file.filename}'
    file.save(temp_path)
    
    # Run analysis
    result = vulnapk_client.analyze_apk(temp_path)
    
    if result['success']:
        return jsonify({
            'total_issues': result['total_issues'],
            'issues': result['issues'][:5],  # First 5 issues
            'plugins_used': result['plugins_used']
        })
    else:
        return jsonify({'error': result['error']}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### Celery Background Tasks

```python
from celery import Celery
from vulnapk_client import VulnApkClient

# Configure Celery
celery_app = Celery('vulnapk_tasks', broker='redis://localhost:6379/0')

@celery_app.task
def analyze_apk_task(apk_path: str, user_id: str):
    """Background task for APK analysis"""
    
    client = VulnApkClient()
    result = client.analyze_apk(apk_path)
    
    # Store results in database
    store_analysis_results(user_id, result)
    
    # Send notification
    if result['success'] and result['total_issues'] > 0:
        send_security_alert(user_id, result)
    
    return result

# Usage in your service
def upload_apk(user_id: str, apk_path: str):
    # Start background analysis
    task = analyze_apk_task.delay(apk_path, user_id)
    
    return {
        'task_id': task.id,
        'status': 'processing'
    }
```

## 🚀 Getting Started Checklist

### Prerequisites
- [ ] Python 3.8+ installed
- [ ] Java JDK/JRE installed
- [ ] Docker installed (for containerized deployment)
- [ ] Redis installed (for API service)

### Setup Steps
1. [ ] Clone VulnApk repository
2. [ ] Install dependencies: `pip install -r service_requirements.txt`
3. [ ] Install smaliflow: `pip install -e ../smaliflow`
4. [ ] Verify installation: `python vulnapk_client.py`
5. [ ] Choose integration approach
6. [ ] Implement integration code
7. [ ] Test with sample APK
8. [ ] Deploy to production

### Integration Checklist
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Resource limits set
- [ ] Security measures in place
- [ ] Monitoring enabled
- [ ] Backup strategy defined

## 🆘 Troubleshooting

### Common Issues

1. **Java not found**
   ```bash
   export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
   export PATH=$PATH:$JAVA_HOME/bin
   ```

2. **smalivm import error**
   ```bash
   pip install -e ../smaliflow
   ```

3. **APK decompilation failed**
   - Check APK file integrity
   - Verify apkeditor.jar exists
   - Check Java version compatibility

4. **Memory issues**
   - Increase container memory limits
   - Implement analysis queuing
   - Use streaming for large files

### Performance Optimization

1. **Parallel Processing**
   ```python
   # Use async for multiple APKs
   results = await client.analyze_multiple_apks_async(apk_paths)
   ```

2. **Plugin Selection**
   ```python
   # Run only necessary plugins
   result = client.analyze_apk(
       apk_path,
       included_plugins=["hardcode_secrets"]
   )
   ```

3. **Caching**
   ```python
   # Cache analysis results
   import hashlib
   
   def get_apk_hash(apk_path):
       with open(apk_path, 'rb') as f:
           return hashlib.sha256(f.read()).hexdigest()
   ```

---

**Ready to integrate VulnApk into your service? Choose your integration approach and follow the step-by-step guide above! 🚀** 