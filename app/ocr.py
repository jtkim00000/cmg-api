import re
import requests
from PIL import Image
import pytesseract

def extract_math_from_text(raw_text: str) -> str:
    """
    Return a cleaned math expression from OCR output.
    Strategy:
     - normalize common unicode symbols
     - remove leading prompt words ("solve", "find", ...)
     - split lines, filter out purely textual lines
     - prefer a line that contains '=' and at least one digit
     - otherwise pick first sensible math-like line
     - post-process: insert '*' between number and '(' and remove stray trailing 'y='
    """
    if not raw_text:
        return ""

    # 1) normalize common unicode symbols
    norm_map = {
        "−": "-", "—": "-", "×": "*", "·": "*", "∙": "*",
        "÷": "/", "√": "sqrt", "π": "pi"
    }
    s = raw_text
    for k, v in norm_map.items():
        s = s.replace(k, v)

    # 2) remove common instruction words (case-insensitive)
    s = re.sub(r'(?i)\b(?:solve(?:\s+for)?|calculate|find|evaluate|what is)\b', ' ', s)

    # 3) split into lines and trim
    lines = [ln.strip() for ln in s.splitlines()]

    # 4) build candidate lines that look like math
    candidates = []
    for ln in lines:
        if not ln:
            continue
        # skip trivial "y=" or "x="
        if re.fullmatch(r'[A-Za-z]\s*=', ln):
            # probably a place for answer, ignore
            continue
        # if line contains a digit OR contains an '=' with something else -> treat as math candidate
        if re.search(r'\d', ln) or ('=' in ln and re.search(r'[A-Za-z0-9]', ln.replace('=', ''))):
            candidates.append(ln)
            continue
        # also accept lines containing a variable and an operator (e.g. "x+2")
        if re.search(r'[A-Za-z].*[\+\-\*/\^()]', ln) or re.search(r'[\+\-\*/\^()].*[A-Za-z]', ln):
            candidates.append(ln)
            continue
        # otherwise skip textual lines (like "The answer is")
    # debug: show candidates
    # print("DEBUG candidates:", candidates)

    # 5) prefer a line that has '=' and a digit
    for ln in candidates:
        if '=' in ln and re.search(r'\d', ln):
            chosen = ln
            break
    else:
        # otherwise, choose first candidate containing digits/operators
        chosen = None
        for ln in candidates:
            if re.search(r'[\d\+\-\*/\^()=]', ln):
                chosen = ln
                break

    # 6) fallback: if nothing chosen, strip non-math chars from whole text
    if not chosen:
        cleaned = re.sub(r'[^0-9A-Za-z=+\-*/^()., ]', '', s)
        chosen = cleaned.strip()

    # 7) post-process: remove leftover words, trailing lone "y=" etc.
    chosen = chosen.strip()
    # remove trailing single-letter-equals if any left
    chosen = re.sub(r'\b([A-Za-z])\s*=$', '', chosen).strip()

    # insert explicit multiplication between number and '(' or between letter and '(' if needed:
    chosen = re.sub(r'(?<=\d)\s*\(', '*(', chosen)   # 2( -> 2*(
    chosen = re.sub(r'(?<=[A-Za-z0-9\)])\s*(?=[A-Za-z0-9\(])', '', chosen)  # collapse stray spaces inside math
    # remove multiple spaces
    chosen = re.sub(r'\s+', '', chosen)

    return chosen

# Example integration in your ocr workflow:

if __name__ == "__main__":
    img = Image.open("/Users/jessekim/Desktop/CMG/cmg-api/uploaded_images/math.png")
    raw = pytesseract.image_to_string(img, config="--psm 6")  # tune psm if needed
    print("Raw OCR:", repr(raw))

    cleaned = extract_math_from_text(raw)
    print("Cleaned equation:", cleaned)

    # optionally detect requested variable from the instruction (e.g., "Solve for y")
    m = re.search(r'(?i)solve\s+for\s+([A-Za-z])', raw)
    vars_to_send = [m.group(1)] if m else None

    payload = {"problem": cleaned}
    if vars_to_send:
        payload["vars"] = vars_to_send

    # send to your solver (adjust URL/path if your API expects /api/solve or different key)
    url = "http://127.0.0.1:8000/solve"
    resp = requests.post(url, json=payload, timeout=60)
    print("API Response:", resp.status_code, resp.text)

    