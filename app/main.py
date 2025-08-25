from fastapi import FastAPI
from app.models import SolveRequest, SolveResponse
from app.solver import solve_task
from app.parsing import parse_and_solve

app = FastAPI(title="Math Solver API", version="0.1.0")

@app.post("/solve")
def solve_math(payload: dict):
    query = payload.get("query")
    task = payload.get("task", "solve")

    result = parse_and_solve(query)

    return {"task": task, **result}
#uvicorn app.main:app --reload