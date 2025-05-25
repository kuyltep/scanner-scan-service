#!/usr/bin/env python3
"""
Environment Setup Script for VulnApk
Checks and installs all required dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_java():
    """Check if Java is installed and accessible"""
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Java is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Java not found. Please install Java JDK/JRE")
    print("   Download from: https://adoptium.net/")
    return False


def check_apkeditor():
    """Check if apkeditor.jar exists"""
    apkeditor_path = Path("apkeditor.jar")
    if apkeditor_path.exists():
        print("✅ apkeditor.jar found")
        return True
    else:
        print("❌ apkeditor.jar not found in current directory")
        print("   This file should be in the project root")
        return False


def install_python_dependencies():
    """Install Python dependencies from requirements.txt"""
    try:
        print("📦 Installing Python dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Python dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def check_smalivm():
    """Check if smalivm is available"""
    try:
        import smalivm
        print("✅ smalivm module available")
        return True
    except ImportError:
        print("❌ smalivm module not found")
        print("   Check if smaliflow is properly installed")
        return False


def create_sample_script():
    """Create a sample analysis script"""
    sample_content = '''#!/usr/bin/env python3
"""
Sample APK Analysis Script
Replace 'path/to/your/app.apk' with your actual APK path
"""

from analyze_local_apk import analyze_apk

# Example usage
if __name__ == "__main__":
    # Replace with your APK path
    apk_path = "path/to/your/app.apk"
    
    try:
        results = analyze_apk(apk_path, output_dir="my_reports")
        print(f"Analysis found {results['total_issues']} security issues")
    except Exception as e:
        print(f"Error: {e}")
'''
    
    with open("sample_analysis.py", "w") as f:
        f.write(sample_content)
    print("✅ Created sample_analysis.py")


def main():
    """Main setup function"""
    print("🔧 Setting up VulnApk environment...\n")
    
    all_good = True
    
    # Check Java
    if not check_java():
        all_good = False
    
    # Check apkeditor.jar
    if not check_apkeditor():
        all_good = False
    
    # Install Python dependencies
    if not install_python_dependencies():
        all_good = False
    
    # Check smalivm
    if not check_smalivm():
        all_good = False
    
    # Create sample script
    create_sample_script()
    
    print("\n" + "="*50)
    if all_good:
        print("🎉 Environment setup complete!")
        print("\n📋 Next steps:")
        print("1. Place your APK file in the project directory")
        print("2. Run: python analyze_local_apk.py your_app.apk")
        print("3. Check the 'reports' directory for results")
        print("\n💡 Example:")
        print("   python analyze_local_apk.py myapp.apk")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main() 