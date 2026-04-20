#!/usr/bin/env python3
"""Script untuk menjalankan semua automation tests"""

import subprocess
import sys
import os
import time
from datetime import datetime

def run_command(command, description):
    """Menjalankan command shell dan print output"""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("ERROR:", result.stderr)
    
    return result.returncode == 0

def main():
    print("🚀 TaskFlow Automation Testing Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Buat folder reports jika belum ada
    os.makedirs("reports", exist_ok=True)
    
    all_passed = True
    
    # 1. Jalankan API Tests dengan Newman
    print("\n📡 Running Backend API Tests...")
    api_passed = run_command(
        "newman run tests/postman/TaskFlow_API_Collection.json -e tests/postman/TaskFlow_Local_Environment.json --reporters cli,htmlextra --reporter-htmlextra-export reports/api-test-report.html",
        "Backend API Tests"
    )
    all_passed = all_passed and api_passed
    
    # 2. Jalankan Frontend Selenium Tests
    print("\n🖥️ Running Frontend Selenium Tests...")
    frontend_passed = run_command(
        "cd tests/selenium && pytest test_frontend.py -v --html=../../reports/frontend-test-report.html --self-contained-html",
        "Frontend Selenium Tests"
    )
    all_passed = all_passed and frontend_passed
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Backend API Tests:  {'✅ PASSED' if api_passed else '❌ FAILED'}")
    print(f"Frontend UI Tests:  {'✅ PASSED' if frontend_passed else '❌ FAILED'}")
    print(f"{'='*60}")
    print(f"Overall Result:     {'✅ ALL PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()