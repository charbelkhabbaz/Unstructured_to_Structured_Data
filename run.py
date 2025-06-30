#!/usr/bin/env python3
"""
AI Data Structuring Platform - Startup Script
This script checks dependencies and launches the application with proper error handling.
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        'streamlit',
        'requests',
        'pdfplumber',
        'pytesseract',
        'PIL',
        'pandas',
        'openpyxl',
        'psutil',
        'urllib3'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            else:
                importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages with: pip install -r requirements.txt")
        return False
    
    return True

def check_tesseract():
    """Check if Tesseract OCR is installed."""
    try:
        import pytesseract
        # Try to get tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract OCR: {version}")
        return True
    except Exception as e:
        print("❌ Tesseract OCR not found or not properly configured")
        print("Please install Tesseract OCR:")
        print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("  macOS: brew install tesseract")
        print("  Linux: sudo apt-get install tesseract-ocr")
        return False

def check_config():
    """Check if configuration is properly set up."""
    config_file = Path('.env')
    if not config_file.exists():
        print("⚠️  .env file not found")
        print("Please create a .env file with your OpenRouter API key:")
        print("OPENROUTER_API_KEY=your_api_key_here")
        return False
    
    # Check if API key is set
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print("❌ OPENROUTER_API_KEY not found in .env file")
            return False
        print("✅ OpenRouter API key configured")
        return True
    except ImportError:
        print("❌ python-dotenv not installed")
        return False

def install_missing_packages():
    """Install missing packages."""
    print("\n🔧 Installing missing packages...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Packages installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages")
        return False

def launch_application():
    """Launch the Streamlit application."""
    print("\n🚀 Launching AI Data Structuring Platform...")
    try:
        # Start performance monitoring
        from performance_monitor import performance_monitor
        performance_monitor.start_system_monitoring()
        print("✅ Performance monitoring started")
        
        # Launch Streamlit
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app.py'])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error launching application: {e}")
    finally:
        # Stop performance monitoring
        try:
            from performance_monitor import performance_monitor
            performance_monitor.stop_system_monitoring()
        except:
            pass

def main():
    """Main startup function."""
    print("🚀 AI Data Structuring Platform - Startup Check")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        print("\nWould you like to install missing packages? (y/n): ", end="")
        if input().lower() == 'y':
            if not install_missing_packages():
                sys.exit(1)
        else:
            sys.exit(1)
    
    print("\n🔍 Checking Tesseract OCR...")
    if not check_tesseract():
        print("\n⚠️  Tesseract OCR is required for image processing")
        print("You can still use the application for PDF and text files")
    
    print("\n⚙️  Checking configuration...")
    if not check_config():
        print("\n⚠️  Configuration issues detected")
        print("You can still run the application, but AI features may not work")
    
    print("\n" + "=" * 50)
    print("✅ All checks completed!")
    
    # Launch the application
    launch_application()

if __name__ == "__main__":
    main() 