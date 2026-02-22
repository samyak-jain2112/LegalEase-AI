"""
AI module for LegalEase.
All AI operations now use the RAG pipeline for context retrieval,
and Map-Reduce for summarization.
"""

import streamlit as st
import groq
import json
from rag_module import retrieve_relevant_chunks, get_all_chunks


def get_translation(groq_api_key, target_language, chunks):
    """
    Translate the full document by translating each chunk sequentially.
    Uses all chunks (not RAG retrieval) since translation needs full coverage.
    """
    all_chunks = get_all_chunks(chunks)
    if not all_chunks:
        st.warning("There is no text to translate.")
        return

    translated_chunks = []
    progress_bar = st.progress(0, text=f"Translating chunk 1 of {len(all_chunks)}...")
    try:
        client = groq.Groq(api_key=groq_api_key)
        for i, chunk in enumerate(all_chunks):
            progress_bar.progress(
                (i + 1) / len(all_chunks),
                text=f"Translating chunk {i + 1} of {len(all_chunks)}...",
            )
            system_prompt = (
                f"You are a translation machine. Your ONLY task is to translate "
                f"the user's text into {target_language}. "
                f"Output NOTHING but the direct translation."
            )
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk},
                ],
                model="llama-3.1-8b-instant",
            )
            translated_chunks.append(chat_completion.choices[0].message.content)
        st.session_state.translated_text = " ".join(translated_chunks)
        progress_bar.empty()
    except Exception as e:
        st.error(f"Translation failed. Error: {e}")
        progress_bar.empty()


def get_summary(groq_api_key, target_language, chunks):
    """
    Map-Reduce summarization:
    1. Map: summarize each chunk individually
    2. Reduce: combine all chunk summaries into a final cohesive summary
    This covers the ENTIRE document instead of truncating.
    """
    all_chunks = get_all_chunks(chunks)
    if not all_chunks:
        st.warning("There is no text to summarize.")
        return

    with st.spinner(f"Summarizing in {target_language}..."):
        try:
            client = groq.Groq(api_key=groq_api_key)

            # --- MAP STEP: summarize each chunk ---
            chunk_summaries = []
            for i, chunk in enumerate(all_chunks):
                map_prompt = (
                    f"You are a summarization engine. Summarize the following "
                    f"section of a legal document concisely. Focus on key facts, "
                    f"obligations, and important details. Write in {target_language}."
                    f"\n\nSECTION {i + 1}:\n---\n{chunk}\n---"
                )
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": map_prompt}],
                    model="llama-3.1-8b-instant",
                )
                chunk_summaries.append(completion.choices[0].message.content)

            # --- REDUCE STEP: combine all chunk summaries ---
            combined_summaries = "\n\n".join(
                [f"Section {i + 1}: {s}" for i, s in enumerate(chunk_summaries)]
            )

            reduce_system = (
                f"You are a multilingual summarization engine. "
                f"Your final output MUST be written in {target_language}. "
                f"This is your most important instruction."
            )
            reduce_prompt = (
                f"Below are summaries of individual sections of a legal document. "
                f"Combine them into a single, cohesive, well-structured summary. "
                f"Remove any redundancy and organize the information logically. "
                f"The summary MUST be written in {target_language}.\n\n"
                f"SECTION SUMMARIES:\n---\n{combined_summaries}\n---"
            )

            reduce_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": reduce_system},
                    {"role": "user", "content": reduce_prompt},
                ],
                model="llama-3.1-8b-instant",
            )
            st.session_state.summary = reduce_completion.choices[0].message.content

        except Exception as e:
            st.error(f"Automatic summarization failed. Error: {e}")


def get_qa_answer(groq_api_key, question, target_language, collection):
    """
    RAG-based Q&A: retrieve relevant chunks for the question,
    then ask the LLM to answer based on those chunks.
    """
    context = retrieve_relevant_chunks(collection, question, top_k=5)

    if not context.strip():
        st.error("Could not retrieve relevant context from the document.")
        return

    try:
        client = groq.Groq(api_key=groq_api_key)

        system_prompt = (
            f"You are an expert legal assistant. Your final response MUST be "
            f"written in {target_language}. Answer the user's question based on "
            f"the provided document context. If the answer is not found in the "
            f"context, clearly state that the information is not available in "
            f"the document and provide an answer from your general knowledge, "
            f"making clear that it is from general knowledge."
        )

        user_prompt = (
            f"Based on the following relevant sections from a legal document, "
            f"answer the user's question.\n\n"
            f"RELEVANT DOCUMENT SECTIONS:\n---\n{context}\n---\n\n"
            f'QUESTION: "{question}"'
        )

        with st.spinner(f"Generating answer in {target_language}..."):
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model="llama-3.1-8b-instant",
            )
            st.session_state.qa_answer = completion.choices[0].message.content

    except Exception as e:
        st.error(f"Q&A failed. Error: {e}")


def analyze_document_authenticity(groq_api_key, collection):
    """
    RAG-based authenticity analysis: retrieve chunks related to fraud indicators.
    """
    fraud_query = (
        "fraud forgery fake document authenticity signs of tampering "
        "suspicious inconsistencies altered modified"
    )
    context = retrieve_relevant_chunks(collection, fraud_query, top_k=5)

    if not context.strip():
        return 0, "No text available for analysis."

    try:
        client = groq.Groq(api_key=groq_api_key)
        prompt = (
            f"You are a forensic document analysis AI. Assess the likelihood "
            f"that the provided text is from a fake or fraudulent document. "
            f"Analyze for red flags and respond with a single JSON object with "
            f'two keys: "is_fake_confidence_score": an integer (0-100), '
            f'and "reasoning": a brief, one-sentence explanation.\n\n'
            f"DOCUMENT TEXT:\n---\n{context}\n---\n\nJSON RESPONSE:"
        )
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0,
            response_format={"type": "json_object"},
        )
        result = json.loads(completion.choices[0].message.content)
        return result.get("is_fake_confidence_score", 0), result.get(
            "reasoning", "No specific reason provided."
        )
    except Exception as e:
        st.error(f"Authenticity analysis failed: {e}")
        return 0, "Analysis could not be completed."


def get_key_insights(groq_api_key, target_language, collection):
    """
    RAG-based key insights: retrieve chunks related to legal entities,
    signatures, obligations, and consequences.
    """
    insights_query = (
        "parties involved entities signatures obligations responsibilities "
        "consequences of signing not signing agreement terms conditions"
    )
    context = retrieve_relevant_chunks(collection, insights_query, top_k=7)

    if not context.strip():
        st.warning("No relevant sections found for key insights.")
        return

    try:
        client = groq.Groq(api_key=groq_api_key)
        system_prompt = (
            f"You are an AI legal analyst. Your task is to extract specific, "
            f"critical information from the provided document text. "
            f"You MUST provide your analysis in {target_language}. "
            f"Structure your response using Markdown headings."
        )
        user_prompt = f"""
        Please analyze the following document text and provide a structured breakdown of these four key points. If a point is not mentioned in the text, explicitly state that.

        1.  **Entities Involved:** Who are the parties, individuals, or organizations mentioned in this document?
        2.  **Signature Requirements:** Does this document state or imply that a signature is required? Who needs to sign?
        3.  **Consequences of Signing:** Based on the text, what obligations, responsibilities, or agreements does a person enter into by signing this?
        4.  **Consequences of NOT Signing:** Based on the text, what happens if the relevant party does not sign this document?

        RELEVANT DOCUMENT SECTIONS:
        ---
        {context}
        ---
        """
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="llama-3.1-8b-instant",
        )
        st.session_state.key_insights = completion.choices[0].message.content
    except Exception as e:
        st.error(f"Failed to generate key insights. Error: {e}")