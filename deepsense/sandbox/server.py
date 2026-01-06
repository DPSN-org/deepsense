"""
Sandbox server for executing code in isolated Docker containers.
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
import uuid
import os
import subprocess
import json

app = FastAPI()

BASE_DIR = "/tmp/exec_sandbox"
os.makedirs(BASE_DIR, exist_ok=True)

class ScriptRequest(BaseModel):
    code: str
    requirements: list[str] = []
    language: str = "python"  # or "node"

@app.post("/run")
def run_script(body: ScriptRequest):
    uid = str(uuid.uuid4())
    script_dir = os.path.join(BASE_DIR, uid)
    os.makedirs(script_dir, exist_ok=True)
    
    # Set permissions so the sandbox user can write to the directory
    os.chmod(script_dir, 0o777)

    with open(os.path.join(script_dir, "meta.json"), "w") as f:
        json.dump(body.dict(), f)

    if body.language == "node":
        image = "sandbox-node"
        runner = "runner.js"
    else:
        image = "sandbox-python"
        runner = "runner.py"

    result = subprocess.run([
        "docker", "run", "--rm",
        "--memory=256m", "--cpus=0.5",
        "-v", f"{script_dir}:/home/sandbox/script",
        image
    ], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    return {"stdout": result.stdout, "stderr": result.stderr}

