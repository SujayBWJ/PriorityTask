import subprocess
import os

def final_push():
    cwd = r"c:\Users\sujay\OneDrive\Desktop\Project - Skill Classes"
    log_file = os.path.join(cwd, "push_results.txt")
    
    with open(log_file, "w") as f:
        # 1. Fetch
        f.write("--- FETCH ---\n")
        subprocess.run(["git", "fetch", "origin"], cwd=cwd, stdout=f, stderr=f)
        
        # 2. Rebase
        f.write("\n--- REBASE ---\n")
        subprocess.run(["git", "rebase", "origin/main"], cwd=cwd, stdout=f, stderr=f)
        
        # 3. Push
        f.write("\n--- PUSH ---\n")
        subprocess.run(["git", "push", "origin", "main"], cwd=cwd, stdout=f, stderr=f)

if __name__ == "__main__":
    final_push()
