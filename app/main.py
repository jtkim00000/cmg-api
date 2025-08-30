from fastapi import FastAPI
from pydantic import BaseModel
from .sympy_ollama_tutor import analyze_and_solve, ask_ollama_to_explain

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
