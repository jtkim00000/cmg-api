import re
from PIL import Image
import pytesseract
from sympy_ollama_tutor import analyze_and_solve


def clean_equation(text: str) -> str:
    # Keep only math-related characters
    eq = re.sub(r"[^0-9a-zA-Z+\-*/=().]", "", text)
    return eq


def process_image(image_path: str):
    """
    Runs OCR + solver pipeline on an image.
    """
    try:
        raw_text, cleaned_text, solution, explanation = run_ocr_and_solve(image_path)

        return {
            "raw": raw_text.strip() if raw_text else "",
            "cleaned": cleaned_text.strip() if cleaned_text else "",
            "solution": solution if solution else None,
            "explanation": explanation if explanation else "No explanation generated."
        }
    except Exception as e:
        return {
            "raw": "",
            "cleaned": "",
            "solution": None,
            "explanation": f"Error: {str(e)}"
        }
