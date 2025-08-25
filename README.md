
# Math Solver API (FastAPI + SymPy)

A minimal API that accepts **text math** and returns a solution using SymPy.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Open: http://127.0.0.1:8000/docs

### Examples

Solve an equation:
```bash
curl -X POST http://127.0.0.1:8000/solve \
  -H "content-type: application/json" \
  -d '{"query":"x^2 - 5x + 6 = 0", "task":"solve", "vars":["x"]}'
```

Differentiate:
```bash
curl -X POST http://127.0.0.1:8000/solve \
  -H "content-type: application/json" \
  -d '{"query":"sin(x)*exp(x)", "task":"differentiate", "vars":["x"]}'
```

Integrate:
```bash
curl -X POST http://127.0.0.1:8000/solve \
  -H "content-type: application/json" \
  -d '{"query":"x^2", "task":"integrate", "vars":["x"]}'
```

Simplify:
```bash
curl -X POST http://127.0.0.1:8000/solve \
  -H "content-type: application/json" \
  -d '{"query":"(x^2 - 1)/(x-1)", "task":"simplify"}'
```

## Tasks supported

- `auto` (default): If there's an `=`, solve the equation. Otherwise, simplify the expression.
- `solve`: Solve equations for the given variable(s).
- `simplify`: Algebraic simplify.
- `differentiate`: Derivative wrt the first provided variable (or inferred).
- `integrate`: Indefinite integral wrt the first provided variable (or inferred).
- `factor`, `expand`.

## Safety notes

- We use SymPy's `parse_expr` with restricted transformations and a controlled namespace.
- Inputs like `__import__` etc. will be rejected.

## Tests

```bash
pytest -q
```

## License

MIT
