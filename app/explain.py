from sympy import Eq, Poly, factor, simplify, Add, Mul

def _s(e):  # compact string
    return str(simplify(e))

def explain_linear(eq, var):
    steps = []
    lhs, rhs = eq.lhs, eq.rhs

    # Split each side into "var terms" and "constant terms"
    var_part   = lambda e: e - e.as_independent(var, as_Add=True)[0]
    const_part = lambda e: e.as_independent(var, as_Add=True)[0]

    A = simplify(var_part(lhs) - var_part(rhs))        # should be k*var
    B = simplify(const_part(rhs) - const_part(lhs))    # constants on the right

    steps.append(f"Move variable terms left and constants right:  {_s(Eq(lhs, rhs))}  →  {_s(Eq(A, B))}")

    coeff = A.as_coefficient(var)
    if coeff is None:
        # Fallback if SymPy couldn't pick off the coefficient directly
        coeff = simplify(A/var)

    if simplify(coeff - 1) != 0:
        steps.append(f"Divide both sides by { _s(coeff) }:  {_s(Eq(A, B))}  →  {_s(Eq(var, B/coeff))}")
    else:
        steps.append(f"Variable already isolated:  {_s(Eq(var, B))}")

    return steps

def explain_quadratic(eq, var):
    steps = []
    expr = simplify(eq.lhs - eq.rhs)
    poly = Poly(expr, var)
    a, b, c = poly.all_coeffs()  # degree 2 → [a, b, c]

    steps.append(f"Standard form: {_s(Eq(eq.lhs, eq.rhs))}  →  {_s(Eq(expr, 0))} with a={_s(a)}, b={_s(b)}, c={_s(c)}")

    D = simplify(b**2 - 4*a*c)
    steps.append(f"Discriminant: Δ = b² − 4ac = {_s(D)}")

    fact = factor(expr)
    if _s(fact) != _s(expr):
        steps.append(f"Factor the quadratic:  {_s(expr)} = {_s(fact)}")
        steps.append("Apply zero-product property: set each factor to 0 and solve.")
    else:
        steps.append("Use the quadratic formula:  x = (−b ± √Δ) / (2a). Substitute a, b, c and simplify.")

    return steps

def explain_derivative(expr, var):
    steps = []
    if isinstance(expr, Add):
        steps.append("Linearity: d/dx(f + g) = f' + g'. Differentiate each term and add.")
    elif isinstance(expr, Mul):
        steps.append("Product rule: d/dx(f·g) = f'·g + f·g'. Differentiate each factor.")
    elif hasattr(expr, "args") and len(expr.args) == 1 and expr.args[0].has(var):
        steps.append("Chain rule: d/dx f(g(x)) = f'(g(x)) · g'(x).")
    else:
        steps.append("Differentiate using basic rules and simplify.")
    return steps