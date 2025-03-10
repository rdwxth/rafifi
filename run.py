import subprocess

subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

import sys
import time
import webbrowser
import os

def run_backend():
    print("Starting backend server...")
    backend_process = subprocess.Popen(
        [sys.executable, "backend/app.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    # Wait for server to start
    time.sleep(2)
    return backend_process

def run_frontend():
    print("Starting frontend application...")
    frontend_process = subprocess.Popen(
        [sys.executable, "frontend/main.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    return frontend_process

def main():
    # First, initialize the database with sample data
    print("Initializing database with sample data...")
    subprocess.run(
        [sys.executable, "backend/init_db.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    # Start backend
    backend_process = run_backend()

    # Start frontend
    frontend_process = run_frontend()

    print("\nRevision App is running!")
    print("Sample login credentials:")
    print("Username: student1")
    print("Password: password123")
    
    try:
        # Wait for processes to complete
        frontend_process.wait()
    finally:
        # Clean up processes
        print("\nShutting down...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    main()
