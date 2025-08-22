#!/usr/bin/env python3
"""
Simple startup script for the Job Automation System.
"""

def main():
    print("Job Automation System - Startup Menu")
    print("=" * 40)
    print()
    print("Available commands:")
    print("1. python cli.py init")
    print("2. python cli.py fetch")
    print("3. python cli.py post")
    print("4. python cli.py list-jobs")
    print("5. python cli.py list-posts")
    print("6. python cli.py analytics")
    print("7. python cli.py status")
    print("8. python test_system.py")
    print("9. python test_gemini.py")
    print()
    print("To start the system, run: python cli.py init")
    print("Then fetch jobs: python cli.py fetch")
    print("Then post to LinkedIn: python cli.py post")

if __name__ == "__main__":
    main()
