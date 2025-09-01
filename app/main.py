from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from .sympy_ollama_tutor import analyze_and_solve, ask_ollama_to_explain
from app.upload import router as upload_router
from app.ocr_solver import process_image

import tempfile
import shutil

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
async def upload_image(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        result = process_image(tmp_path)

        if not result.get("raw") or not result.get("cleaned"):
            raise HTTPException(status_code=422, detail="OCR failed to extract meaningful text.")

        return result

    except HTTPException as e:
        raise e 
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )
    
    #uvicorn app.main:app --reload --port 8000

