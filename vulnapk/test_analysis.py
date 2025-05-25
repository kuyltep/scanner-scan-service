#!/usr/bin/env python3
"""
Comprehensive Test Script for VulnApk Local Analysis
Demonstrates various usage patterns and configurations
"""

import os
import sys
import json
from pathlib import Path

# Add vulnapk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vulnapk'))

from vulnapk.main import VulnApk
from analyze_local_apk import analyze_apk
import vulnapk.logger as logger
import logging


def test_basic_analysis():
    """Test basic APK analysis functionality"""
    print("🧪 Testing Basic Analysis...")
    
    # This would work with a real APK file
    # apk_path = "sample.apk"
    # results = analyze_apk(apk_path)
    # print(f"Found {results['total_issues']} issues")
    
    print("✅ Basic analysis test structure ready")


def test_advanced_configuration():
    """Test advanced VulnApk configuration options"""
    print("\n🧪 Testing Advanced Configuration...")
    
    try:
        # Example with multiple configuration options
        vulnapk = VulnApk(
            # files=["app1.apk", "app2.apk"],  # Multiple APK files
            # directories=["apk_folder"],       # APK directory
            # packages=["com.example.app"],     # Package to download
            included_plugins=["hardcode_secrets", "unsafe_crypto"],  # Specific plugins
            output_reports="test_reports"
        )
        
        print(f"✅ VulnApk configured with {len(vulnapk.plugins)} plugins:")
        for plugin in vulnapk.plugins:
            print(f"   - {plugin.__class__.__module__}")
            
    except ValueError as e:
        print(f"⚠️  Expected error (no APK provided): {e}")


def test_plugin_filtering():
    """Test plugin inclusion/exclusion functionality"""
    print("\n🧪 Testing Plugin Filtering...")
    
    # Test with included plugins only
    try:
        vulnapk_included = VulnApk(
            # files=["test.apk"],  # Would need real APK
            included_plugins=["hardcode_secrets"],
            output_reports="test_reports"
        )
        print(f"✅ Included plugins: {len(vulnapk_included.plugins)} loaded")
    except ValueError:
        print("⚠️  Expected error (no APK provided)")
    
    # Test with excluded plugins
    try:
        vulnapk_excluded = VulnApk(
            # files=["test.apk"],  # Would need real APK
            excluded_plugins=["sharedprefs"],
            output_reports="test_reports"
        )
        print(f"✅ Excluded plugins: {len(vulnapk_excluded.plugins)} loaded")
    except ValueError:
        print("⚠️  Expected error (no APK provided)")


def test_batch_analysis():
    """Test batch analysis functionality"""
    print("\n🧪 Testing Batch Analysis Pattern...")
    
    # Simulate batch analysis logic
    apk_files = ["app1.apk", "app2.apk", "app3.apk"]  # Example files
    
    print("📁 Batch analysis pattern:")
    for apk_file in apk_files:
        print(f"   - Would analyze: {apk_file}")
        # results = analyze_apk(apk_file, f"reports/{apk_file}_analysis")
        # print(f"     Found: {results['total_issues']} issues")
    
    print("✅ Batch analysis pattern ready")


def test_custom_output():
    """Test custom output directory functionality"""
    print("\n🧪 Testing Custom Output...")
    
    custom_output = "custom_security_reports"
    os.makedirs(custom_output, exist_ok=True)
    
    print(f"📁 Created custom output directory: {custom_output}")
    print("✅ Custom output configuration ready")


def test_error_handling():
    """Test error handling scenarios"""
    print("\n🧪 Testing Error Handling...")
    
    # Test non-existent APK file
    try:
        vulnapk = VulnApk(files=["nonexistent.apk"])
    except ValueError as e:
        print(f"✅ Correctly caught error: {e}")
    
    # Test invalid file extension
    try:
        # Create a dummy file with wrong extension
        with open("test.txt", "w") as f:
            f.write("dummy")
        vulnapk = VulnApk(files=["test.txt"])
    except Exception as e:
        print(f"✅ Correctly handled invalid file")
        os.remove("test.txt")  # Cleanup
    
    # Test no input provided
    try:
        vulnapk = VulnApk()
    except ValueError as e:
        print(f"✅ Correctly caught no input error: {e}")


def demonstrate_usage_patterns():
    """Demonstrate various usage patterns"""
    print("\n📚 Usage Pattern Examples:")
    
    patterns = [
        {
            "name": "Single APK Analysis",
            "code": 'vulnapk = VulnApk(files="myapp.apk")',
            "description": "Analyze one APK file"
        },
        {
            "name": "Multiple APK Analysis", 
            "code": 'vulnapk = VulnApk(files=["app1.apk", "app2.apk"])',
            "description": "Analyze multiple APK files"
        },
        {
            "name": "Directory Analysis",
            "code": 'vulnapk = VulnApk(directories="apk_folder")',
            "description": "Analyze all APKs in a directory"
        },
        {
            "name": "Package Download",
            "code": 'vulnapk = VulnApk(packages="com.example.app")',
            "description": "Download and analyze package"
        },
        {
            "name": "Targeted Security Check",
            "code": 'vulnapk = VulnApk(files="app.apk", included_plugins=["hardcode_secrets"])',
            "description": "Run specific security plugins only"
        },
        {
            "name": "Custom Output",
            "code": 'vulnapk = VulnApk(files="app.apk", output_reports="security_reports")',
            "description": "Save reports to custom directory"
        }
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\n{i}. {pattern['name']}")
        print(f"   Code: {pattern['code']}")
        print(f"   Use: {pattern['description']}")


def main():
    """Main test function"""
    print("🔍 VulnApk Local Analysis Test Suite")
    print("=" * 50)
    
    # Initialize logging
    logger.init(logging.INFO)
    
    # Run tests
    test_basic_analysis()
    test_advanced_configuration()
    test_plugin_filtering()
    test_batch_analysis()
    test_custom_output()
    test_error_handling()
    demonstrate_usage_patterns()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\n📋 To analyze your APK:")
    print("1. Place your APK file in this directory")
    print("2. Run: python analyze_local_apk.py your_app.apk")
    print("3. Check the 'reports' directory for results")
    
    print("\n🔧 Available plugins:")
    try:
        vulnapk = VulnApk(files=["dummy.apk"])  # Will fail but load plugins
    except:
        pass
    
    # Show available plugins by checking the plugins directory
    plugin_dir = Path("vulnapk/plugins")
    if plugin_dir.exists():
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name != "base_plugin.py":
                plugin_name = plugin_file.stem
                print(f"   - {plugin_name}")


if __name__ == "__main__":
    main() 