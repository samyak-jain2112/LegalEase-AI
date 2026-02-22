# LegalEase: Your AI Legal Assistant ⚖️

LegalEase is an intelligent, multilingual web application designed to help users understand complex legal documents. It uses a **RAG (Retrieval-Augmented Generation)** pipeline to extract text via OCR, index it into a vector store, and then retrieve only the most relevant sections for AI-powered summarization, translation, Q&A, and risk analysis — all in the user's chosen language.

## Try it here: https://legalease-ai-n77zid8dujn2vderg7mvnt.streamlit.app/

---

## ✨ Key Features

-   **Multi-Format Document Upload:** Seamlessly upload and process documents in both **PDF** and **Image** formats (`.png`, `.jpg`, `.jpeg`).
-   **Advanced OCR:** Automatically extracts text from documents using Tesseract, with a robust two-pass system for high accuracy.
-   **Smart Language Auto-Detection:** Intelligently identifies the source language of the document after cleaning the extracted text.
-   **RAG-Powered Document Indexing:** After extraction, the document is split into overlapping chunks, embedded using `sentence-transformers`, and stored in an in-memory ChromaDB vector store for fast, accurate retrieval.
-   **Automatic Background Analysis:**
    -   **Summarization (Map-Reduce):** Generates a comprehensive summary of the **entire** document by summarizing each chunk individually and then combining them — no truncation.
    -   **Risk Assessment:** Retrieves fraud-relevant sections via similarity search and scans for signs of forgery or authenticity issues.
    -   **Key Insights:** Retrieves sections about entities, signatures, and obligations to extract structured legal insights.
-   **Multilingual AI Suite:**
    -   **Translate:** Translate the entire document chunk-by-chunk into a wide range of global languages.
    -   **Summarize:** Get a full-document summary in your desired language, regardless of the document's original language.
    -   **Interactive Q&A:** Ask questions and get answers powered by RAG — the system retrieves only the most relevant sections before answering in your chosen language.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          User Uploads Document                       │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  OCR & Cleaning (ocr_module.py)                                      │
│  ┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │  PDF → Images   │──▶│  Tesseract OCR   │──▶│  Text Cleaning   │  │
│  │  (pdf2image)    │   │  (2-pass system)  │   │  (noise removal) │  │
│  └─────────────────┘   └──────────────────┘   └────────┬─────────┘  │
└────────────────────────────────────────────────────────┬─────────────┘
                                                         │
                       ┌─────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  RAG Pipeline (rag_module.py)                                        │
│  ┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │  Overlapping    │──▶│  Sentence-Trans.  │──▶│  ChromaDB Store  │  │
│  │  Text Chunking  │   │  Embeddings       │   │  (in-memory)     │  │
│  │  (500 chars)    │   │  (MiniLM-L6-v2)   │   │                  │  │
│  └─────────────────┘   └──────────────────┘   └────────┬─────────┘  │
└────────────────────────────────────────────────────────┬─────────────┘
                                                         │
                       ┌─────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  AI Operations (ai_module.py)                  Groq API (Llama 3.1) │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ Summary       │ Map-Reduce: summarize each chunk → combine     │ │
│  ├───────────────┼────────────────────────────────────────────────┤ │
│  │ Q&A           │ RAG: retrieve top-5 relevant chunks → answer   │ │
│  ├───────────────┼────────────────────────────────────────────────┤ │
│  │ Key Insights  │ RAG: retrieve top-7 chunks → extract insights  │ │
│  ├───────────────┼────────────────────────────────────────────────┤ │
│  │ Risk Analysis │ RAG: retrieve top-5 fraud-related chunks       │ │
│  ├───────────────┼────────────────────────────────────────────────┤ │
│  │ Translation   │ All chunks sequentially → full-text translate  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Frontend** | [Streamlit](https://streamlit.io/) |
| **Backend & Logic** | [Python](https://www.python.org/) |
| **AI & LLM** | [Groq API](https://groq.com/) (Llama 3.1) |
| **RAG — Vector Store** | [ChromaDB](https://www.trychroma.com/) (in-memory) |
| **RAG — Embeddings** | [Sentence-Transformers](https://www.sbert.net/) (`all-MiniLM-L6-v2`) |
| **OCR Engine** | [Tesseract](https://github.com/tesseract-ocr/tesseract) (`pytesseract`) |
| **Language Detection** | `langdetect` |
| **PDF Processing** | `pdf2image` & Poppler |

---

## 📁 Project Structure

```
LegalEase/
├── app.py              # Streamlit UI & main application flow
├── rag_module.py       # RAG pipeline: chunking, embeddings, vector store, retrieval
├── ai_module.py        # AI operations: summary, Q&A, insights, authenticity, translation
├── ocr_module.py       # OCR text extraction & cleaning
├── utils.py            # Language option mappings
├── requirements.txt    # Python dependencies
├── packages.txt        # System-level packages (Streamlit Cloud)
└── .streamlit/
    └── secrets.toml    # API keys (GROQ_API_KEY)
```

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

```bash
git clone https://github.com/samyak-jain2112/LegalEase-AI
cd LegalEase-AI
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

Create a `.streamlit/secrets.toml` file (or set environment variable):
```toml
GROQ_API_KEY = "your-groq-api-key-here"
```

### 5. Run the App

```bash
streamlit run app.py
```

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
