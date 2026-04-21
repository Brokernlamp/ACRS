import os
import logging
from dotenv import load_dotenv
from rag import query_rag

log = logging.getLogger("chatbot")

MODEL = "gemini-2.5-flash-lite"

_SYSTEM_PROMPT = (
    "You are an expert marketing analytics AI assistant for an agency platform called AI Growth Operator. "
    "You have access to the client's real campaign data, KPIs, predictions, budget recommendations, and performance insights. "
    "Answer questions clearly and concisely. Always ground your answers in the provided data context. "
    "If the data doesn't contain enough information to answer, say so honestly. "
    "Format numbers clearly (e.g. $1,234.56, 3.2%, 450 leads)."
)

# History: [{"role": "user"|"model", "parts": [{"text": "..."}]}]
_history: list[dict] = []


def _api_key() -> str:
    load_dotenv(override=True)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    log.debug(f"[CHATBOT] API key present: {bool(key)} (length={len(key)})")
    return key


def chat(user_message: str) -> str:
    log.info(f"[CHATBOT] chat() called — message='{user_message[:80]}'")

    # Step 1: RAG
    log.info("[CHATBOT] Step 1: querying RAG index")
    context = query_rag(user_message, n_results=8)
    if context:
        log.info(f"[CHATBOT] RAG returned {len(context.splitlines())} chunks ({len(context)} chars)")
    else:
        log.warning("[CHATBOT] RAG returned no context — answering without data")

    augmented = (
        f"[Relevant campaign data context]\n{context}\n\n[User question]\n{user_message}"
        if context else user_message
    )

    # Step 2: API key check
    key = _api_key()
    if not key:
        log.warning("[CHATBOT] No GEMINI_API_KEY — using fallback")
        reply = _fallback(user_message, context)
        _append(user_message, reply)
        return reply

    # Step 3: Call Gemini via new google-genai SDK
    log.info(f"[CHATBOT] Step 3: calling Gemini model={MODEL}")
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)

        contents = []
        for h in _history:
            contents.append(types.Content(
                role=h["role"],
                parts=[types.Part(text=h["parts"][0]["text"])]
            ))
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=augmented)]
        ))

        log.info(f"[CHATBOT] Sending {len(contents)} content entries to Gemini")
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                temperature=0.3,
            ),
        )
        reply = response.text.strip()
        log.info(f"[CHATBOT] Gemini replied ({len(reply)} chars)")
    except Exception as e:
        log.error(f"[CHATBOT] Gemini FAILED: {type(e).__name__}: {e}")
        reply = f"Gemini error: {type(e).__name__}: {e}"

    _append(user_message, reply)
    return reply


def _append(user_msg: str, model_reply: str) -> None:
    _history.append({"role": "user",  "parts": [{"text": user_msg}]})
    _history.append({"role": "model", "parts": [{"text": model_reply}]})
    log.debug(f"[CHATBOT] History now has {len(_history)} entries")


def reset_history() -> None:
    _history.clear()
    log.info("[CHATBOT] History cleared")


def get_history() -> list[dict]:
    return [{"role": h["role"], "content": h["parts"][0]["text"]} for h in _history]


def _fallback(question: str, context: str) -> str:
    if context:
        return (
            f"Here's what I found in your campaign data:\n\n{context[:800]}\n\n"
            "⚠️ Add GEMINI_API_KEY to backend/.env for full AI-powered responses."
        )
    return "No campaign data loaded yet. Upload a CSV on the Dashboard first."
