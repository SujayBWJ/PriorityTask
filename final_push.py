import subprocess
import os

def final_push():
    cwd = r"c:\Users\sujay\OneDrive\Desktop\Project - Skill Classes"
    
    # 1. Fetch
    subprocess.run(["git", "fetch", "origin"], cwd=cwd)
    
    # 2. Rebase
    rebase = subprocess.run(["git", "rebase", "origin/main"], cwd=cwd, capture_output=True, text=True)
    print(f"REBASE STDOUT: {rebase.stdout}")
    print(f"REBASE STDERR: {rebase.stderr}")
    
    # 3. Push
    push = subprocess.run(["git", "push", "origin", "main"], cwd=cwd, capture_output=True, text=True)
    print(f"PUSH STDOUT: {push.stdout}")
    print(f"PUSH STDERR: {push.stderr}")

if __name__ == "__main__":
    final_push()
