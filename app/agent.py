"""
shopping_agent.py
© 2025 Your Company — LangGraph ReAct Shopping Assistant
"""
import os
import requests
from typing import TypedDict, Annotated, Sequence

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

# ---------------------------------------------------------------------
# 0.  Environment -----------------------------------------------------------------
# Expect OPENAI_API_KEY in the environment (put it in .env or your host’s secret‑store)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("Set OPENAI_API_KEY (e.g., in .env) before running.")

# ---------------------------------------------------------------------
# 1.  Helper to build an auth header from RunnableConfig ----------------------------
def _auth_header(cfg: RunnableConfig) -> dict[str, str]:
    token = cfg["configurable"].get("user_token")
    if not token:
        raise ValueError(
            "Missing user_token in RunnableConfig.configurable — "
            "UI must pass the token when invoking the graph."
        )
    return {"Authorization": f"{token}"}


# ---------------------------------------------------------------------
# 2.  Tool definitions -------------------------------------------------
@tool
def search_products(query: str, cfg: RunnableConfig) -> list[dict]:
    """Full‑text product search; returns a list of product dicts."""
    url = f"{API_BASE_URL}/products/search"
    resp = requests.get(url, params={"q": query}, headers=_auth_header(cfg), timeout=10)
    resp.raise_for_status()
    return resp.json()


@tool
def add_to_cart(sku: str, quantity: int = 1, cfg: RunnableConfig = None) -> str:
    """Add an item (SKU) to the current user's cart."""
    url = f"{API_BASE_URL}/cart/items"
    payload = {"sku": sku, "quantity": quantity}
    resp = requests.post(url, json=payload, headers=_auth_header(cfg), timeout=10)
    resp.raise_for_status()
    return "added"


@tool
def get_cart(cfg: RunnableConfig) -> dict:
    """Retrieve current cart contents."""
    url = f"{API_BASE_URL}/cart"
    resp = requests.get(url, headers=_auth_header(cfg), timeout=10)
    resp.raise_for_status()
    return resp.json()


@tool
def checkout(cfg: RunnableConfig) -> dict:
    """Submit the order and return order confirmation."""
    url = f"{API_BASE_URL}/cart/checkout"
    resp = requests.post(url, headers=_auth_header(cfg), timeout=10)
    resp.raise_for_status()
    return resp.json()


# List of all tools the agent may call
TOOLS = [search_products, add_to_cart, get_cart, checkout]

# ---------------------------------------------------------------------
# 3.  Model ------------------------------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Instruct the model which functions it can call
llm = llm.bind_tools(TOOLS)

# ---------------------------------------------------------------------
# 4.  Prompt -----------------------------------------------------------
SYSTEM_PROMPT = (
    "You are an expert shopping assistant. Use the tools provided to search "
    "the catalogue, manage the user's cart, and complete purchases. "
    "Always explain what you are doing and, unless the user asks otherwise, "
    "summarise the cart before checkout."
)

# ---------------------------------------------------------------------
# 5.  Memory / persistence --------------------------------------------
checkpointer = InMemorySaver()

# ---------------------------------------------------------------------
# 6.  Build the ReAct agent -------------------------------------------
shopping_agent = create_react_agent(
    model=llm,
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

# ---------------------------------------------------------------------
# 7.  Convenience wrapper (optional) ----------------------------------
def run_shopping_agent(user_message: str, *, thread_id: str, user_token: str):
    """
    Helper so the UI layer only needs to supply plain strings.
    """
    inputs = {"messages": [{"role": "user", "content": user_message}]}
    cfg = {"configurable": {"thread_id": thread_id, "user_token": user_token}}
    return shopping_agent.invoke(inputs, cfg)


# ---------------------------------------------------------------------
# 8.  __main__ block for quick manual test ----------------------------
if __name__ == "__main__":
    import json

    _token = os.getenv("TEST_USER_TOKEN", "demo‑token‑123")
    reply = run_shopping_agent(
        "Find me waterproof trail‑running shoes under £120 and add the top pick to my cart",
        thread_id="demo‑session‑1",
        user_token=_token,
    )
    print(json.dumps(reply, indent=2, default=str))
