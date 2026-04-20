"""
Chatbot — uses RAG context + Gemini to answer marketing analytics questions.
Maintains per-session conversation history (in-memory list).
"""

from typing import Optional
from config import config
from rag import query_rag

# Conversation history: list of {"role": "user"|"model", "parts": [str]}
_history: list[dict] = []

_SYSTEM_PROMPT = """You are an expert marketing analytics AI assistant for an agency platform called AI Growth Operator.
You have access to the client's real campaign data, KPIs, predictions, budget recommendations, and performance insights.
Answer questions clearly and concisely. Always ground your answers in the provided data context.
If the data doesn't contain enough information to answer, say so honestly.
Format numbers clearly (e.g. $1,234.56, 3.2%, 450 leads).
"""


def _get_model():
    try:
        import google.generativeai as genai
        if not config.GEMINI_API_KEY:
            return None
        genai.configure(api_key=config.GEMINI_API_KEY)
        return genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=_SYSTEM_PROMPT,
        )
    except Exception:
        return None


def chat(user_message: str) -> str:
    """
    Send a message, retrieve RAG context, call Gemini, return assistant reply.
    Maintains conversation history across calls.
    """
    # Retrieve relevant data context
    context = query_rag(user_message, n_results=8)

    # Build the augmented message
    if context:
        augmented = (
            f"[Relevant campaign data context]\n{context}\n\n"
            f"[User question]\n{user_message}"
        )
    else:
        augmented = user_message

    model = _get_model()

    if model is None:
        # Fallback: rule-based response when no API key
        _history.append({"role": "user", "parts": [user_message]})
        reply = _fallback(user_message, context)
        _history.append({"role": "model", "parts": [reply]})
        return reply

    try:
        chat_session = model.start_chat(history=_history.copy())
        response = chat_session.send_message(augmented)
        reply = response.text.strip()
    except Exception as e:
        reply = f"I encountered an error calling the AI model: {str(e)}. Please check your GEMINI_API_KEY."

    _history.append({"role": "user", "parts": [user_message]})
    _history.append({"role": "model", "parts": [reply]})
    return reply


def reset_history() -> None:
    """Clear conversation history."""
    _history.clear()


def get_history() -> list[dict]:
    return [{"role": h["role"], "content": h["parts"][0]} for h in _history]


def _fallback(question: str, context: str) -> str:
    """Simple rule-based fallback when Gemini is unavailable."""
    q = question.lower()
    if context:
        if any(w in q for w in ["best", "top", "highest"]):
            return f"Based on your data:\n{context[:500]}\n\nPlease add a GEMINI_API_KEY to .env for full AI responses."
        if any(w in q for w in ["worst", "lowest", "poor"]):
            return f"Based on your data:\n{context[:500]}\n\nPlease add a GEMINI_API_KEY to .env for full AI responses."
        return f"Here's what I found in your data:\n\n{context[:600]}\n\n⚠️ Add GEMINI_API_KEY to .env for intelligent AI responses."
    return "No campaign data is loaded yet. Please upload a CSV or connect an API first."
