#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple Python Version Checker for CredTech XScore
Compatible with Python 3.4
"""

import os
import sys
import subprocess
import platform

def print_header():
    """Print header information"""
    print("=" * 70)
    print("CredTech XScore - Python Environment Checker")
    print("=" * 70)
    print()

def check_current_python():
    """Check current Python version and capabilities"""
    print("1. Current Python Environment:")
    print("   Python Version: {}".format(sys.version))
    print("   Python Executable: {}".format(sys.executable))
    print("   Platform: {}".format(platform.platform()))
    print("   Architecture: {}".format(platform.architecture()))
    
    # Check Python features
    features = []
    try:
        # Check for f-string support (Python 3.6+)
        compile('f"test {1}"', '<string>', 'exec')
        features.append("f-strings")
    except SyntaxError:
        pass
    
    try:
        # Check for type hints (Python 3.5+)
        compile('def test(x: int) -> str: pass', '<string>', 'exec')
        features.append("type hints")
    except SyntaxError:
        pass
    
    try:
        # Check for dataclasses (Python 3.7+)
        compile('from dataclasses import dataclass', '<string>', 'exec')
        features.append("dataclasses")
    except SyntaxError:
        pass
    
    print("   Supported Features: {}".format(', '.join(features) if features else "Basic Python 3.4"))
    
    if "f-strings" in features:
        print("   OK: Compatible with enhanced features")
        return True
    else:
        print("   NOT OK: NOT compatible with enhanced features (requires Python 3.6+)")
        return False

def check_python_3_8_executable():
    """Check if the Python 3.8 executable works"""
    print("\n2. Checking Python 3.8 Executable:")
    
    python_38_path = "python-3.8.10.exe"
    if os.path.exists(python_38_path):
        print("   OK: Python 3.8.10 executable found")
        
        # Try to get version
        try:
            result = subprocess.run([python_38_path, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("   OK: Python 3.8.10 is working: {}".format(result.stdout.strip()))
                return True
            else:
                print("   NOT OK: Python 3.8.10 failed: {}".format(result.stderr.strip()))
                return False
        except subprocess.TimeoutExpired:
            print("   WARNING: Python 3.8.10 timed out (may need installation)")
            return False
        except Exception as e:
            print("   NOT OK: Error running Python 3.8.10: {}".format(e))
            return False
    else:
        print("   NOT OK: Python 3.8.10 executable not found")
        return False

def check_system_python():
    """Check for other Python installations on the system"""
    print("\n3. Checking System Python Installations:")
    
    # Common Python paths on Windows
    python_paths = [
        r"C:\Python38\python.exe",
        r"C:\Python39\python.exe",
        r"C:\Python310\python.exe",
        r"C:\Python311\python.exe",
        r"C:\Users\{}\AppData\Local\Programs\Python\Python38\python.exe".format(os.getenv('USERNAME', '')),
        r"C:\Users\{}\AppData\Local\Programs\Python\Python39\python.exe".format(os.getenv('USERNAME', '')),
        r"C:\Users\{}\AppData\Local\Programs\Python\Python310\python.exe".format(os.getenv('USERNAME', '')),
        r"C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe".format(os.getenv('USERNAME', '')),
    ]
    
    found_pythons = []
    for path in python_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run([path, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print("   OK: Found: {} - {}".format(path, version))
                    found_pythons.append((path, version))
                else:
                    print("   WARNING: Found but not working: {}".format(path))
            except Exception as e:
                print("   WARNING: Found but error: {} - {}".format(path, e))
    
    if not found_pythons:
        print("   NOT OK: No additional Python installations found")
        return False
    
    return found_pythons

def provide_installation_instructions():
    """Provide instructions for installing Python 3.6+"""
    print("\n4. Installation Instructions:")
    print("   To run the enhanced features, you need Python 3.6 or higher.")
    print("   Here are your options:")
    print()
    print("   Option A: Download from python.org")
    print("   - Visit: https://www.python.org/downloads/")
    print("   - Download Python 3.8, 3.9, or 3.10")
    print("   - Install with 'Add to PATH' checked")
    print()
    print("   Option B: Use Windows Store")
    print("   - Search for 'Python' in Windows Store")
    print("   - Install Python 3.8 or 3.9")
    print()
    print("   Option C: Use existing executable")
    print("   - The python-3.8.10.exe in this directory should work")
    print("   - May need to be installed first")
    print()
    print("   After installation, you can:")
    print("   - Install dependencies: pip install -r requirements.txt")
    print("   - Run enhanced features: python run_all.py")
    print("   - Run Streamlit app: streamlit run src/serve/app.py")

def test_enhanced_features():
    """Test if enhanced features can be imported"""
    print("\n5. Testing Enhanced Features:")
    
    try:
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Try to import enhanced modules
        try:
            import src.utils.enhanced_logging
            print("   OK: Enhanced logging module imported successfully")
        except Exception as e:
            print("   NOT OK: Enhanced logging import failed: {}".format(e))
        
        try:
            import src.utils.monitoring
            print("   OK: Monitoring module imported successfully")
        except Exception as e:
            print("   NOT OK: Monitoring import failed: {}".format(e))
        
        try:
            import src.config.dashboard_config
            print("   OK: Dashboard config imported successfully")
        except Exception as e:
            print("   NOT OK: Dashboard config import failed: {}".format(e))
        
        return True
        
    except Exception as e:
        print("   NOT OK: Enhanced features test failed: {}".format(e))
        return False

def main():
    """Main function"""
    print_header()
    
    # Run all checks
    current_ok = check_current_python()
    python38_ok = check_python_3_8_executable()
    system_pythons = check_system_python()
    
    # Test enhanced features
    enhanced_ok = test_enhanced_features()
    
    # Provide instructions
    provide_installation_instructions()
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    
    if current_ok:
        print("OK: Current Python is compatible with enhanced features!")
    else:
        print("NOT OK: Current Python 3.4 is NOT compatible with enhanced features")
    
    if python38_ok:
        print("OK: Python 3.8.10 executable is working")
    else:
        print("NOT OK: Python 3.8.10 executable needs installation")
    
    if system_pythons:
        print("OK: Found {} additional Python installation(s)".format(len(system_pythons)))
    else:
        print("NOT OK: No additional Python installations found")
    
    if enhanced_ok:
        print("OK: Enhanced features can be imported")
    else:
        print("NOT OK: Enhanced features cannot be imported (Python version issue)")
    
    print("\n" + "=" * 70)
    
    if current_ok or python38_ok or system_pythons:
        print("SUCCESS: You have options to run the enhanced features!")
    else:
        print("WARNING: You need to install Python 3.6+ to use enhanced features")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

