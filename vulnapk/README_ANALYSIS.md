# 🔍 VulnApk Local APK Analysis Guide

A comprehensive guide to analyze your Android APK files for security vulnerabilities using the VulnApk framework.

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Run the setup script to check dependencies
python setup_environment.py
```

### 2. Analyze Your APK
```bash
# Basic analysis
python analyze_local_apk.py /path/to/your/app.apk

# Example with actual file
python analyze_local_apk.py myapp.apk
```

### 3. Check Results
- Reports are saved in the `reports/` directory
- JSON format with detailed vulnerability information

## 📋 Prerequisites

### Required Software:
- **Python 3.8+** with pip
- **Java JDK/JRE** (for APK decompilation)
- **apkeditor.jar** (included in project)

### Required Files:
- `apkeditor.jar` - APK decompilation tool
- `requirements.txt` - Python dependencies
- `smaliflow/` - Smali VM for bytecode analysis

## 🔧 Manual Setup

If the automatic setup fails, follow these steps:

### 1. Install Java
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install openjdk-11-jdk

# Windows - Download from https://adoptium.net/
# macOS - brew install openjdk@11
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Setup
```bash
java -version  # Should show Java version
python -c "import smalivm; print('smalivm OK')"
```

## 🎯 Usage Examples

### Basic Analysis
```python
from analyze_local_apk import analyze_apk

# Analyze single APK
results = analyze_apk("myapp.apk")
print(f"Found {results['total_issues']} security issues")
```

### Advanced Configuration
```python
from vulnapk.main import VulnApk

# Custom analysis with specific plugins
vulnapk = VulnApk(
    files=["app1.apk", "app2.apk"],
    included_plugins=["hardcode_secrets", "unsafe_crypto"],
    output_reports="custom_reports"
)

results = vulnapk.start()
```

### Batch Analysis
```python
import os
from analyze_local_apk import analyze_apk

# Analyze all APKs in a directory
apk_dir = "apk_files/"
for file in os.listdir(apk_dir):
    if file.endswith('.apk'):
        apk_path = os.path.join(apk_dir, file)
        results = analyze_apk(apk_path, f"reports/{file}_analysis")
        print(f"{file}: {results['total_issues']} issues found")
```

## 🔌 Available Security Plugins

### 1. Hardcoded Secrets (`hardcode_secrets.py`)
- **Detects**: API keys, passwords, tokens in code
- **Severity**: High
- **Examples**: AWS keys, database passwords, OAuth tokens

### 2. Unsafe Cryptography (`unsafe_crypto.py`)
- **Detects**: Weak encryption algorithms, poor key management
- **Severity**: Medium-High
- **Examples**: MD5, SHA1, hardcoded encryption keys

### 3. Shared Preferences (`sharedprefs.py`)
- **Detects**: Insecure data storage in SharedPreferences
- **Severity**: Medium
- **Examples**: Sensitive data stored in plain text

## 📊 Understanding Results

### Report Structure
```json
{
  "title": "Hardcoded API Key Found",
  "severity": "HIGH",
  "file": "com/example/app/ApiClient.smali",
  "line": 42,
  "description": "API key found in source code",
  "recommendation": "Store API keys securely using Android Keystore"
}
```

### Severity Levels
- **CRITICAL**: Immediate security risk
- **HIGH**: Significant vulnerability
- **MEDIUM**: Moderate security concern
- **LOW**: Minor security issue
- **INFO**: Informational finding

## 🛠️ Troubleshooting

### Common Issues

#### 1. Java Not Found
```bash
# Error: java command not found
# Solution: Install Java and add to PATH
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export PATH=$PATH:$JAVA_HOME/bin
```

#### 2. APK Decompilation Failed
```bash
# Error: apkeditor.jar failed
# Solution: Check APK file integrity
file myapp.apk  # Should show "Android application package"
```

#### 3. smalivm Import Error
```bash
# Error: No module named 'smalivm'
# Solution: Install smaliflow dependency
pip install -e ../smaliflow
```

#### 4. Permission Denied
```bash
# Error: Permission denied accessing APK
# Solution: Check file permissions
chmod 644 myapp.apk
```

## 🎨 Customization

### Create Custom Plugin
```python
# plugins/my_custom_plugin.py
from plugins.base_plugin import BasePlugin, Problem

class Plugin(BasePlugin):
    enabled = True
    
    def on_class(self, vm, cls):
        # Your custom security check logic
        if self.detect_vulnerability(cls):
            problem = Problem(
                title="Custom Vulnerability",
                severity="HIGH",
                file=cls.name,
                description="Custom security issue detected"
            )
            self.problems.add(problem)
```

### Filter Specific Plugins
```python
# Run only specific plugins
vulnapk = VulnApk(
    files=["myapp.apk"],
    included_plugins=["hardcode_secrets"]  # Only run this plugin
)

# Exclude specific plugins
vulnapk = VulnApk(
    files=["myapp.apk"],
    excluded_plugins=["sharedprefs"]  # Skip this plugin
)
```

## 📈 Performance Tips

### 1. Parallel Processing
- VulnApk uses 3 worker threads by default
- Larger APKs benefit from more memory allocation

### 2. Plugin Selection
- Use `included_plugins` for targeted analysis
- Skip unnecessary plugins with `excluded_plugins`

### 3. Output Management
- Specify custom output directory to organize reports
- Use timestamped reports for version tracking

## 🔒 Security Best Practices

### 1. APK Source Verification
- Only analyze APKs from trusted sources
- Verify APK signatures before analysis

### 2. Report Handling
- Store analysis reports securely
- Sanitize sensitive data in reports

### 3. Environment Isolation
- Run analysis in isolated environment
- Use virtual machines for untrusted APKs

## 📞 Support

### Getting Help
1. Check this README for common solutions
2. Verify all prerequisites are installed
3. Test with a simple APK first
4. Check log files for detailed error messages

### Debug Mode
```python
import logging
from vulnapk import logger

# Enable debug logging
logger.init(logging.DEBUG)
```

---

**Happy APK Hunting! 🕵️‍♂️** 