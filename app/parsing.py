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

def parse_and_solve(query: str):
    try:
        # Case 1: Equation
        if "=" in query:
            lhs, rhs = query.split("=")
            lhs_expr = sympify(lhs.strip())
            rhs_expr = sympify(rhs.strip())
            equation = Eq(lhs_expr, rhs_expr)
            
            result = solve(equation)
            
            return {
                "ok": True,
                "detected": "equation",
                "result": [str(r) for r in result],
                "steps": None,
                "warnings": []
            }

        # Case 2: Expression
        else:
            expr = sympify(query)
            
            result = expr.simplify()
            
            return {
                "ok": True,
                "detected": "expression",
                "result": str(result),
                "steps": None,
                "warnings": []
            }

    except Exception as e:
        return {
            "ok": False,
            "detected": {},
            "result": None,
            "steps": None,
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
