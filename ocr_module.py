import streamlit as st
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
import io
from langdetect import detect, LangDetectException
import re
from utils import LANGUAGE_OPTIONS
import pdfplumber
import os

# ADDED: detect Streamlit Cloud environment
IS_CLOUD = os.getenv("STREAMLIT_SERVER_RUNNING") == "true"

TESSERACT_PATH = os.getenv("TESSERACT_CMD")

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
elif os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def clean_extracted_text(text):
    if not text:
        return ""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        alpha_chars = sum(1 for char in stripped_line if char.isalpha())
        total_chars = len(stripped_line)
        if total_chars > 10 and (alpha_chars / total_chars) < 0.4:
            continue
        cleaned_lines.append(stripped_line)
    cleaned_text = "\n".join(cleaned_lines)
    return re.sub(r'\n\s*\n', '\n\n', cleaned_text).strip()


def extract_text_from_pdf_no_ocr(file_bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    return text.strip()


def extract_text_from_document(uploaded_file, language='auto'):
    if uploaded_file is None:
        return "", "en"

    file_bytes = uploaded_file.getvalue()

    # CHANGED: cloud-safe PDF handling (no OCR on Streamlit Cloud)
    if uploaded_file.name.lower().endswith(".pdf"):
        if IS_CLOUD:
            text = extract_text_from_pdf_no_ocr(file_bytes)
            if not text:
                st.warning(
                    "This PDF appears to be scanned. "
                    "OCR is disabled on Streamlit Cloud. "
                    "Please run the app locally for OCR support."
                )
            return text, "en"
        else:
            try:
                images = convert_from_bytes(file_bytes)
            except Exception as img_err:
                st.error(f"File could not be read or processed. Error: {img_err}")
                return "", "en"
    else:
        images = [Image.open(io.BytesIO(file_bytes))]

    initial_scan_langs = 'eng+hin+pan'
    sample_text = ""

    for image in images:
        sample_text += pytesseract.image_to_string(image, lang=initial_scan_langs) + "\n"

    if not sample_text.strip():
        return "", "en"

    ocr_lang_code = 'eng'
    if language == 'auto':
        try:
            cleaned_sample = clean_extracted_text(sample_text)
            if cleaned_sample:
                detected_lang = detect(cleaned_sample)
                ocr_lang_code = next(
                    (tess_code for name, tess_code in LANGUAGE_OPTIONS.items()
                     if tess_code.startswith(detected_lang)),
                    'eng'
                )
        except LangDetectException:
            pass
    else:
        ocr_lang_code = language

    final_text = ""
    for image in images:
        final_text += pytesseract.image_to_string(image, lang=ocr_lang_code) + "\n\n"

    cleaned_text = clean_extracted_text(final_text)

    if not cleaned_text:
        return "", "en"

    return cleaned_text, ocr_lang_code[:2]
