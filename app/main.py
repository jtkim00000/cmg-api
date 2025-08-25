from fastapi import FastAPI
from app.models import SolveRequest, SolveResponse
from app.solver import solve_task

app = FastAPI(title="Math Solver API", version="0.1.0")

@app.post("/solve", response_model=SolveResponse)
async def solve(req: SolveRequest):
    return solve_task(req)