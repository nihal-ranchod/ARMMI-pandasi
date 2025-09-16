#!/usr/bin/env python3
import os
import subprocess
import sys

def main():
    port = os.environ.get('PORT', '5000')
    cmd = ['gunicorn', 'app:app', '--bind', f'0.0.0.0:{port}']

    print(f"Starting server on port {port}")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.exec(cmd)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()