#!/usr/bin/env python3
"""
Test runner for CSV import/export functionality
Runs comprehensive tests for MaterialCSVService and API endpoints
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run CSV tests with proper environment setup"""
    
    # Ensure we're in the project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Add project root to Python path
    sys.path.insert(0, str(project_root))
    
    print("🧪 Running CSV Import/Export Tests")
    print("=" * 50)
    
    # Test files to run
    test_files = [
        "tests/test_material_csv_service.py",
        "tests/test_csv_api_endpoints.py", 
        "tests/test_csv_validation_security.py"
    ]
    
    # Check if test files exist
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print(f"❌ Missing test files: {', '.join(missing_files)}")
        return 1
    
    # Install required test dependencies if needed
    try:
        import pytest
        import fastapi.testclient
    except ImportError:
        print("📦 Installing test dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "httpx"], check=True)
    
    # Run tests with different configurations
    test_configs = [
        {
            "name": "Unit Tests - MaterialCSVService",
            "files": ["tests/test_material_csv_service.py"],
            "markers": "unit"
        },
        {
            "name": "Integration Tests - API Endpoints", 
            "files": ["tests/test_csv_api_endpoints.py"],
            "markers": "integration"
        },
        {
            "name": "Security Tests - Validation & Security",
            "files": ["tests/test_csv_validation_security.py"],
            "markers": "security"
        },
        {
            "name": "Complete Test Suite",
            "files": test_files,
            "markers": "csv"
        }
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n🔍 Running: {config['name']}")
        print("-" * 40)
        
        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            "-v",
            "--tb=short",
            "--color=yes",
            "-x",  # Stop on first failure for cleaner output
        ]
        
        # Add marker if specified
        if config.get("markers"):
            cmd.extend(["-m", config["markers"]])
        
        # Add test files
        cmd.extend(config["files"])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ {config['name']}: PASSED")
                passed_tests = result.stdout.count(" PASSED")
                print(f"   {passed_tests} tests passed")
            else:
                print(f"❌ {config['name']}: FAILED")
                failed_tests = result.stdout.count(" FAILED")
                error_tests = result.stdout.count(" ERROR")
                print(f"   {failed_tests} failed, {error_tests} errors")
                
                # Show first few lines of failure output
                if result.stdout:
                    lines = result.stdout.split('\n')
                    failure_lines = [line for line in lines if 'FAILED' in line or 'ERROR' in line]
                    for line in failure_lines[:3]:  # Show first 3 failures
                        print(f"   {line}")
            
            results.append({
                "name": config["name"],
                "passed": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            })
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {config['name']}: TIMEOUT (exceeded 5 minutes)")
            results.append({
                "name": config["name"],
                "passed": False,
                "output": "",
                "errors": "Test timeout"
            })
        except Exception as e:
            print(f"💥 {config['name']}: ERROR - {str(e)}")
            results.append({
                "name": config["name"],
                "passed": False,
                "output": "",
                "errors": str(e)
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    
    for result in results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} - {result['name']}")
    
    print(f"\n🎯 Overall: {passed_count}/{total_count} test suites passed")
    
    # Detailed failure report
    failed_results = [r for r in results if not r["passed"]]
    if failed_results:
        print("\n" + "=" * 50)
        print("🔍 FAILURE DETAILS")
        print("=" * 50)
        
        for result in failed_results:
            print(f"\n❌ {result['name']}")
            print("-" * 30)
            if result["errors"]:
                print("ERRORS:")
                print(result["errors"])
            if result["output"]:
                # Show relevant parts of output
                lines = result["output"].split('\n')
                relevant_lines = []
                for line in lines:
                    if any(keyword in line.upper() for keyword in ['FAILED', 'ERROR', 'ASSERTION', 'EXCEPTION']):
                        relevant_lines.append(line)
                
                if relevant_lines:
                    print("OUTPUT:")
                    for line in relevant_lines[:10]:  # Show first 10 relevant lines
                        print(f"  {line}")
    
    # Exit with appropriate code
    return 0 if passed_count == total_count else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)