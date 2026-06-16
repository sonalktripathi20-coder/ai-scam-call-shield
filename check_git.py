import subprocess

try:
    res = subprocess.run(["git", "status"], capture_output=True, text=True, shell=True)
    status_out = res.stdout + "\n" + res.stderr
except Exception as e:
    status_out = str(e)

try:
    res = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True, shell=True)
    diff_out = res.stdout + "\n" + res.stderr
except Exception as e:
    diff_out = str(e)

with open("git_output.txt", "w", encoding="utf-8") as f:
    f.write("=== GIT STATUS ===\n")
    f.write(status_out)
    f.write("\n=== GIT DIFF ===\n")
    f.write(diff_out)

print("Done writing git output")
