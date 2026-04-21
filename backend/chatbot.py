import os
import logging
from dotenv import load_dotenv
from rag import query_rag

log = logging.getLogger("chatbot")

# Groq model — fast, free, 14,400 req/day
GROQ_MODEL = "llama-3.1-8b-instant"
# Gemini fallback model
GEMINI_MODEL = "gemini-2.0-flash-lite"

_SYSTEM_PROMPT = (
    "You are an expert marketing analytics AI assistant for an agency platform called AI Growth Operator. "
    "You have access to the client's real campaign data, KPIs, predictions, budget recommendations, and performance insights. "
    "Answer questions clearly and concisely. Always ground your answers in the provided data context. "
    "If the data doesn't contain enough information to answer, say so honestly. "
    "Format numbers clearly (e.g. $1,234.56, 3.2%, 450 leads)."
)

# History stored in OpenAI format (works for both Groq and Gemini)
# [{"role": "user"|"assistant", "content": "..."}]
_history: list[dict] = []


def _keys() -> dict:
    load_dotenv(override=True)
    return {
        "groq": os.getenv("GROQ_API_KEY", "").strip(),
        "gemini": os.getenv("GEMINI_API_KEY", "").strip(),
    }


def chat(user_message: str) -> str:
    log.info(f"[CHATBOT] chat() called — message='{user_message[:80]}'")

    # Step 1: RAG
    context = query_rag(user_message, n_results=8)
    if context:
        log.info(f"[CHATBOT] RAG returned {len(context.splitlines())} chunks")
    else:
        log.warning("[CHATBOT] RAG returned no context")

    augmented = (
        f"[Relevant campaign data context]\n{context}\n\n[User question]\n{user_message}"
        if context else user_message
    )

    keys = _keys()

    # Step 2: Try Groq first (free, fast), then Gemini, then fallback
    if keys["groq"]:
        reply = _call_groq(augmented, keys["groq"])
    elif keys["gemini"]:
        reply = _call_gemini(augmented, keys["gemini"])
    else:
        log.warning("[CHATBOT] No API key found — using fallback")
        reply = _fallback(user_message, context)

    _append(user_message, reply)
    return reply


def _call_groq(augmented: str, key: str) -> str:
    log.info(f"[CHATBOT] Calling Groq model={GROQ_MODEL}")
    try:
        from groq import Groq
        client = Groq(api_key=key)
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
        # Add history
        for h in _history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": augmented})

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        reply = response.choices[0].message.content.strip()
        log.info(f"[CHATBOT] Groq replied ({len(reply)} chars)")
        return reply
    except Exception as e:
        log.error(f"[CHATBOT] Groq FAILED: {type(e).__name__}: {e}")
        return f"AI error: {type(e).__name__}: {e}"


def _call_gemini(augmented: str, key: str) -> str:
    log.info(f"[CHATBOT] Calling Gemini model={GEMINI_MODEL}")
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)

        contents = []
        for h in _history:
            role = "user" if h["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=h["content"])]))
        contents.append(types.Content(role="user", parts=[types.Part(text=augmented)]))

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                temperature=0.3,
            ),
        )
        reply = response.text.strip()
        log.info(f"[CHATBOT] Gemini replied ({len(reply)} chars)")
        return reply
    except Exception as e:
        log.error(f"[CHATBOT] Gemini FAILED: {type(e).__name__}: {e}")
        return f"AI error: {type(e).__name__}: {e}"


def _append(user_msg: str, model_reply: str) -> None:
    _history.append({"role": "user",      "content": user_msg})
    _history.append({"role": "assistant", "content": model_reply})
    log.debug(f"[CHATBOT] History now has {len(_history)} entries")


def reset_history() -> None:
    _history.clear()
    log.info("[CHATBOT] History cleared")


def get_history() -> list[dict]:
    return list(_history)


def _fallback(question: str, context: str) -> str:
    if context:
        return (
            f"Here's what I found in your campaign data:\n\n{context[:800]}\n\n"
            "⚠️ Add GROQ_API_KEY or GEMINI_API_KEY to backend/.env to enable AI responses."
        )
    return "No campaign data loaded yet. Upload a CSV on the Dashboard first."
