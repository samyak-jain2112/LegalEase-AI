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
import pytesseract

TESSERACT_PATH = os.getenv("TESSERACT_CMD")

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
elif os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def clean_extracted_text(text):
    """
    Intelligently cleans raw OCR output.
    """
    if not text: return ""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line: continue
        alpha_chars = sum(1 for char in stripped_line if char.isalpha())
        total_chars = len(stripped_line)
        if total_chars > 10 and (alpha_chars / total_chars) < 0.4: continue
        cleaned_lines.append(stripped_line)
    cleaned_text = "\n".join(cleaned_lines)
    return re.sub(r'\n\s*\n', '\n\n', cleaned_text).strip()

#Cloud safe pdf text exraction 
def extract_text_from_pdf_no_ocr(file_bytes):
    """
    Cloud-safe PDF text extraction (NO OCR).
    """
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    return text.strip()

def extract_text_from_document(uploaded_file, language='auto'):
    """
    PERMANENT FIX: Implements a fast, accurate, two-pass hybrid OCR strategy.
    """
    if uploaded_file is None: return "", "en"
    
    file_bytes = uploaded_file.getvalue()
    images = []
    try:
        if uploaded_file.name.lower().endswith('.pdf'):
            images.extend(convert_from_bytes(file_bytes))
        else:
            images.append(Image.open(io.BytesIO(file_bytes)))
    except Exception as img_err:
        st.error(f"File could not be read or processed. Error: {img_err}"); return "", "en"

    if not images:
        st.error("Could not convert the document into images for processing."); return "", "en"

    try:
        initial_scan_langs = 'eng+hin+pan'
        sample_text = ""
        with st.spinner("Performing initial scan..."):
            for image in images:
                sample_text += pytesseract.image_to_string(image, lang=initial_scan_langs) + "\n"

        if not sample_text.strip():
            st.warning("Could not extract any text during the initial scan.")
            return "", "en"

        ocr_lang_code = 'eng'
        if language == 'auto':
            try:
                with st.spinner("Detecting language..."):
                    cleaned_sample = clean_extracted_text(sample_text)
                    if cleaned_sample:
                        detected_lang = detect(cleaned_sample)
                        ocr_lang_code = next((tess_code for name, tess_code in LANGUAGE_OPTIONS.items() if tess_code.startswith(detected_lang)), 'eng')
                        st.sidebar.success(f"Detected Language: {ocr_lang_code.upper()}")
                    else:
                        st.sidebar.warning("Could not identify language. Defaulting to English.")
            except LangDetectException:
                st.sidebar.warning("Could not reliably detect language. Defaulting to English.")
        else:
            ocr_lang_code = language

        final_text = ""
        with st.spinner(f"Performing high-accuracy scan with {ocr_lang_code.upper()} model..."):
            for image in images:
                final_text += pytesseract.image_to_string(image, lang=ocr_lang_code) + "\n\n"

        with st.spinner("Sanitizing final text..."):
            cleaned_text = clean_extracted_text(final_text)

        if not cleaned_text:
            st.warning("No readable text could be extracted after final cleaning.")
            return "", "en"

        return cleaned_text, ocr_lang_code[:2]

    except Exception as e:
        st.error(f"A critical error occurred during text extraction: {e}")
        return "", "en"