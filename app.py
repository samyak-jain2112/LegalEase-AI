import streamlit as st
from ocr_module import extract_text_from_document
from ai_module import get_translation, get_summary, get_qa_answer, analyze_document_authenticity, get_key_insights
from utils import LANGUAGE_OPTIONS, TARGET_LANGUAGES

st.set_page_config(page_title="LegalEase", layout="wide", page_icon="⚖️")

st.markdown("""<style> .stApp { background-color: #0E1117; } [data-testid="stSidebar"] { background-color: #1E2126; } h1, h2, h3, p, .stMarkdown, .stText, .stAlert p { color: #FAFAFA; } .stTextInput input, .stTextArea textarea { background-color: #2D3748; border: 1px solid #4A5568; color: #FAFAFA; } .stButton>button { background-color: #2563EB; color: white; } .stButton>button:hover { background-color: #1D4ED8; } button[data-baseweb="tab"] { color: #A0AEC0; } button[data-baseweb="tab"][aria-selected="true"] { color: #2563EB; border-bottom: 2px solid #2563EB; } </style>""", unsafe_allow_html=True)

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

st.title("LegalEase: Your AI Legal Assistant ⚖️")
st.write("Upload a document for automatic summarization, key insights, and multilingual Q&A.")

with st.sidebar:
    st.header("Upload & Language Settings")
    uploaded_file = st.file_uploader("Choose a PDF or Image file", type=['pdf', 'png', 'jpg', 'jpeg'])
    ocr_language_key = st.selectbox("Document Language (Optional Override)", options=list(LANGUAGE_OPTIONS.keys()))
    chosen_ocr_lang = LANGUAGE_OPTIONS[ocr_language_key]
    target_language_key = st.selectbox("Output Language:", options=list(TARGET_LANGUAGES.keys()), index=0)
    chosen_target_lang = TARGET_LANGUAGES[target_language_key]

if not GROQ_API_KEY:
    st.error("App is not configured. The developer needs to provide a GROQ_API_KEY in the Streamlit Secrets.")
elif uploaded_file is not None:
    
    if ('extracted_text' not in st.session_state or st.session_state.get('file_name') != uploaded_file.name or st.session_state.get('ocr_lang_used') != chosen_ocr_lang):
        
        with st.spinner("Step 1/4: Extracting text..."):
            text, lang_code = extract_text_from_document(uploaded_file, language=chosen_ocr_lang)
        
        keys_to_clear = ['extracted_text', 'translated_text', 'summary', 'qa_answer', 'authenticity_score', 'authenticity_reason', 'key_insights']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        
        st.session_state.extracted_text = text
        st.session_state.source_lang_code = lang_code
        st.session_state.file_name = uploaded_file.name
        st.session_state.ocr_lang_used = chosen_ocr_lang

        if text:
            with st.spinner("Step 2/4: Performing background risk analysis..."):
                score, reason = analyze_document_authenticity(GROQ_API_KEY, text)
                st.session_state.authenticity_score = score
                st.session_state.authenticity_reason = reason
            
            with st.spinner(f"Step 3/4: Automatically generating summary in {chosen_target_lang}..."):
                get_summary(GROQ_API_KEY, chosen_target_lang)

            with st.spinner(f"Step 4/4: Automatically extracting key insights in {chosen_target_lang}..."):
                get_key_insights(GROQ_API_KEY, chosen_target_lang)

    if st.session_state.get('authenticity_score', 0) > 85:
        st.error(f"**⚠️ High-Risk Document Detected!** (Confidence: {st.session_state.authenticity_score}%)")
        st.warning(f"**Reason:** {st.session_state.authenticity_reason}")

    if st.session_state.get('extracted_text'):
        st.header("Extracted Document Text")
        st.text_area("Review the extracted text below.", st.session_state.extracted_text, height=250)
        
        tab1, tab2, tab3 = st.tabs(["📜 Summary & Translation", "🔑 Key Insights", "❓ Interactive Q&A"])
        
        with tab1:
            st.subheader("Automatic Summary")
            if 'summary' in st.session_state:
                st.markdown(st.session_state.summary)
            else:
                st.info("Summary is being generated...")

            st.subheader("Translate Document")
            if st.button(f"Translate Full Text to {chosen_target_lang}"):
                get_translation(GROQ_API_KEY, chosen_target_lang)
            if 'translated_text' in st.session_state:
                st.text_area("Translated Text", st.session_state.translated_text, height=200)

        with tab2:
            st.subheader("Key Insights Analysis")
            if 'key_insights' in st.session_state:
                st.markdown(st.session_state.key_insights)
            else:
                st.info("Key insights are being generated...")

        with tab3:
            st.subheader(f"Ask Questions (Get answers in {chosen_target_lang})")
            user_question = st.text_input("Enter your question here:")
            if st.button("Get Answer"):
                if user_question:
                    get_qa_answer(GROQ_API_KEY, user_question, chosen_target_lang)
                else:
                    st.warning("Please enter a question.")
            if 'qa_answer' in st.session_state:
                st.markdown(st.session_state.qa_answer)
    else:
        st.warning("No text could be extracted.")
else:
    st.info("Please upload a document to begin.")