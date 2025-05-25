import json
import locale
import time
import pdfkit
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add VulnApk to path
vulnapk_path = os.path.join(os.getcwd(), "vulnapk")
if vulnapk_path not in sys.path:
    sys.path.insert(0, vulnapk_path)

from vulnapk_client import VulnApkClient

# Установка локали на русский язык
# locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')  # Для Linux/macOS
locale.setlocale(locale.LC_TIME, 'Russian_Russia.1251')  # Для Windows

class Scanner:
    def __init__(self):
        self.vulnapk_client = VulnApkClient(
            temp_dir=os.path.join(os.getcwd(), "tmp", "vulnapk"),
            log_level=20  # INFO level
        )
    
    def scan_file(self, file_path: str, file_name: str, folder_name: str, name: str):
        """Main scanning method that routes to appropriate scanner based on file type"""
        
        # Check if file is APK
        if file_path.lower().endswith('.apk'):
            return self._scan_apk_file(file_path, file_name, folder_name, name)
        else:
            return self._scan_default_file(file_path, file_name, folder_name, name)
    
    async def scan_file_async(self, file_path: str, file_name: str, folder_name: str, name: str):
        """Async version of scan_file for better performance"""
        
        if file_path.lower().endswith('.apk'):
            return await self._scan_apk_file_async(file_path, file_name, folder_name, name)
        else:
            return self._scan_default_file(file_path, file_name, folder_name, name)
    
    def _scan_apk_file(self, file_path: str, file_name: str, folder_name: str, name: str):
        """Synchronous APK scanning using VulnApk"""
        
        try:
            # Run VulnApk analysis
            analysis_result = self.vulnapk_client.analyze_apk(
                apk_path=file_path,
                included_plugins=["hardcode_secrets", "unsafe_crypto", "sharedprefs"]
            )
            
            if analysis_result['success']:
                # Convert VulnApk results to our format
                defects = self._convert_vulnapk_results(analysis_result)
                
                # Generate PDF report
                return self._generate_pdf_report(defects, folder_name, name, file_name)
            else:
                # Fallback to default scanning if VulnApk fails
                print(f"VulnApk analysis failed: {analysis_result.get('error', 'Unknown error')}")
                return self._scan_default_file(file_path, file_name, folder_name, name)
                
        except Exception as e:
            print(f"APK scanning error: {str(e)}")
            return self._scan_default_file(file_path, file_name, folder_name, name)
    
    async def _scan_apk_file_async(self, file_path: str, file_name: str, folder_name: str, name: str):
        """Async APK scanning using VulnApk"""
        
        try:
            # Run async VulnApk analysis
            analysis_result = await self.vulnapk_client.analyze_apk_async(
                apk_path=file_path,
                included_plugins=["hardcode_secrets", "unsafe_crypto", "sharedprefs"]
            )
            
            if analysis_result['success']:
                # Convert VulnApk results to our format
                defects = self._convert_vulnapk_results(analysis_result)
                
                # Generate PDF report
                return self._generate_pdf_report(defects, folder_name, name, file_name)
            else:
                # Fallback to default scanning if VulnApk fails
                print(f"VulnApk analysis failed: {analysis_result.get('error', 'Unknown error')}")
                return self._scan_default_file(file_path, file_name, folder_name, name)
                
        except Exception as e:
            print(f"Async APK scanning error: {str(e)}")
            return self._scan_default_file(file_path, file_name, folder_name, name)
    
    def _convert_vulnapk_results(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert VulnApk analysis results to our defect format"""
        
        defects = []
        issues = analysis_result.get('issues', [])
        
        for index, issue in enumerate(issues, start=1):
            defect = {
                "id": f"APK-{index}",
                "name": issue.get('title', 'Security Issue'),
                "severity": issue.get('severity', 'MEDIUM'),
                "file": issue.get('file', 'Unknown'),
                "line": issue.get('line', 0),
                "description": issue.get('description', 'No description available'),
                "recommendation": issue.get('recommendation', 'Review and fix this issue'),
                "details": json.dumps(issue, indent=4, ensure_ascii=False),
                "analysis_type": "VulnApk Security Analysis"
            }
            defects.append(defect)
        
        # Add summary information
        if defects:
            summary_defect = {
                "id": "APK-SUMMARY",
                "name": "APK Security Analysis Summary",
                "severity": "INFO",
                "file": "Analysis Summary",
                "line": 0,
                "description": f"VulnApk found {len(issues)} security issues in {analysis_result.get('analysis_time_seconds', 0):.2f} seconds",
                "recommendation": "Review all identified security issues and implement recommended fixes",
                "details": json.dumps({
                    "total_issues": analysis_result.get('total_issues', 0),
                    "analysis_time": analysis_result.get('analysis_time_seconds', 0),
                    "plugins_used": analysis_result.get('plugins_used', []),
                    "apk_path": analysis_result.get('apk_path', '')
                }, indent=4, ensure_ascii=False),
                "analysis_type": "VulnApk Security Analysis"
            }
            defects.insert(0, summary_defect)
        
        return defects
    
    def _scan_default_file(self, file_path: str, file_name: str, folder_name: str, name: str):
        """Original scanning logic for non-APK files"""
        
        with open(os.path.join(os.getcwd(), "scan.json"), 'r', encoding='utf-8') as json_file:
            raw_data = json.load(json_file)

        defects = []
        for index, item in enumerate(raw_data, start=1):
            defect = {
                "id": f"{index}",
                "name": item.get("name", "Unknown"),
                "details": json.dumps(item, indent=4, ensure_ascii=False),
            }
            defects.append(defect)

        return self._generate_pdf_report(defects, folder_name, name, file_name)
    
    def _generate_pdf_report(self, defects: List[Dict[str, Any]], folder_name: str, name: str, file_name: str):
        """Generate PDF report from defects data"""
        
        data = {
            "project_name": folder_name,
            "app_name": name,
            "analysis_date": datetime.now().strftime("%d %B %Y, %H:%M"),
            "defects": defects,
        }

        env = Environment(loader=FileSystemLoader(os.getcwd()))
        template = env.get_template('report_template.html')

        html_output = template.render(data)

        # Generate safe filename
        base_name = file_name.split('.')[0]
        if '-' in base_name:
            base_name = base_name.split('-')[1]
        pdf_filename = f"{time.time_ns()}-{base_name}.pdf"
        pdf_filepath = os.path.join(os.getcwd(), pdf_filename)
        config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")

        # Конвертация HTML в PDF
        pdfkit.from_string(html_output, pdf_filename, configuration=config)

        print("PDF-отчет успешно создан!")

        return pdf_filepath, pdf_filename, json.dumps(defects)