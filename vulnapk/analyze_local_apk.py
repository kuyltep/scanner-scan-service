#!/usr/bin/env python3
"""
Local APK Analysis Script using VulnApk
Usage: python analyze_local_apk.py /path/to/your/app.apk
"""

import os
import sys
import json
from pathlib import Path

# Add the vulnapk module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vulnapk'))

from vulnapk.main import VulnApk
import vulnapk.logger as logger
import logging


def analyze_apk(apk_path: str, output_dir: str = "reports") -> dict:
    """
    Analyze a local APK file for security vulnerabilities
    
    Args:
        apk_path: Path to the APK file
        output_dir: Directory to save analysis reports
        
    Returns:
        Dictionary containing analysis results
    """
    
    # Initialize logging
    logger.init(logging.INFO)
    
    # Validate APK file exists
    if not os.path.exists(apk_path):
        raise FileNotFoundError(f"APK file not found: {apk_path}")
    
    if not apk_path.endswith('.apk'):
        raise ValueError("File must have .apk extension")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🔍 Starting analysis of: {apk_path}")
    print(f"📁 Reports will be saved to: {output_dir}")
    
    try:
        # Initialize VulnApk with your local APK
        vulnapk = VulnApk(
            files=[apk_path],  # Your local APK file
            output_reports=output_dir,  # Where to save reports
            # included_plugins=['hardcode_secrets'],  # Uncomment to run specific plugins
            # excluded_plugins=['unsafe_crypto'],     # Uncomment to exclude plugins
        )
        
        print(f"🔌 Loaded {len(vulnapk.plugins)} security plugins:")
        for plugin in vulnapk.plugins:
            print(f"  ✓ {plugin.__class__.__module__}")
        
        # Start the analysis
        print("\n🚀 Starting security analysis...")
        results = vulnapk.start()
        
        # Display summary
        print(f"\n📊 Analysis Complete!")
        print(f"   Found {len(results)} security issues")
        
        if results:
            print("\n⚠️  Security Issues Found:")
            for i, issue in enumerate(results[:5], 1):  # Show first 5 issues
                print(f"   {i}. {issue.get('title', 'Unknown Issue')}")
                print(f"      Severity: {issue.get('severity', 'Unknown')}")
                print(f"      Location: {issue.get('file', 'Unknown')}")
                print()
            
            if len(results) > 5:
                print(f"   ... and {len(results) - 5} more issues")
        else:
            print("✅ No security issues detected!")
        
        return {
            'apk_path': apk_path,
            'total_issues': len(results),
            'issues': results,
            'plugins_used': [p.__class__.__module__ for p in vulnapk.plugins]
        }
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        raise


def main():
    """Main entry point for the script"""
    
    if len(sys.argv) != 2:
        print("Usage: python analyze_local_apk.py <path_to_apk>")
        print("Example: python analyze_local_apk.py /path/to/myapp.apk")
        sys.exit(1)
    
    apk_path = sys.argv[1]
    
    try:
        results = analyze_apk(apk_path)
        print(f"\n✅ Analysis completed successfully!")
        print(f"📄 Detailed reports saved in 'reports' directory")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 