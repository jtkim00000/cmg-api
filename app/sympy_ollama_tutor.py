"""
sympy_ollama_tutor.py
A small SymPy + Ollama pipeline:
 - parse a math problem (auto-detect some types),
 - compute solution and a few SymPy "intermediate" outputs,
 - ask Ollama to produce a step-by-step explanation using those facts.

Requires: sympy, ollama
"""

from typing import Dict, Any, Optional
import re
import traceback

import sympy as sp
import ollama

# -----------------------
# Utilities: detection & parsing
# -----------------------
def _safe_sympify(s: str):
    """Wrap sympy.sympify with an error-safe API that returns None on failure."""
    try:
        return sp.sympify(s)
    except Exception:
        return None

def detect_operation(text: str) -> str:
    """Heuristic detection of operation type."""
    t = text.strip().lower()
    # equation detection
    if '=' in text and not text.strip().startswith(('diff', 'd/d', 'integrate', 'int')):
        return 'solve_equation'
    # derivative keywords
    if re.search(r'\b(d/d|deriv|differentiat|prime|\'\')\b', t) or t.startswith('d/d'):
        return 'differentiate'
    if 'integrate' in t or '∫' in t or re.search(r'\bint\b', t):
        return 'integrate'
    if 'limit' in t or 'lim' in t:
        return 'limit'
    if 'simplify' in t or 'simplify(' in t:
        return 'simplify'
    if 'factor' in t:
        return 'factor'
    # fallback: try simplification/evaluation
    return 'simplify'

# -----------------------
# SymPy handlers
# -----------------------
def solve_equation(problem: str) -> Dict[str, Any]:
    """
    Solve equations of form 'expr = expr' or a single expression to be solved for a variable.
    Returns dict with intermediates and result.
    """
    left, right = problem.split('=', 1)
    L = _safe_sympify(left)
    R = _safe_sympify(right)
    if L is None or R is None:
        raise ValueError("Couldn't parse equation parts with SymPy.")
    eq = sp.Eq(L, R)
    # attempt to determine which symbol to solve for
    symbols = list(eq.free_symbols)
    if len(symbols) == 0:
        # no symbols -> check if true/false
        return {
            'operation': 'solve_equation',
            'equation': str(eq),
            'result': str(sp.simplify(L - R) == 0),
            'intermediates': {'lhs': str(L), 'rhs': str(R)},
        }
    # prefer single symbol, otherwise solve for first
    var = symbols[0]
    sol = sp.solve(eq, var)
    return {
        'operation': 'solve_equation',
        'equation': str(eq),
        'variable': str(var),
        'intermediates': {'lhs': str(L), 'rhs': str(R)},
        'result': [str(s) for s in sol],
    }

def differentiate(problem: str) -> Dict[str, Any]:
    """
    Accept strings like 'd/dx sin(x)*x' or 'derivative(sin(x)*x, x)' or 'sin(x)*x prime'
    Will try to locate variable automatically.
    """
    # try to extract using common patterns
    m = re.match(r'd/d([a-zA-Z])\s*(.*)', problem.strip())
    if m:
        var = sp.Symbol(m.group(1))
        expr = _safe_sympify(m.group(2))
        if expr is None:
            raise ValueError("Couldn't parse expression to differentiate.")
    else:
        # fallback: try parse whole and use free symbols
        expr = _safe_sympify(problem)
        if expr is None:
            raise ValueError("Couldn't parse expression to differentiate.")
        syms = list(expr.free_symbols)
        var = syms[0] if syms else sp.Symbol('x')
    deriv = sp.diff(expr, var)
    simplified = sp.simplify(deriv)
    return {
        'operation': 'differentiate',
        'expression': str(expr),
        'variable': str(var),
        'raw_derivative': str(deriv),
        'simplified_derivative': str(simplified),
    }

def integrate(problem: str) -> Dict[str, Any]:
    """
    Try to integrate an expression. If the user provided 'integrate(expr, x)' style,
    parse accordingly; otherwise pick the variable from free_symbols or default to x.
    """
    # attempt pattern integrate(expr, var)
    m = re.match(r'integrate\((.*),\s*([a-zA-Z])\s*\)', problem.replace(' ', ''))
    if m:
        expr = _safe_sympify(m.group(1))
        var = sp.Symbol(m.group(2))
    else:
        # try parse expression and pick variable
        expr = _safe_sympify(problem)
        syms = list(expr.free_symbols) if expr is not None else []
        var = syms[0] if syms else sp.Symbol('x')
    if expr is None:
        raise ValueError("Couldn't parse expression to integrate.")
    integral = sp.integrate(expr, var)
    return {
        'operation': 'integrate',
        'expression': str(expr),
        'variable': str(var),
        'integral': str(integral),
    }

def limit_handler(problem: str) -> Dict[str, Any]:
    """
    Attempt to parse limit(expression, x, a).
    """
    # naive parse for limit(f, x, a)
    m = re.match(r'limit\((.*),\s*([a-zA-Z]),\s*(.*)\)', problem.replace(' ', ''))
    if not m:
        raise ValueError("Couldn't parse limit; expect limit(expr, x, a).")
    expr = _safe_sympify(m.group(1))
    var = sp.Symbol(m.group(2))
    point = _safe_sympify(m.group(3))
    if expr is None or point is None:
        raise ValueError("Couldn't parse limit arguments.")
    val = sp.limit(expr, var, point)
    return {
        'operation': 'limit',
        'expression': str(expr),
        'variable': str(var),
        'point': str(point),
        'limit': str(val),
    }

def simplify_handler(problem: str) -> Dict[str, Any]:
    expr = _safe_sympify(problem)
    if expr is None:
        raise ValueError("Couldn't parse expression to simplify.")
    simp = sp.simplify(expr)
    return {
        'operation': 'simplify',
        'expression': str(expr),
        'simplified': str(simp),
    }

def factor_handler(problem: str) -> Dict[str, Any]:
    expr = _safe_sympify(problem)
    if expr is None:
        raise ValueError("Couldn't parse expression to factor.")
    fact = sp.factor(expr)
    return {
        'operation': 'factor',
        'expression': str(expr),
        'factored': str(fact),
    }

# -----------------------
# Top-level API: analyze_and_solve
# -----------------------
def analyze_and_solve(problem: str) -> Dict[str, Any]:
    """Main entry: detect operation and dispatch to the correct SymPy handler."""
    op = detect_operation(problem)
    try:
        if op == 'solve_equation':
            return solve_equation(problem)
        if op == 'differentiate':
            return differentiate(problem)
        if op == 'integrate':
            return integrate(problem)
        if op == 'limit':
            return limit_handler(problem)
        if op == 'factor':
            return factor_handler(problem)
        # default/simplify
        return simplify_handler(problem)
    except Exception as e:
        return {'error': str(e), 'traceback': traceback.format_exc()}

# -----------------------
# Ollama: ask the model to explain steps
# -----------------------
def make_explain_prompt(problem: str, sympy_output: Dict[str, Any]) -> str:
    """
    Build a careful prompt for the LLM: include the original problem, the computed
    results and intermediates, and instruct the model to act as a patient math tutor,
    showing step-by-step reasoning (small steps, short lines).
    """
    prompt_lines = [
        "You are a helpful math tutor. The user wants a clear, step-by-step explanation showing how to solve the problem.",
        "Be concise and show numbered steps. Explain why each step is taken.",
        "",
        f"Original problem:\n{problem}",
        "",
        "SymPy solver output (do not contradict these results; use them as ground truth):",
    ]
    # include sympy_output in readable form
    for k, v in sympy_output.items():
        prompt_lines.append(f"- {k}: {v}")
    prompt_lines += [
        "",
        "Using standard math notation (LaTeX where helpful), provide a step-by-step solution and explanation. If multiple solutions exist, explain each. If the solver could not parse something, explain what was ambiguous and how to rewrite the problem.",
        "",
        "Keep steps numbered and easy to follow for a student that understands basic algebra and calculus.",
    ]
    return "\n".join(prompt_lines)

def ask_ollama_to_explain(problem: str, sympy_output: Dict[str, Any], model: str = "gemma3") -> str:
    """
    Send the constructed prompt to Ollama and return the assistant reply text.
    Uses the ollama.chat helper (sync).
    """
    prompt = make_explain_prompt(problem, sympy_output)
    messages = [
        {'role': 'system', 'content': 'You are a precise math tutor.'},
        {'role': 'user', 'content': prompt},
    ]
    # Using the high-level chat API from the ollama Python client
    resp = ollama.chat(model=model, messages=messages)
    # resp may be a ChatResponse object or dict; access message content robustly
    # The README shows response['message']['content'] or response.message.content
    try:
        return resp['message']['content']
    except Exception:
        try:
            return resp.message.content
        except Exception:
            # fallback: str(resp)
            return str(resp)

# -----------------------
# CLI example
# -----------------------
def interactive_loop(model: str = "gemma3"):
    print("SymPy + Ollama Tutor — type 'quit' to exit.")
    while True:
        problem = input("\nEnter a math problem: ").strip()
        if problem.lower() in ('quit', 'exit'):
            break
        print("\n→ Running SymPy...")
        sympy_out = analyze_and_solve(problem)
        if 'error' in sympy_out:
            print("SymPy error:", sympy_out['error'])
            continue
        print("SymPy result:", sympy_out.get('result') or sympy_out.get('simplified') or sympy_out)
        print("\n→ Asking Ollama to explain steps (this uses your local Ollama model)...")
        try:
            explanation = ask_ollama_to_explain(problem, sympy_out, model=model)
            print("\n--- Explanation ---\n")
            print(explanation)
            print("\n-------------------\n")
        except Exception as e:
            print("Error calling Ollama:", e)

# -----------------------
# If run as script
# -----------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gemma3", help="Ollama model to use (e.g. gemma3, llama3).")
    args = parser.parse_args()
    interactive_loop(model=args.model)
