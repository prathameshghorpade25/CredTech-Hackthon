#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Basic Demo Script for CredTech XScore
Compatible with Python 3.4
"""

import os
import sys
import json
import pandas as pd

def print_header():
    """Print a nice header"""
    print("=" * 60)
    print("CredTech XScore - Basic Demo")
    print("=" * 60)
    print()

def check_project_structure():
    """Check if the project structure is correct"""
    print("1. Checking Project Structure...")
    
    required_dirs = ['src', 'data', 'models', 'logs', 'tests', 'docs']
    missing_dirs = []
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print("   ✓ {} directory exists".format(dir_name))
        else:
            print("   ✗ {} directory missing".format(dir_name))
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print("   WARNING: {} directories are missing".format(len(missing_dirs)))
        return False
    else:
        print("   SUCCESS: All required directories exist")
        return True

def check_data_files():
    """Check if data files exist"""
    print("\n2. Checking Data Files...")
    
    data_files = [
        'data/raw/sample.csv',
        'data/processed/combined_data.csv',
        'data/processed/features.csv',
        'data/processed/news_data.csv'
    ]
    
    missing_files = []
    for file_path in data_files:
        if os.path.exists(file_path):
            print("   ✓ {} exists".format(file_path))
        else:
            print("   ✗ {} missing".format(file_path))
            missing_files.append(file_path)
    
    if missing_files:
        print("   WARNING: {} data files are missing".format(len(missing_files)))
        return False
    else:
        print("   SUCCESS: All data files exist")
        return True

def check_model_files():
    """Check if model files exist"""
    print("\n3. Checking Model Files...")
    
    model_files = [
        'models/model.joblib'
    ]
    
    missing_files = []
    for file_path in model_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print("   ✓ {} exists ({} bytes)".format(file_path, file_size))
        else:
            print("   ✗ {} missing".format(file_path))
            missing_files.append(file_path)
    
    if missing_files:
        print("   WARNING: {} model files are missing".format(len(missing_files)))
        return False
    else:
        print("   SUCCESS: All model files exist")
        return True

def check_documentation():
    """Check if documentation exists"""
    print("\n4. Checking Documentation...")
    
    doc_files = [
        'README.md',
        'ENHANCEMENTS_SUMMARY.md',
        'CONTRIBUTING.md',
        'model_card.md'
    ]
    
    missing_files = []
    for file_path in doc_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print("   ✓ {} exists ({} bytes)".format(file_path, file_size))
        else:
            print("   ✗ {} missing".format(file_path))
            missing_files.append(file_path)
    
    if missing_files:
        print("   WARNING: {} documentation files are missing".format(len(missing_files)))
        return False
    else:
        print("   SUCCESS: All documentation files exist")
        return True

def show_sample_data():
    """Show sample data from the processed files"""
    print("\n5. Sample Data Preview...")
    
    try:
        # Show combined data
        if os.path.exists('data/processed/combined_data.csv'):
            print("   Combined Data (first 3 rows):")
            df = pd.read_csv('data/processed/combined_data.csv')
            print("   Shape: {} rows, {} columns".format(df.shape[0], df.shape[1]))
            print("   Columns: {}".format(', '.join(df.columns.tolist())))
            print("   First 3 rows:")
            print(df.head(3).to_string())
        
        # Show features data
        if os.path.exists('data/processed/features.csv'):
            print("\n   Features Data (first 3 rows):")
            df = pd.read_csv('data/processed/features.csv')
            print("   Shape: {} rows, {} columns".format(df.shape[0], df.shape[1]))
            print("   Columns: {}".format(', '.join(df.columns.tolist())))
            print("   First 3 rows:")
            print(df.head(3).to_string())
            
        return True
        
    except Exception as e:
        print("   ERROR: Could not read sample data: {}".format(e))
        return False

def show_project_info():
    """Show project information"""
    print("\n6. Project Information...")
    
    try:
        # Read README
        if os.path.exists('README.md'):
            with open('README.md', 'r') as f:
                content = f.read()
            
            # Extract project description
            lines = content.split('\n')
            for line in lines:
                if line.startswith('## Overview') or line.startswith('## Description'):
                    print("   Project: CredTech XScore - Explainable Credit Scoring")
                    break
        
        # Show file counts
        total_files = 0
        for root, dirs, files in os.walk('.'):
            total_files += len(files)
        
        print("   Total files in project: {}".format(total_files))
        print("   Project size: {} bytes".format(sum(os.path.getsize(os.path.join(root, name)) 
                                                   for root, dirs, files in os.walk('.') 
                                                   for name in files)))
        
        return True
        
    except Exception as e:
        print("   ERROR: Could not read project info: {}".format(e))
        return False

def show_enhancements_summary():
    """Show a summary of the enhancements"""
    print("\n7. Enhancements Summary...")
    
    try:
        if os.path.exists('ENHANCEMENTS_SUMMARY.md'):
            with open('ENHANCEMENTS_SUMMARY.md', 'r') as f:
                content = f.read()
            
            # Extract key points
            lines = content.split('\n')
            enhancement_count = 0
            for line in lines:
                if line.startswith('### '):
                    enhancement_count += 1
                    if enhancement_count <= 5:  # Show first 5 enhancements
                        print("   {}".format(line.strip()))
            
            print("   Total enhancements implemented: {}".format(enhancement_count))
            print("   NOTE: Enhanced features require Python 3.6+")
            
        return True
        
    except Exception as e:
        print("   ERROR: Could not read enhancements summary: {}".format(e))
        return False

def main():
    """Main demo function"""
    print_header()
    
    # Run all checks
    checks = [
        ("Project Structure", check_project_structure),
        ("Data Files", check_data_files),
        ("Model Files", check_model_files),
        ("Documentation", check_documentation),
        ("Sample Data", show_sample_data),
        ("Project Info", show_project_info),
        ("Enhancements", show_enhancements_summary)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print("   ERROR: {} failed with exception: {}".format(check_name, e))
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Demo Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "PASS" if result else "FAIL"
        print("{:<20} {}".format(check_name, status))
        if result:
            passed += 1
    
    print("\nOverall: {}/{} checks passed".format(passed, total))
    
    if passed == total:
        print("\n🎉 SUCCESS: All checks passed! The project is ready.")
        print("\nTo run the enhanced features, you need:")
        print("  - Python 3.6 or higher")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Run: python run_all.py")
        print("  - Streamlit app: streamlit run src/serve/app.py")
    else:
        print("\n⚠️  WARNING: Some checks failed. Check the output above.")
    
    print("\n" + "=" * 60)
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
