#!/usr/bin/env python3
"""
VulnApk Client Library
Easy integration of VulnApk scanner into existing Python services
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging
import tempfile

# Import VulnApk components
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vulnapk'))

from vulnapk.main import VulnApk
import vulnapk.logger as vulnapk_logger


class VulnApkClient:
    """
    Client class for integrating VulnApk into existing services
    Provides both synchronous and asynchronous interfaces
    """
    
    def __init__(
        self,
        temp_dir: Optional[str] = None,
        log_level: int = logging.INFO,
        max_workers: int = 3
    ):
        """
        Initialize VulnApk client
        
        Args:
            temp_dir: Directory for temporary files
            log_level: Logging level
            max_workers: Maximum concurrent analyses
        """
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "vulnapk_client"
        self.temp_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        
        # Initialize logging
        vulnapk_logger.init(log_level)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"VulnApk client initialized with temp_dir: {self.temp_dir}")
    
    def analyze_apk(
        self,
        apk_path: str,
        included_plugins: Optional[List[str]] = None,
        excluded_plugins: Optional[List[str]] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a single APK file synchronously
        
        Args:
            apk_path: Path to APK file
            included_plugins: List of plugins to include
            excluded_plugins: List of plugins to exclude
            output_dir: Directory to save reports
            
        Returns:
            Dictionary with analysis results
        """
        
        if not os.path.exists(apk_path):
            raise FileNotFoundError(f"APK file not found: {apk_path}")
        
        if not apk_path.endswith('.apk'):
            raise ValueError("File must have .apk extension")
        
        # Set output directory
        if not output_dir:
            output_dir = str(self.temp_dir / "reports")
        
        self.logger.info(f"Starting analysis of: {apk_path}")
        
        try:
            # Create VulnApk instance
            vulnapk = VulnApk(
                files=[apk_path],
                included_plugins=included_plugins,
                excluded_plugins=excluded_plugins,
                output_reports=output_dir
            )
            
            # Run analysis
            start_time = time.time()
            results = vulnapk.start()
            analysis_time = time.time() - start_time
            
            # Prepare response
            response = {
                'success': True,
                'apk_path': apk_path,
                'total_issues': len(results),
                'issues': results,
                'plugins_used': [p.__class__.__module__ for p in vulnapk.plugins],
                'analysis_time_seconds': round(analysis_time, 2),
                'output_directory': output_dir
            }
            
            self.logger.info(f"Analysis completed: {len(results)} issues found in {analysis_time:.2f}s")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'apk_path': apk_path
            }
    
    def analyze_multiple_apks(
        self,
        apk_paths: List[str],
        included_plugins: Optional[List[str]] = None,
        excluded_plugins: Optional[List[str]] = None,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple APK files synchronously
        
        Args:
            apk_paths: List of APK file paths
            included_plugins: List of plugins to include
            excluded_plugins: List of plugins to exclude
            output_dir: Directory to save reports
            
        Returns:
            List of analysis results
        """
        
        results = []
        
        for apk_path in apk_paths:
            try:
                result = self.analyze_apk(
                    apk_path=apk_path,
                    included_plugins=included_plugins,
                    excluded_plugins=excluded_plugins,
                    output_dir=output_dir
                )
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {apk_path}: {str(e)}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'apk_path': apk_path
                })
        
        return results
    
    def analyze_directory(
        self,
        directory_path: str,
        included_plugins: Optional[List[str]] = None,
        excluded_plugins: Optional[List[str]] = None,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze all APK files in a directory
        
        Args:
            directory_path: Directory containing APK files
            included_plugins: List of plugins to include
            excluded_plugins: List of plugins to exclude
            output_dir: Directory to save reports
            
        Returns:
            List of analysis results
        """
        
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Find all APK files
        apk_files = []
        for file in os.listdir(directory_path):
            if file.endswith('.apk'):
                apk_files.append(os.path.join(directory_path, file))
        
        if not apk_files:
            self.logger.warning(f"No APK files found in directory: {directory_path}")
            return []
        
        self.logger.info(f"Found {len(apk_files)} APK files in directory")
        
        return self.analyze_multiple_apks(
            apk_paths=apk_files,
            included_plugins=included_plugins,
            excluded_plugins=excluded_plugins,
            output_dir=output_dir
        )
    
    def analyze_package(
        self,
        package_name: str,
        included_plugins: Optional[List[str]] = None,
        excluded_plugins: Optional[List[str]] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download and analyze APK by package name
        
        Args:
            package_name: Android package name
            included_plugins: List of plugins to include
            excluded_plugins: List of plugins to exclude
            output_dir: Directory to save reports
            
        Returns:
            Dictionary with analysis results
        """
        
        if not output_dir:
            output_dir = str(self.temp_dir / "reports")
        
        self.logger.info(f"Starting analysis of package: {package_name}")
        
        try:
            # Create VulnApk instance
            vulnapk = VulnApk(
                packages=[package_name],
                included_plugins=included_plugins,
                excluded_plugins=excluded_plugins,
                output_reports=output_dir
            )
            
            # Run analysis
            start_time = time.time()
            results = vulnapk.start()
            analysis_time = time.time() - start_time
            
            # Prepare response
            response = {
                'success': True,
                'package_name': package_name,
                'total_issues': len(results),
                'issues': results,
                'plugins_used': [p.__class__.__module__ for p in vulnapk.plugins],
                'analysis_time_seconds': round(analysis_time, 2),
                'output_directory': output_dir
            }
            
            self.logger.info(f"Package analysis completed: {len(results)} issues found in {analysis_time:.2f}s")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Package analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'package_name': package_name
            }
    
    async def analyze_apk_async(
        self,
        apk_path: str,
        included_plugins: Optional[List[str]] = None,
        excluded_plugins: Optional[List[str]] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze APK file asynchronously
        
        Args:
            apk_path: Path to APK file
            included_plugins: List of plugins to include
            excluded_plugins: List of plugins to exclude
            output_dir: Directory to save reports
            
        Returns:
            Dictionary with analysis results
        """
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.analyze_apk,
            apk_path,
            included_plugins,
            excluded_plugins,
            output_dir
        )
    
    async def analyze_multiple_apks_async(
        self,
        apk_paths: List[str],
        included_plugins: Optional[List[str]] = None,
        excluded_plugins: Optional[List[str]] = None,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple APK files asynchronously
        
        Args:
            apk_paths: List of APK file paths
            included_plugins: List of plugins to include
            excluded_plugins: List of plugins to exclude
            output_dir: Directory to save reports
            
        Returns:
            List of analysis results
        """
        
        tasks = []
        for apk_path in apk_paths:
            task = self.analyze_apk_async(
                apk_path=apk_path,
                included_plugins=included_plugins,
                excluded_plugins=excluded_plugins,
                output_dir=output_dir
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_available_plugins(self) -> List[str]:
        """
        Get list of available security plugins
        
        Returns:
            List of plugin names
        """
        
        plugins_dir = Path(__file__).parent / "vulnapk" / "plugins"
        available_plugins = []
        
        if plugins_dir.exists():
            for plugin_file in plugins_dir.glob("*.py"):
                if plugin_file.name != "base_plugin.py":
                    available_plugins.append(plugin_file.stem)
        
        return available_plugins
    
    def validate_plugins(self, plugins: List[str]) -> Dict[str, bool]:
        """
        Validate if plugins exist
        
        Args:
            plugins: List of plugin names to validate
            
        Returns:
            Dictionary mapping plugin names to validation status
        """
        
        available_plugins = self.get_available_plugins()
        validation_results = {}
        
        for plugin in plugins:
            validation_results[plugin] = plugin in available_plugins
        
        return validation_results
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary files"""
        
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
                self.logger.info("Temporary files cleaned up")
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp files: {str(e)}")


# Convenience functions for quick integration
def quick_analyze(apk_path: str, plugins: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Quick analysis function for simple use cases
    
    Args:
        apk_path: Path to APK file
        plugins: List of plugins to run (None = all plugins)
        
    Returns:
        Analysis results
    """
    
    client = VulnApkClient()
    return client.analyze_apk(apk_path, included_plugins=plugins)


async def quick_analyze_async(apk_path: str, plugins: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Quick async analysis function
    
    Args:
        apk_path: Path to APK file
        plugins: List of plugins to run (None = all plugins)
        
    Returns:
        Analysis results
    """
    
    client = VulnApkClient()
    return await client.analyze_apk_async(apk_path, included_plugins=plugins)


def batch_analyze(apk_paths: List[str], plugins: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Batch analysis function for multiple APKs
    
    Args:
        apk_paths: List of APK file paths
        plugins: List of plugins to run (None = all plugins)
        
    Returns:
        List of analysis results
    """
    
    client = VulnApkClient()
    return client.analyze_multiple_apks(apk_paths, included_plugins=plugins)


# Example usage
if __name__ == "__main__":
    # Example 1: Simple analysis
    client = VulnApkClient()
    
    # Analyze single APK
    # result = client.analyze_apk("example.apk")
    # print(f"Found {result['total_issues']} security issues")
    
    # Example 2: Targeted analysis
    # result = client.analyze_apk(
    #     "example.apk",
    #     included_plugins=["hardcode_secrets", "unsafe_crypto"]
    # )
    
    # Example 3: Batch analysis
    # results = client.analyze_directory("/path/to/apk/directory")
    # for result in results:
    #     print(f"{result['apk_path']}: {result['total_issues']} issues")
    
    # Example 4: Package analysis
    # result = client.analyze_package("com.example.app")
    
    print("VulnApk Client ready for integration!")
    print(f"Available plugins: {client.get_available_plugins()}") 