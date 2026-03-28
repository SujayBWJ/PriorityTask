import subprocess
import os

def run_git_operations():
    cwd = r"c:\Users\sujay\OneDrive\Desktop\Project - Skill Classes"
    
    commands = [
        ["git", "config", "user.email", "sujaybharadwaj.dev@gmail.com"],
        ["git", "config", "user.name", "SujayBWJ"],
        ["git", "add", "."],
        ["git", "commit", "-m", "Implement Task Graveyard, Responsive UI, and Bug Fixes"],
        ["git", "push", "origin", "main"]
    ]
    
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        print(f"Exit Code: {result.returncode}")
        print("-" * 20)

if __name__ == "__main__":
    run_git_operations()
