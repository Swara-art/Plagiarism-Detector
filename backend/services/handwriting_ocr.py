import io

try:
    from PIL import Image, ImageFilter, ImageEnhance
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

def preprocess_image(image_bytes: bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    w, h = img.size
    if w < 1000:
        img = img.resize((int(w * 1000/w), int(h * 1000/w)), Image.LANCZOS)
    return img

def extract_text_from_image(image_bytes: bytes) -> dict:
    if not OCR_AVAILABLE:
        return {"success": False, "text": "",
                "error": "pytesseract/Pillow not installed. Run: pip install pytesseract Pillow"}
    try:
        text = pytesseract.image_to_string(
            preprocess_image(image_bytes), config=r'--oem 3 --psm 6'
        ).strip()
        if not text:
            return {"success": False, "text": "",
                    "error": "No text extracted. Try a clearer, higher-contrast scan."}
        return {"success": True, "text": text,
                "char_count": len(text), "word_count": len(text.split())}
    except Exception as e:
        return {"success": False, "text": "", "error": f"OCR failed: {str(e)}"}