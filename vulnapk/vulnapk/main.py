import argparse
import concurrent.futures
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from importlib import util as importutil
from typing import Any

import logger
import smalivm
import tqdm
from apk import Apk
from bs4 import Tag
from logger import logd, loge, logi
from plugins.base_plugin import BasePlugin, Problem


class VulnApk:
    plugins: list[BasePlugin]

    def __init__(
        self,
        included_plugins: list[str] | None = None,
        excluded_plugins: list[str] | None = None,
        files: list[str] | str | None = None,
        packages: list[str] | str | None = None,
        directories: list[str] | str | None = None,
        lists: list[str] | str | None = None,
        output_reports: str | None = None,
    ) -> None:
        self.plugins = []
        self.__load_plugins(included_plugins, excluded_plugins)
        self.output_reports = output_reports
        self.files: list[str] = []
        self.packages: list[str] = []

        # Handle packages parameter (can be string or list)
        if packages:
            if isinstance(packages, str):
                self.packages.append(packages)
            else:
                self.packages.extend(packages)

        # Handle files parameter (can be string or list)
        if files:
            file_list = [files] if isinstance(files, str) else files
            for file in file_list:
                apk_file = os.path.abspath(file)
                if not os.path.exists(apk_file):
                    raise ValueError(f"APK file not found at {apk_file}")
                self.files.append(apk_file)

        # Handle lists parameter (can be string or list)
        if lists:
            list_files = [lists] if isinstance(lists, str) else lists
            for list_file in list_files:
                with open(list_file) as f:
                    for line in f:
                        self.packages.append(line.strip())

        # Handle directories parameter (can be string or list)
        if directories:
            dir_list = [directories] if isinstance(directories, str) else directories
            for directory in dir_list:
                for file in os.listdir(directory):
                    if not file.endswith(".apk"):
                        raise ValueError(f"Non-APK file {file}")
                    self.files.append(os.path.join(directory, file))

        if not self.files and not self.packages:
            raise ValueError(
                "At least one of files, packages, directories, or lists must be provided."
            )

    def start(self) -> list[dict[str, Any]]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures: list[concurrent.futures.Future[list[dict[str, Any]]]] = []
            for apk_file in self.files:
                futures.append(executor.submit(self.__process_apk, apk_file))
            for pkg in self.packages:
                futures.append(executor.submit(self.__download_and_process_apk, pkg))

            results: list[dict[str, Any]] = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.extend(result)

            return results

    def __load_plugins(
        self,
        included_plugins: list[str] | None = None,
        excluded_plugins: list[str] | None = None,
    ) -> None:
        plugin_folder = os.path.join(os.path.dirname(__file__), "plugins")
        for file in os.listdir(plugin_folder):
            if not file.endswith(".py"):
                continue
            module_name = file[:-3]
            if module_name == "base_plugin":
                continue
            if included_plugins and module_name not in included_plugins:
                logd(f"Skipping plugin {module_name} as it's not included")
                continue
            elif excluded_plugins and module_name in excluded_plugins:
                logd(f"Skipping plugin {module_name} as it's excluded")
                continue

            module_path = os.path.join(plugin_folder, file)
            spec = importutil.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                loge(f"Failed to load plugin {module_name}")
                continue
            module = importutil.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not module.Plugin.enabled:
                logd(f"Skipping disabled plugin {module_name}")
                continue
            self.plugins.append(module.Plugin())

    def __download_and_process_apk(self, pkg: str) -> list[dict[str, Any]]:
        with tempfile.NamedTemporaryFile() as apk_file:
            # Get absolute path to apkd executable - same directory as apkeditor.jar
            current_dir = os.path.dirname(os.path.abspath(__file__))
            apkd_name = "apkd.exe" if os.name == "nt" else "apkd"
            apkd_path = os.path.join(current_dir, "..", "..", apkd_name)
            apkd_path = os.path.abspath(apkd_path)
            
            if not os.path.exists(apkd_path):
                raise FileNotFoundError(f"{apkd_name} not found at {apkd_path}")
            
            proc = subprocess.run(
                [
                    apkd_path,
                    "-p",
                    pkg,
                    "-o",
                    apk_file.name,
                    "-F",
                ]
            )
            if proc.returncode != 0:
                return []
            with tempfile.TemporaryDirectory() as apk_dir:
                self.__decompile_apk(apk_file.name, apk_dir)
                return self.__analyze_apk(
                    apk_dir,
                )

    def __process_apk(self, apk_file: str) -> list[dict[str, Any]]:
        with tempfile.TemporaryDirectory() as apk_dir:
            self.__decompile_apk(apk_file, apk_dir)
            return self.__analyze_apk(apk_dir)

    def __decompile_apk(self, apk: str, apk_dir: str) -> None:
        logi(f"Decompiling APK: {apk} to {apk_dir}")
        
        # Get absolute path to apkeditor.jar - go up two levels from this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        apkeditor_path = os.path.join(current_dir, "..", "apkeditor.jar")
        apkeditor_path = os.path.abspath(apkeditor_path)

        print(apkeditor_path)
        
        if not os.path.exists(apkeditor_path):
            raise FileNotFoundError(f"apkeditor.jar not found at {apkeditor_path}")
        
        command = f"java -jar {apkeditor_path} d -i {apk} -f -o {apk_dir}"
        subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def __analyze_apk(self, apk_dir: str) -> list[dict[str, Any]]:
        problems_json: list[dict[str, Any]] = []
        apk = Apk(apk_dir)
        apk_info = ""
        start_time = time.strftime("%Y%m%d-%H%M%S")
        manifest = apk.get_manifest()
        if manifest:
            manifest_tag = manifest.find("manifest")
            if isinstance(manifest_tag, Tag):
                pkg_tag = manifest_tag.get("package")
                if not isinstance(pkg_tag, str):
                    raise RuntimeError(
                        f"Package tag is not a string in the app {apk_dir}"
                    )
                version_code = manifest_tag.get("android:versionCode")
                version_name = manifest_tag.get("android:versionName")
                apk_info = f"{pkg_tag}_v{version_name}_{version_code}"
        if not apk_info:
            return problems_json
        smali_dir = apk.get_smali_dir()
        logi("Creating smali VM")
        vm = smalivm.Vm(smali_dir)
        problems: set[Problem] = set()
        for plugin in self.plugins:
            plugin.on_start(apk, vm)
        bar = tqdm.tqdm(
            unit="B",
            unit_scale=True,
            bar_format="{l_bar}{bar}{r_bar}",
            desc=f"Analyzing {apk_info}",
        )
        bar.reset(vm.class_count())
        bar.set_description(f"Analyzing {apk_info}")

        for cls in vm.iter_classes():
            bar.update(1)
            bar.set_description(f"Analyzing {apk_info}")
            if cls.is_framework():
                continue
            for plugin in self.plugins:
                plugin.on_class(vm, cls)
                vm.run_all_methods(cls)
                if len(plugin.problems) > 0:
                    problems.update(plugin.problems)
                    plugin.problems.clear()

        problems_json.extend([problem.get_data() for problem in problems])

        if self.output_reports:
            report_name = f"{apk_info}_{start_time}_report.json"
            report_path = os.path.join(self.output_reports, report_name)
            if not os.path.exists(self.output_reports):
                os.makedirs(self.output_reports)

            with open(report_path, "w") as f:
                f.write(json.dumps(problems_json, indent=4, ensure_ascii=True))

        return problems_json


def cli() -> None:
    logger.init(logging.INFO)

    arg_parser = argparse.ArgumentParser(
        description="VulnAPK - Static Analysis Tool for Android Applications"
    )
    arg_parser.add_argument(
        "--include-plugin", help="Include plugin", action="append", default=[]
    )
    arg_parser.add_argument(
        "--exclude-plugin", help="Exclude plugin", action="append", default=[]
    )
    arg_parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="APK file to analyze",
        action="append",
        dest="files",
        default=[],
    )
    arg_parser.add_argument(
        "-p",
        "--package",
        type=str,
        help="Package name of the APK to download",
        action="append",
        dest="packages",
        default=[],
    )
    arg_parser.add_argument(
        "-d",
        "--directory",
        type=str,
        help="Folder with APK files",
        action="append",
        default=[],
        dest="directories",
    )
    arg_parser.add_argument(
        "-l",
        "--list",
        type=str,
        help="File with list of packages to download (one per line)",
        action="append",
        default=[],
        dest="lists",
    )
    arg_parser.add_argument(
        "-o", "--output-reports", type=str, help="Output reports directory", default="."
    )
    if len(sys.argv) <= 1:
        arg_parser.print_help()
        sys.exit(1)

    args = arg_parser.parse_args(sys.argv[1:])
    vulnapk = VulnApk(
        included_plugins=args.include_plugin,
        excluded_plugins=args.exclude_plugin,
        packages=args.packages,
        files=args.files,
        directories=args.directories,
        output_reports=args.output_reports,
    )
    logi(f"Loaded {len(vulnapk.plugins)} plugin(s):")
    for plugin in vulnapk.plugins:
        logi(f"  - {plugin.__class__.__module__}")
    vulnapk.start()


if __name__ == "__main__":
    cli()
