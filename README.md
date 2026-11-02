# Pinket Chatbot

Persian shopping assistant for [Pinket](https://pinket.com). A FastAPI service wraps a LangGraph ReAct agent that searches the catalogue, updates the cart, and places orders on behalf of an authenticated user.

The agent answers in Persian and only handles shopping. Conversation state is stored in a local SQLite database so a client can resume a thread.

## How it works

1. The client sends a Bearer JWT issued by Pinket’s auth server.
2. The API verifies the token against `https://pinket.com/auth-server/.well-known/jwks.json` and reads the user id from the claims.
3. The agent (`gpt-4.1-mini`) calls Pinket APIs with that same token: product search, shopping lists, addresses, invoices, and checkout.
4. The reply, any tool payload (search results or a placed order), and the `thread_id` are returned to the client.

```
client  →  FastAPI (main.py)  →  shopping agent (app/agent.py)
                                      ├─ tools → Pinket API (app/services)
                                      └─ SqliteSaver → chat_history.db
```

## Requirements

- Python 3.9+
- An OpenAI API key
- A valid Pinket user JWT for each request

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install PyJWT
```

`PyJWT` is imported by `app/auth_utils.py` and is not listed in `requirements.txt`.

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
```

## Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or with Docker Compose:

```bash
docker compose up --build
```

Pass `OPENAI_API_KEY` into the container (for example with an env file). The compose file only sets `ENV=production`.

The graph is also declared in `langgraph.json` as `app/agent.py:shopping_agent` for the LangGraph CLI.

## API

All routes require `Authorization: Bearer <jwt>`.

### `POST /shopping-assistant`

Send a message. Omit `thread_id` to start a new conversation; send it back to continue one.

```bash
curl -X POST http://localhost:8000/shopping-assistant \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "شیر کم‌چرب داری؟", "thread_id": null}'
```

Response:

```json
{
  "payload": {},
  "content": "…",
  "thread_id": "…"
}
```

`content` is the assistant reply. `payload` is the JSON returned by `global_search` or `place_order` when those tools run; otherwise it is `null`.

### `GET /shopping-assistant/threads`

Lists the authenticated user’s threads and the message count of each.

### `GET /shopping-assistant/history/{thread_id}`

Returns the stored messages for a thread.

## Agent tools

| Tool | Pinket endpoint |
| --- | --- |
| `global_search` | `GET ai-assistance/items` |
| `get_shopping_lists` | `GET cu/v3/shopping-lists` |
| `update_shopping_list` | `PUT cu/v3/shopping-lists` |
| `get_addresses` | `GET cu/v1/addresses` |
| `create_invoice` | `POST cu/v3/shopping-lists/{uid}/invoice` |
| `place_order` | `POST cu/v3/orders` |

System instructions for tone, Persian naming, and when to search live in `app/guidlines/prompt.md`.

## Project layout

```
main.py                  FastAPI routes
app/agent.py             LangGraph agent, tools, SQLite history
app/auth_utils.py        JWT verification
app/services/            Pinket HTTP client
app/guidlines/prompt.md  System prompt
langgraph.json           LangGraph graph entry
chat_history.db          Created at runtime (checkpoints and user↔thread map)
```
