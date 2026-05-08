import os
import logging
from dotenv import load_dotenv
from rag import query_rag

log = logging.getLogger("chatbot")

# Gemini model
GEMINI_MODEL = "gemini-2.5-flash-lite"

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
        "groq": "",
        "gemini": os.getenv("GEMINI_API_KEY", "").strip(),
    }


# Max chars per RAG chunk and number of chunks — keeps context tight
_RAG_CHUNKS = 3
_RAG_CHUNK_CHARS = 300
# Max history turns sent to model (each turn = 1 user + 1 assistant msg)
_MAX_HISTORY_TURNS = 4


def _trim_context(context: str) -> str:
    """Keep top N chunks, each truncated to _RAG_CHUNK_CHARS."""
    chunks = [c.strip() for c in context.splitlines() if c.strip()]
    trimmed = [c[:_RAG_CHUNK_CHARS] for c in chunks[:_RAG_CHUNKS]]
    return "\n".join(trimmed)


def chat(user_message: str, license_token: str = "") -> dict:
    """Returns { reply, tokens_in, tokens_out, tokens_total, provider }"""
    log.info(f"[CHATBOT] chat() called — message='{user_message[:80]}'")

    # Step 1: RAG — fetch fewer, shorter chunks
    context = query_rag(user_message, n_results=_RAG_CHUNKS)
    if context:
        context = _trim_context(context)
        log.info(f"[CHATBOT] RAG context trimmed to {len(context)} chars")
    else:
        log.warning("[CHATBOT] RAG returned no context")

    augmented = (
        f"[Campaign data]\n{context}\n\n[Question]\n{user_message}"
        if context else user_message
    )

    keys = _keys()
    license_server = os.getenv("LICENSE_SERVER_URL", "").strip()

    # Step 2: Route through license server if configured (keeps Gemini key server-side)
    if license_server and license_token:
        result = _call_license_server_ai(augmented, license_server, license_token)
    elif keys["gemini"]:
        result = _call_gemini(augmented, keys["gemini"])
    else:
        log.warning("[CHATBOT] No API key found — using fallback")
        result = {"reply": _fallback(user_message, context), "tokens_in": 0, "tokens_out": 0, "provider": "none"}

    # If rate-limited (dict with error key), return as-is for main.py to raise 429
    if isinstance(result, dict) and result.get("error"):
        return result

    reply = result["reply"] if isinstance(result, dict) else result
    tokens_in  = result.get("tokens_in", 0)  if isinstance(result, dict) else 0
    tokens_out = result.get("tokens_out", 0) if isinstance(result, dict) else 0
    provider   = result.get("provider", "unknown") if isinstance(result, dict) else "unknown"

    log.info(f"[CHATBOT] tokens — in={tokens_in} out={tokens_out} total={tokens_in+tokens_out} provider={provider}")
    _append(user_message, reply)
    return {"reply": reply, "tokens_in": tokens_in, "tokens_out": tokens_out, "tokens_total": tokens_in + tokens_out, "provider": provider}


def _call_license_server_ai(prompt: str, server_url: str, token: str) -> dict:
    """Route AI request through license server — Gemini key never leaves the server."""
    log.info("[CHATBOT] Routing via license server AI proxy")
    try:
        import requests
        r = requests.post(
            f"{server_url}/api/ai/chat",
            json={"prompt": prompt, "token": token},
            timeout=30,
        )
        if r.status_code == 402:
            # Token credits exhausted
            return {"error": "credits_exhausted", "reply": "", "tokens_in": 0, "tokens_out": 0, "provider": "license_server"}
        if r.status_code == 403:
            return {"reply": "⚠️ License invalid. Please contact support.", "tokens_in": 0, "tokens_out": 0, "provider": "license_server"}
        if r.status_code == 429:
            return r.json()  # { error, limit, resets_at, ... } — main.py raises 429
        r.raise_for_status()
        data = r.json()
        return {
            "reply": data.get("reply", "No response from AI."),
            "tokens_in":  data.get("tokens_in", 0),
            "tokens_out": data.get("tokens_out", 0),
            "provider": "license_server",
        }
    except Exception as e:
        log.error(f"[CHATBOT] License server AI proxy FAILED: {e}")
        return {"reply": f"AI service temporarily unavailable: {e}", "tokens_in": 0, "tokens_out": 0, "provider": "license_server"}


def _recent_history() -> list[dict]:
    """Return only the last _MAX_HISTORY_TURNS turns to save tokens."""
    return _history[-(  _MAX_HISTORY_TURNS * 2):]


def _call_groq(augmented: str, key: str) -> dict:
    log.info(f"[CHATBOT] Calling Groq model={GROQ_MODEL}")
    try:
        from groq import Groq
        client = Groq(api_key=key)
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
        for h in _recent_history():
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": augmented})

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        usage = response.usage
        reply = response.choices[0].message.content.strip()
        log.info(f"[CHATBOT] Groq replied — in={usage.prompt_tokens} out={usage.completion_tokens}")
        return {"reply": reply, "tokens_in": usage.prompt_tokens, "tokens_out": usage.completion_tokens, "provider": "groq"}
    except Exception as e:
        log.error(f"[CHATBOT] Groq FAILED: {type(e).__name__}: {e}")
        return {"reply": f"AI error: {type(e).__name__}: {e}", "tokens_in": 0, "tokens_out": 0, "provider": "groq"}


def _call_gemini(augmented: str, key: str) -> dict:
    log.info(f"[CHATBOT] Calling Gemini model={GEMINI_MODEL}")
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)

        contents = []
        for h in _recent_history():
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
        usage = response.usage_metadata
        tokens_in  = getattr(usage, "prompt_token_count", 0) or 0
        tokens_out = getattr(usage, "candidates_token_count", 0) or 0
        reply = response.text.strip()
        log.info(f"[CHATBOT] Gemini replied — in={tokens_in} out={tokens_out}")
        return {"reply": reply, "tokens_in": tokens_in, "tokens_out": tokens_out, "provider": "gemini"}
    except Exception as e:
        log.error(f"[CHATBOT] Gemini FAILED: {type(e).__name__}: {e}")
        return {"reply": f"AI error: {type(e).__name__}: {e}", "tokens_in": 0, "tokens_out": 0, "provider": "gemini"}


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
