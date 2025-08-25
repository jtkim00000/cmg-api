from sympy import (
    symbols, simplify, diff, integrate, factor, expand,
    Eq, solveset, S
)
from app.parsing import parse_math
from app.models import SolveRequest, SolveResponse

def solve_task(req: SolveRequest) -> SolveResponse:
    try:
        expr, kind = parse_math(req.query)
        vars = [symbols(v) for v in (req.vars or ["x"])]

        result = None
        steps = []

        if req.task == "auto":
            if kind == "equation":
                result = list(solveset(expr, vars[0], domain=S.Complexes))
                task = "solve"
            else:
                result = simplify(expr)
                task = "simplify"

        elif req.task == "solve":
            if kind == "equation":
                result = list(solveset(expr, vars[0], domain=S.Complexes))
            else:
                result = list(solveset(Eq(expr, 0), vars[0], domain=S.Complexes))

        elif req.task == "simplify":
            result = simplify(expr)

        elif req.task == "differentiate":
            result = diff(expr, vars[0])

        elif req.task == "integrate":
            result = integrate(expr, vars[0])

        elif req.task == "factor":
            result = factor(expr)

        elif req.task == "expand":
            result = expand(expr)

        else:
            return SolveResponse(ok=False, task=req.task, detected={"kind": kind}, result=None,
                                 warnings=[f"Unknown task: {req.task}"])

        return SolveResponse(
            ok=True,
            task=req.task,
            detected={"kind": kind, "query": str(expr)},
            result=str(result),
            steps=steps
        )
    except Exception as e:
        return SolveResponse(ok=False, task=req.task, detected={}, result=None,
                             warnings=[str(e)])