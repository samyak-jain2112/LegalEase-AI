import streamlit as st
import groq
import json
import re

def chunk_text(text, chunk_size=2000):
    chunks = []
    while len(text) > chunk_size:
        break_point = text.rfind('.', 0, chunk_size)
        if break_point == -1: break_point = text.rfind(' ', 0, chunk_size)
        if break_point == -1: break_point = chunk_size
        chunks.append(text[:break_point+1])
        text = text[break_point+1:]
    chunks.append(text)
    return chunks


def get_translation(groq_api_key, target_language):
    text_to_translate = st.session_state.get('extracted_text', '')
    if not text_to_translate.strip():
        st.warning("There is no text to translate."); return
    text_chunks = chunk_text(text_to_translate)
    translated_chunks = []
    progress_bar = st.progress(0, text=f"Translating chunk 1 of {len(text_chunks)}...")
    try:
        client = groq.Groq(api_key=groq_api_key)
        for i, chunk in enumerate(text_chunks):
            progress_bar.progress((i + 1) / len(text_chunks), text=f"Translating chunk {i+1} of {len(text_chunks)}...")
            system_prompt = f"You are a translation machine. Your ONLY task is to translate the user's text into {target_language}. Output NOTHING but the direct translation."
            user_prompt = chunk
            chat_completion = client.chat.completions.create(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], model="llama-3.1-8b-instant")
            translated_chunks.append(chat_completion.choices[0].message.content)
        st.session_state.translated_text = " ".join(translated_chunks)
        progress_bar.empty()
    except Exception as e:
        st.error(f"Translation failed. Error: {e}"); progress_bar.empty()

def get_summary(groq_api_key, target_language):
    """
    FINAL FIX: Implements a "bulletproof" dual-command prompt to force the correct output language.
    """
    with st.spinner(f"Summarizing in {target_language}..."):
        try:
            client = groq.Groq(api_key=groq_api_key)
            text_to_summarize = st.session_state.get('translated_text', st.session_state.extracted_text)
            truncated_text = text_to_summarize[:2500]

            system_prompt = f"You are a multilingual summarization engine. Your final output MUST be written in {target_language}. This is your most important instruction. Do not use any other language."
            
            user_prompt = f"Please provide a concise summary of the following text. Remember, the summary MUST be written in {target_language}.\n\nDOCUMENT TEXT:\n---\n{truncated_text}\n---"

            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ], model="llama-3.1-8b-instant"
            )
            st.session_state.summary = chat_completion.choices[0].message.content
        except Exception as e:
            st.error(f"Automatic summarization failed. Error: {e}")

def get_qa_answer(groq_api_key, question, target_language):
  
    client = groq.Groq(api_key=groq_api_key)
    context = st.session_state.get('translated_text', st.session_state.get('extracted_text', ''))
    if not context.strip():
        st.error("Document text is empty."); return
    try:
        with st.spinner("Analyzing document..."):
            gatekeeper_prompt = f"""Based *only* on the DOCUMENT TEXT below, can the user's question be answered? Respond with a single JSON object with one key, "answer_in_document", which is either true or false. DOCUMENT TEXT: --- {context[:2500]} --- USER'S QUESTION: "{question}" JSON RESPONSE:"""
            gatekeeper_completion = client.chat.completions.create(messages=[{"role": "user", "content": gatekeeper_prompt}], model="llama-3.1-8b-instant", temperature=0, response_format={"type": "json_object"})
            is_answer_in_doc = json.loads(gatekeeper_completion.choices[0].message.content).get("answer_in_document", False)
        system_prompt = f"You are an expert assistant. Your final response MUST be written in {target_language}."
        if is_answer_in_doc:
            with st.spinner(f"Generating answer in {target_language}..."):
                user_prompt = f"Based ONLY on the following document, answer the user's question.\n\nDOCUMENT: --- {context} ---\n\nQUESTION: \"{question}\""
                final_completion = client.chat.completions.create(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], model="llama-3.1-8b-instant")
                st.session_state.qa_answer = final_completion.choices[0].message.content
        else:
            with st.spinner(f"Consulting knowledge base and answering in {target_language}..."):
                user_prompt = f"The answer was not in the user's document. Answer the following question using your general knowledge.\n\nQUESTION: \"{question}\""
                final_completion = client.chat.completions.create(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], model="llama-3.1-8b-instant")
                st.session_state.qa_answer = f"I could not find a direct answer in your document. However, based on my general knowledge, here is an explanation (in {target_language}):\n\n" + final_completion.choices[0].message.content
    except Exception as e:
        st.error(f"Q&A failed. Error: {e}")

def analyze_document_authenticity(groq_api_key, document_text):

    try:
        client = groq.Groq(api_key=groq_api_key)
        truncated_text = document_text[:2500]
        prompt = f"""You are a forensic document analysis AI. Assess the likelihood that the provided text is from a fake or fraudulent document. Analyze for red flags and respond with a single JSON object with two keys: "is_fake_confidence_score": an integer (0-100), and "reasoning": a brief, one-sentence explanation. DOCUMENT TEXT: --- {truncated_text} --- JSON RESPONSE:"""
        analysis_completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.1-8b-instant", temperature=0, response_format={"type": "json_object"})
        result = json.loads(analysis_completion.choices[0].message.content)
        return result.get("is_fake_confidence_score", 0), result.get("reasoning", "No specific reason provided.")
    except Exception as e:
        st.error(f"Authenticity analysis failed: {e}")
        return 0, "Analysis could not be completed."

def get_key_insights(groq_api_key, target_language):
 
    try:
        client = groq.Groq(api_key=groq_api_key)
        text_to_analyze = st.session_state.get('translated_text', st.session_state.extracted_text)
        truncated_text = text_to_analyze[:4000]
        system_prompt = f"You are an AI legal analyst. Your task is to extract specific, critical information from the provided document text. You MUST provide your analysis in {target_language}. Structure your response using Markdown headings."
        user_prompt = f"""
        Please analyze the following document text and provide a structured breakdown of these four key points. If a point is not mentioned in the text, explicitly state that.

        1.  **Entities Involved:** Who are the parties, individuals, or organizations mentioned in this document?
        2.  **Signature Requirements:** Does this document state or imply that a signature is required? Who needs to sign?
        3.  **Consequences of Signing:** Based on the text, what obligations, responsibilities, or agreements does a person enter into by signing this?
        4.  **Consequences of NOT Signing:** Based on the text, what happens if the relevant party does not sign this document?

        DOCUMENT TEXT:
        ---
        {truncated_text}
        ---
        """
        chat_completion = client.chat.completions.create(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], model="llama-3.1-8b-instant")
        st.session_state.key_insights = chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"Failed to generate key insights. Error: {e}")