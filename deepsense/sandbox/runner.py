"""
Python runner for sandbox execution.
"""

import subprocess
import sys
import json

with open("script/meta.json") as f:
    meta = json.load(f)

code = meta.get("code", "")
reqs = meta.get("requirements", [])

# Install packages with suppressed warnings
if reqs:
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "--quiet", "--no-warn-script-location", "--disable-pip-version-check"
    ] + reqs, capture_output=True)

# Write code to file
with open("script/user_script.py", "w") as f:
    f.write(code)

# Execute code
result = subprocess.run(["python", "script/user_script.py"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr, file=sys.stderr)

