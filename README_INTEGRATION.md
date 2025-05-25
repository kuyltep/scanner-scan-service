# 🔍 Scanner Service with VulnApk Integration

A comprehensive file scanning service that automatically detects and analyzes APK files using the VulnApk security framework, while maintaining support for other file types.

## 🚀 Features

### Core Capabilities
- **Automatic APK Detection**: Intelligently routes APK files to VulnApk analysis
- **Async Processing**: APK files are processed asynchronously for better performance
- **Security Analysis**: Comprehensive security vulnerability detection for Android apps
- **PDF Reports**: Unified PDF report generation for all file types
- **Kafka Integration**: Message queue processing for scalable file handling
- **MinIO Storage**: Secure file storage and retrieval
- **Fallback Support**: Graceful fallback to default scanning for non-APK files

### VulnApk Security Plugins
- **Hardcoded Secrets**: Detects API keys, passwords, tokens in code
- **Unsafe Cryptography**: Identifies weak encryption and poor key management
- **Shared Preferences**: Finds insecure data storage patterns

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Kafka Queue   │───▶│  Scanner Service │───▶│   MinIO Storage │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   File Analysis  │
                       │                  │
                       │  ┌─────────────┐ │
                       │  │ APK Files   │ │
                       │  │ VulnApk     │ │
                       │  │ Analysis    │ │
                       │  └─────────────┘ │
                       │                  │
                       │  ┌─────────────┐ │
                       │  │ Other Files │ │
                       │  │ Default     │ │
                       │  │ Scanning    │ │
                       │  └─────────────┘ │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   PDF Report     │
                       │   Generation     │
                       └──────────────────┘
```

## 🛠️ Setup and Installation

### Prerequisites
- Docker and Docker Compose
- Java 11+ (for APK decompilation)
- Python 3.11+

### Quick Start with Docker

1. **Clone and Build**
```bash
git clone <repository>
cd scanner-scan-service
docker-compose up --build
```

2. **Access Services**
- Scanner Service: `http://localhost:8000`
- Kafka UI: `http://localhost:8080` (dev profile)
- MinIO Console: `http://localhost:9001`

### Manual Setup

1. **Install Dependencies**
```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r vulnapk/requirements.txt
pip install -r vulnapk/service_requirements.txt

# Install Java 11
sudo apt-get install openjdk-11-jdk

# Install wkhtmltopdf
sudo apt-get install wkhtmltopdf
```

2. **Setup VulnApk**
```bash
cd vulnapk
python setup_environment.py
```

3. **Run Service**
```bash
python main.py
```

## 📊 Usage Examples

### APK File Processing

When an APK file is submitted to the scanner:

1. **Automatic Detection**: Service detects `.apk` extension
2. **Async Processing**: File is processed using VulnApk async analysis
3. **Security Analysis**: Multiple security plugins scan for vulnerabilities
4. **Report Generation**: Comprehensive PDF report with security findings
5. **Storage**: Results uploaded to MinIO and status sent via Kafka

### Sample APK Analysis Output

```json
{
  "id": "APK-SUMMARY",
  "name": "APK Security Analysis Summary",
  "severity": "INFO",
  "description": "VulnApk found 5 security issues in 12.34 seconds",
  "analysis_type": "VulnApk Security Analysis"
}
```

### Non-APK File Processing

Non-APK files continue to use the original scanning logic:
- Synchronous processing
- Default scan.json analysis
- Standard PDF report generation

## 🔧 Configuration

### Environment Variables

```bash
# Java Configuration
JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# PDF Generation
WKHTMLTOPDF_CMD=/usr/local/bin/wkhtmltopdf-headless

# Python Path
PYTHONPATH=/home/scanner/app
```

### VulnApk Plugin Configuration

Modify scanner.py to customize plugin selection:

```python
# Current configuration
analysis_result = self.vulnapk_client.analyze_apk(
    apk_path=file_path,
    included_plugins=["hardcode_secrets", "unsafe_crypto", "sharedprefs"]
)

# Custom configuration
analysis_result = self.vulnapk_client.analyze_apk(
    apk_path=file_path,
    included_plugins=["hardcode_secrets"],  # Only secrets detection
    excluded_plugins=["sharedprefs"]        # Skip shared preferences
)
```

## 📈 Performance Optimizations

### Async Processing
- APK files are processed asynchronously using `asyncio`
- Non-blocking I/O for better throughput
- Concurrent processing capability

### Docker Multi-stage Build
- Optimized production images
- Separate development and production stages
- Minimal runtime dependencies

### Caching Strategy
- VulnApk client with temporary directory management
- Automatic cleanup of temporary files
- Efficient resource utilization

## 🔍 Monitoring and Debugging

### Health Checks
```bash
# Docker health check
docker ps  # Check container health status

# Manual health check
python -c "import sys; sys.path.insert(0, 'vulnapk'); from vulnapk_client import VulnApkClient; print('Health check passed')"
```

### Logging
- Structured logging with timestamps
- Separate log levels for different components
- Error tracking and debugging information

### Development Tools
```bash
# Run with development profile
docker-compose --profile dev up

# Access Kafka UI for message monitoring
open http://localhost:8080

# Access MinIO console for file management
open http://localhost:9001
```

## 🚨 Error Handling

### APK Analysis Failures
- Automatic fallback to default scanning
- Error logging and notification
- Graceful degradation of service

### Resource Management
- Automatic cleanup of temporary files
- Memory-efficient processing
- Timeout handling for long-running analyses

## 🔒 Security Considerations

### Container Security
- Non-root user execution
- Minimal base image
- Security scanning integration

### File Processing
- Isolated temporary directories
- Secure file handling
- Input validation and sanitization

## 📋 API Reference

### Scanner Class Methods

```python
# Synchronous scanning
result = scanner.scan_file(file_path, file_name, folder_name, name)

# Asynchronous scanning (for APK files)
result = await scanner.scan_file_async(file_path, file_name, folder_name, name)
```

### VulnApk Client Integration

```python
from vulnapk_client import VulnApkClient

client = VulnApkClient(
    temp_dir="/tmp/vulnapk",
    log_level=logging.INFO
)

# Analyze APK
result = client.analyze_apk("app.apk")

# Async analysis
result = await client.analyze_apk_async("app.apk")
```

## 🧪 Testing

### Unit Tests
```bash
# Run tests in development container
docker-compose exec scanner-service python -m pytest -v

# Run specific test
docker-compose exec scanner-service python -m pytest tests/test_scanner.py -v
```

### Integration Tests
```bash
# Test APK analysis
python vulnapk/test_analysis.py

# Test full workflow
python vulnapk/sample_analysis.py
```

## 🚀 Deployment

### Production Deployment
```bash
# Build production image
docker build --target production -t scanner-service:prod .

# Run with production configuration
docker run -d \
  --name scanner-service \
  -e PYTHONOPTIMIZE=1 \
  scanner-service:prod
```

### Scaling Considerations
- Horizontal scaling with multiple container instances
- Load balancing for high-throughput scenarios
- Resource allocation based on file types and sizes

## 📚 Additional Resources

- [VulnApk Documentation](vulnapk/README_ANALYSIS.md)
- [Integration Examples](vulnapk/integration_examples.py)
- [Setup Guide](vulnapk/INTEGRATION_GUIDE.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Happy Scanning! 🔍🛡️** 