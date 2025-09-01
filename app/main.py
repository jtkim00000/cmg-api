from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from .sympy_ollama_tutor import analyze_and_solve, ask_ollama_to_explain
from app.upload import router as upload_router

import subprocess
import json
import os

app = FastAPI(title="Math Tutor API", description="Solve math problems with SymPy + Ollama")

# Request body schema
class ProblemRequest(BaseModel):
    problem: str
    model: str = "gemma3"

# Response schema
class ProblemResponse(BaseModel):
    sympy_output: dict
    explanation: str

@app.post("/solve", response_model=ProblemResponse)
async def solve_problem(req: ProblemRequest):
    # Run SymPy solver
    sympy_out = analyze_and_solve(req.problem)

    # If error, return directly
    if "error" in sympy_out:
        return ProblemResponse(sympy_output=sympy_out, explanation="SymPy failed to solve the problem.")

    # Ask Ollama to explain
    explanation = ask_ollama_to_explain(req.problem, sympy_out, model=req.model)

    return ProblemResponse(sympy_output=sympy_out, explanation=explanation)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Save uploaded file temporarily
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Run ocr.py with the file path
    process = subprocess.Popen(
        ["python", "app/ocr.py", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()

    # Clean up temp file
    os.remove(file_path)

    if process.returncode != 0:
        return {"error": stderr.decode("utf-8")}

    try:
        result = json.loads(stdout.decode("utf-8"))
    except:
        return {"error": "Invalid JSON from OCR script", "raw": stdout.decode("utf-8")}

    return result
