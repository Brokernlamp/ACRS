# License Server — Chat Credits Feature

## Context
This is the license server for "AI Growth Operator" — a desktop Electron app.
The app routes all AI chat through this server. You hold the Gemini API key.
Clients never see the key.

## What needs to be added

### 1. Database — add chat credits to license record

Add these fields to your license/subscription table:
```
chat_tokens_remaining  INTEGER  DEFAULT 50000
chat_tokens_total      INTEGER  DEFAULT 50000
```
 
`chat_tokens_remaining` = tokens left to spend (input + output combined).
`chat_tokens_total` = total ever allocated (for display/reporting).

---

### 2. Update `POST /api/license/validate`

Current response: `{ token, ... }`
New response must include:
```json
{
  "token": "<jwt>",
  "chat_credits": 47320
}
```
`chat_credits` = current `chat_tokens_remaining` from DB.

---

### 3. Update `POST /api/license/poll`

Current response: `{ action: "CONTINUE" | "RENEW" | "BLOCK", token? }`
New response must include `chat_credits` on every response:
```json
{
  "action": "CONTINUE",
  "chat_credits": 47320
}
```
This is how top-ups reach the client — next poll after a top-up delivers the new balance.

---

### 4. Update `POST /api/ai/chat`

Request body (already exists):
```json
{ "prompt": "...", "token": "<lease jwt>" }
```

New logic:
1. Verify JWT — if invalid/expired → 403
2. Look up `chat_tokens_remaining` for this license key
3. If `chat_tokens_remaining <= 0` → return **402**:
   ```json
   { "error": "credits_exhausted" }
   ```
4. Call Gemini with the prompt
5. Get actual token usage from Gemini response (`usage_metadata.prompt_token_count + candidates_token_count`)
6. Deduct from `chat_tokens_remaining` in DB
7. Return:
   ```json
   {
     "reply": "...",
     "tokens_in": 342,
     "tokens_out": 187,
     "credits_remaining": 46791
   }
   ```

---

### 5. New `POST /api/admin/topup` — add credits to a license

This is your admin endpoint to distribute more credits to a client.

Request (protected by admin secret header `X-Admin-Key`):
```json
{
  "license_key": "452acdbc-6751-4d98-ae25-d95b8133a2fc",
  "add_tokens": 50000
}
```

Logic:
- Verify `X-Admin-Key` header matches your `ADMIN_SECRET` env var
- Find license by `license_key`
- `chat_tokens_remaining += add_tokens`
- `chat_tokens_total += add_tokens`
- Return:
  ```json
  {
    "license_key": "452acdbc-...",
    "chat_tokens_remaining": 96791,
    "chat_tokens_total": 100000
  }
  ```

The client app picks up the new balance on the next 30-minute poll automatically.
No action needed on the client side.

---

### 6. New `GET /api/admin/credits/:license_key` — check a client's balance

Request header: `X-Admin-Key: <your secret>`

Response:
```json
{
  "license_key": "452acdbc-...",
  "chat_tokens_remaining": 46791,
  "chat_tokens_total": 100000,
  "percent_used": 53.2
}
```

---

## Summary of all endpoints to add/modify

| Method | Path | Change |
|---|---|---|
| POST | `/api/license/validate` | Add `chat_credits` to response |
| POST | `/api/license/poll` | Add `chat_credits` to response |
| POST | `/api/ai/chat` | Check balance → deduct → return `credits_remaining` |
| POST | `/api/admin/topup` | NEW — add tokens to a license |
| GET  | `/api/admin/credits/:key` | NEW — check balance |

---

## Token deduction logic (important)

Deduct **input + output tokens combined** after each successful Gemini call.
If Gemini fails, do NOT deduct.

```python
tokens_used = tokens_in + tokens_out
license.chat_tokens_remaining = max(0, license.chat_tokens_remaining - tokens_used)
db.commit()
```

---

## Default credits on new license creation

When issuing a new license key, set:
- `chat_tokens_remaining = 50000` (enough for ~100 typical queries)
- `chat_tokens_total = 50000`

You can adjust this per plan when creating the license.
