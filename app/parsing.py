from __future__ import annotations
import re
from sympy import Eq
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    convert_xor,
    implicit_multiplication_application,
    function_exponentiation,
)
from sympy import sin, cos, tan, asin, acos, atan, sqrt, log, exp, pi, E, I, Abs
from sympy import sympify, Eq, solve

def parse_and_solve(query: str, task: str = "auto"):
    try:
        # --- differentiate explicitly if requested ---
        if task == "differentiate":
            # Expect "expr" or allow "expr, var"
            if "," in query:
                raw_expr, raw_var = query.split(",", 1)
                var = symbols(raw_var.strip())
                expr = sympify(raw_expr.strip())
            else:
                var = symbols("x")
                expr = sympify(query)

            steps = explain_derivative(expr, var)
            result = simplify(diff(expr, var))
            return {
                "ok": True,
                "detected": {"kind": "derivative", "var": str(var)},
                "result": str(result),
                "steps": steps,
                "warnings": []
            }

        # --- equation if "=" present OR task == "solve" ---
        if "=" in query or task == "solve":
            if "=" in query:
                lhs, rhs = query.split("=", 1)
                lhs_expr = sympify(lhs.strip())
                rhs_expr = sympify(rhs.strip())
                eq = Eq(lhs_expr, rhs_expr)
            else:
                # treat expression == 0
                expr = sympify(query)
                eq = Eq(expr, 0)

            # pick a variable (default x)
            free = sorted(list(eq.free_symbols), key=lambda s: s.name)
            var = free[0] if free else symbols("x")

            steps = []
            # try to classify degree
            try:
                deg = Poly(eq.lhs - eq.rhs, var).degree()
            except Exception:
                deg = None

            if deg == 1:
                steps = explain_linear(eq, var)
            elif deg == 2:
                steps = explain_quadratic(eq, var)
            else:
                steps = ["Solve symbolically and simplify."]

            sol = solve(eq, var)
            return {
                "ok": True,
                "detected": {"kind": "equation", "var": str(var), "degree": deg},
                "result": [str(s) for s in (sol if isinstance(sol, (list, tuple)) else [sol])],
                "steps": steps,
                "warnings": []
            }

        # --- otherwise: treat as expression → simplify ---
        expr = sympify(query)
        result = simplify(expr)
        return {
            "ok": True,
            "detected": {"kind": "expression"},
            "result": str(result),
            "steps": ["Simplify the expression."],
            "warnings": []
        }

    except Exception as e:
        return {
            "ok": False,
            "detected": {},
            "result": None,
            "steps": [],
            "warnings": [str(e)]
        }


# Allowed names (kept intentionally small; extend as needed)
ALLOWED_FUNCS = {
    "sin": sin, "cos": cos, "tan": tan,
    "asin": asin, "acos": acos, "atan": atan,
    "sqrt": sqrt, "log": log, "exp": exp,
    "pi": pi, "E": E, "I": I, "Abs": Abs,
    "ln": log,
}

TRANSFORMS = standard_transformations + (
    convert_xor,                           # allow ^ as power
    implicit_multiplication_application,   # 2x -> 2*x
    function_exponentiation,               # sin^2(x) -> (sin(x))**2
)

UNICODE_MAP = {
    "×": "*", "·": "*", "∙": "*",
    "÷": "/",
    "−": "-", "—": "-",
    "√": "sqrt",
    "π": "pi",
}

def normalize_text(s: str) -> str:
    s = s.strip()
    for k, v in UNICODE_MAP.items():
        s = s.replace(k, v)
    # Insert * between number and symbol if missing: 5x -> 5*x
    s = re.sub(r"(?<=\d)(?=[A-Za-z(])", "*", s)
    s = s.replace("==", "=")
    return s

def parse_math(text: str):
    # Returns (kind, obj) where kind is 'equation' or 'expression'.
    s = normalize_text(text)
    if "=" in s:
        lhs, rhs = s.split("=", 1)
        lhs_expr = parse_expr(lhs, transformations=TRANSFORMS, local_dict=ALLOWED_FUNCS, evaluate=False)
        rhs_expr = parse_expr(rhs, transformations=TRANSFORMS, local_dict=ALLOWED_FUNCS, evaluate=False)
        return "equation", Eq(lhs_expr, rhs_expr)
    else:
        expr = parse_expr(s, transformations=TRANSFORMS, local_dict=ALLOWED_FUNCS, evaluate=False)
        return "expression", expr
