# LegalEase: Your AI Legal Assistant ⚖️

LegalEase is an intelligent, multilingual web application designed to help users understand complex legal documents. By leveraging powerful AI models, it can extract text, translate, summarize, and provide critical insights into any uploaded document, making legal information more accessible and transparent.

## Try it here: https://legalease-ai-n77zid8dujn2vderg7mvnt.streamlit.app/

---

## ✨ Key Features

-   **Multi-Format Document Upload:** Seamlessly upload and process documents in both **PDF** and **Image** formats (`.png`, `.jpg`, `.jpeg`).
-   **Advanced OCR:** Automatically extracts text from documents using Tesseract, with a robust two-pass system for high accuracy.
-   **Smart Language Auto-Detection:** Intelligently identifies the source language of the document after cleaning the extracted text.
-   **Automatic Background Analysis:**
    -   **Summarization:** Instantly generates a concise summary in your chosen output language as soon as a document is uploaded.
    -   **Risk Assessment:** Proactively scans for signs of fraud or authenticity issues and displays a prominent warning for high-risk documents.
    -   **Key Insights:** Automatically extracts crucial information like the entities involved, signature requirements, and the consequences of signing (or not signing).
-   **Multilingual AI Suite:**
    -   **Translate:** Translate the entire document into a wide range of global languages.
    -   **Summarize:** Get a summary in your desired language, regardless of the document's original language.
    -   **Interactive Q&A:** Ask questions about the document and get answers in your chosen language. The AI will answer from the document if possible, or from its general knowledge if the information isn't present.

---

## 🛠️ Tech Stack

-   **Frontend:** [Streamlit](https://streamlit.io/)
-   **Backend & Logic:** [Python](https://www.python.org/)
-   **AI & LLM:** [Groq API](https://groq.com/) (running Llama 3.1)
-   **OCR Engine:** [Tesseract](https://github.com/tesseract-ocr/tesseract) (`pytesseract`)
-   **Language Detection:** `langdetect`
-   **PDF Processing:** `pdf2image` & Poppler

---

## 🚀 Getting Started

Follow these steps to set up and run LegalEase on your local machine.

### 1. Prerequisites

You must have the Tesseract OCR engine and the Poppler utility installed on your system.

-   **Windows:**
    -   **Tesseract:** Download and run the installer from the [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) page. **Important:** During setup, ensure you install the scripts for the languages you need (e.g., Devanagari, Gurmukhi). Add the installation folder (e.g., `C:\Program Files\Tesseract-OCR`) to your system's PATH.
    -   **Poppler:** Download the latest binary zip file from [this link](https://github.com/oschwartz10612/poppler-windows/releases/). Extract it and add its `\Library\bin` subfolder to your system's PATH.

-   **macOS / Linux:** Use a package manager like Homebrew or apt.
    ```bash
    # macOS with Homebrew
    brew install tesseract tesseract-lang poppler

    # Linux (Ubuntu/Debian)
    sudo apt-get install tesseract-ocr tesseract-ocr-all poppler-utils
    ```

### 2. Clone the Repository

Clone this repository to your local machine:
```bash
git clone [https://github.com/samyak-jain2112/LegalEase-AI](https://github.com/samyak-jain2112/LegalEase-AI)
cd LegalEase-AI

