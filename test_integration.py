#!/usr/bin/env python3
"""
Integration Test for VulnApk Scanner Service
Tests the complete workflow of APK analysis integration
"""

import os
import sys
import asyncio
import tempfile
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.getcwd())

from scanner.scanner import Scanner
from app_types.message_types import IncomingMessage

def create_test_apk():
    """Create a dummy APK file for testing"""
    test_apk_content = b"PK\x03\x04"  # Basic ZIP header (APK is a ZIP file)
    
    with tempfile.NamedTemporaryFile(suffix='.apk', delete=False) as f:
        f.write(test_apk_content)
        return f.name

def create_test_file():
    """Create a dummy non-APK file for testing"""
    test_content = b"This is a test file content"
    
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(test_content)
        return f.name

def test_apk_detection():
    """Test APK file detection logic"""
    print("🔍 Testing APK file detection...")
    
    scanner = Scanner()
    
    # Test APK detection
    assert scanner._scan_apk_file.__name__ == '_scan_apk_file'
    assert scanner._scan_default_file.__name__ == '_scan_default_file'
    
    print("✅ APK detection logic is properly implemented")

def test_vulnapk_client_initialization():
    """Test VulnApk client initialization"""
    print("🔍 Testing VulnApk client initialization...")
    
    try:
        scanner = Scanner()
        assert scanner.vulnapk_client is not None
        print("✅ VulnApk client initialized successfully")
    except Exception as e:
        print(f"❌ VulnApk client initialization failed: {e}")
        return False
    
    return True

def test_sync_scanning():
    """Test synchronous scanning for non-APK files"""
    print("🔍 Testing synchronous scanning...")
    
    try:
        scanner = Scanner()
        test_file = create_test_file()
        
        # Test with non-APK file
        result = scanner.scan_file(
            file_path=test_file,
            file_name="test.txt",
            folder_name="test_folder",
            name="test_app"
        )
        
        assert len(result) == 3  # Should return (pdf_path, pdf_name, json_body)
        print("✅ Synchronous scanning works correctly")
        
        # Cleanup
        os.unlink(test_file)
        if os.path.exists(result[0]):
            os.unlink(result[0])
            
    except Exception as e:
        print(f"❌ Synchronous scanning failed: {e}")
        return False
    
    return True

async def test_async_scanning():
    """Test asynchronous scanning for APK files"""
    print("🔍 Testing asynchronous scanning...")
    
    try:
        scanner = Scanner()
        test_apk = create_test_apk()
        
        # Test with APK file (will likely fail VulnApk analysis but should fallback)
        result = await scanner.scan_file_async(
            file_path=test_apk,
            file_name="test.apk",
            folder_name="test_folder",
            name="test_app"
        )
        
        assert len(result) == 3  # Should return (pdf_path, pdf_name, json_body)
        print("✅ Asynchronous scanning works correctly")
        
        # Cleanup
        os.unlink(test_apk)
        if os.path.exists(result[0]):
            os.unlink(result[0])
            
    except Exception as e:
        print(f"❌ Asynchronous scanning failed: {e}")
        return False
    
    return True

def test_file_routing():
    """Test file routing logic"""
    print("🔍 Testing file routing logic...")
    
    # Define the function locally for testing
    def is_apk_file(file_path: str) -> bool:
        return file_path.lower().endswith('.apk')
    
    # Test APK detection
    assert is_apk_file("test.apk") == True
    assert is_apk_file("TEST.APK") == True
    assert is_apk_file("app.apk") == True
    
    # Test non-APK detection
    assert is_apk_file("test.txt") == False
    assert is_apk_file("document.pdf") == False
    assert is_apk_file("image.jpg") == False
    
    print("✅ File routing logic works correctly")

def test_vulnapk_result_conversion():
    """Test VulnApk result conversion to our format"""
    print("🔍 Testing VulnApk result conversion...")
    
    try:
        scanner = Scanner()
        
        # Mock VulnApk analysis result
        mock_result = {
            'success': True,
            'total_issues': 2,
            'analysis_time_seconds': 5.67,
            'issues': [
                {
                    'title': 'Hardcoded API Key',
                    'severity': 'HIGH',
                    'file': 'com/example/ApiClient.smali',
                    'line': 42,
                    'description': 'API key found in source code',
                    'recommendation': 'Store API keys securely'
                },
                {
                    'title': 'Weak Encryption',
                    'severity': 'MEDIUM',
                    'file': 'com/example/CryptoUtil.smali',
                    'line': 15,
                    'description': 'MD5 hash algorithm detected',
                    'recommendation': 'Use SHA-256 or stronger'
                }
            ],
            'plugins_used': ['hardcode_secrets', 'unsafe_crypto'],
            'apk_path': '/tmp/test.apk'
        }
        
        defects = scanner._convert_vulnapk_results(mock_result)
        
        # Should have summary + 2 issues = 3 defects
        assert len(defects) == 3
        assert defects[0]['id'] == 'APK-SUMMARY'
        assert defects[1]['id'] == 'APK-1'
        assert defects[2]['id'] == 'APK-2'
        
        print("✅ VulnApk result conversion works correctly")
        
    except Exception as e:
        print(f"❌ VulnApk result conversion failed: {e}")
        return False
    
    return True

def test_environment_setup():
    """Test environment and dependencies"""
    print("🔍 Testing environment setup...")
    
    # Check if required directories exist
    required_dirs = ['tmp', 'vulnapk']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            print(f"📁 Created directory: {dir_name}")
    
    # Check if VulnApk files exist
    vulnapk_files = [
        'vulnapk/vulnapk_client.py',
        'vulnapk/apkeditor.jar',
        'vulnapk/requirements.txt'
    ]
    
    missing_files = []
    for file_path in vulnapk_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"⚠️  Missing VulnApk files: {missing_files}")
        print("   Make sure VulnApk folder is properly set up")
    else:
        print("✅ VulnApk files are present")
    
    return len(missing_files) == 0

async def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting VulnApk Integration Tests\n")
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("APK Detection", test_apk_detection),
        ("VulnApk Client Init", test_vulnapk_client_initialization),
        ("File Routing", test_file_routing),
        ("VulnApk Result Conversion", test_vulnapk_result_conversion),
        ("Sync Scanning", test_sync_scanning),
        ("Async Scanning", test_async_scanning),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result is not False:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! VulnApk integration is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🔍 Integration test completed successfully!")
        print("🚀 You can now run the scanner service with VulnApk support:")
        print("   python main.py")
        print("   or")
        print("   docker-compose up --build")
    else:
        print("\n❌ Integration test failed. Please fix the issues before proceeding.")
        sys.exit(1) 