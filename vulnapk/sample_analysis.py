#!/usr/bin/env python3
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
