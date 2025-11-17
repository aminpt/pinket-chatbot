import os
from typing import Dict, List, Optional, TypedDict
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3


from app.services.api_service import APIService

# ---------------------------------------------------------------------
# 0.  Environment
# ---------------------------------------------------------------------
env_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("Set OPENAI_API_KEY before running.")


# ---------------------------------------------------------------------
# 1.  Utilities
# ---------------------------------------------------------------------
def require_token(cfg: RunnableConfig) -> str:
    """
    Extract user_token from the RunnableConfig or raise a clear error.
    """
    try:
        return cfg["configurable"]["user_token"]
    except (KeyError, TypeError) as e:
        raise e

# ---------------------------------------------------------------------
# 2.  Service instance
# ---------------------------------------------------------------------
api_service = APIService()


# ---------------------------------------------------------------------
# 3.  Tool definitions
# ---------------------------------------------------------------------
@tool
def global_search(query: str, cfg: RunnableConfig) -> List[Dict]:
    """Search the entire product catalogue."""
    token = require_token(cfg)
    return api_service.global_search(query, token=token)

@tool
def get_shopping_lists(branch_key: str, cfg: RunnableConfig) -> List[Dict]:
    """Return all shopping lists for the user in a branch."""
    token = require_token(cfg)
    return api_service.get_shopping_lists(branch_key, token=token)


@tool
def update_shopping_list(
    shopping_list_uid: str,
    item_uid: str,
    branch_uid: str,
    count: int,
    comment: str,
    cfg: RunnableConfig,
) -> Dict:
    """Add or update an item in the shopping list."""
    token = require_token(cfg)
    return api_service.update_shopping_list(
        shopping_list_uid, item_uid, branch_uid, count, comment, token=token
    )


@tool
def create_invoice(shopping_list_uid: str, address_uid: str, cfg: RunnableConfig) -> Dict:
    """Create a draft invoice."""
    token = require_token(cfg)
    return api_service.create_invoice(shopping_list_uid, address_uid, token=token)


@tool
def get_addresses(cfg: RunnableConfig) -> List[Dict]:
    """Fetch saved delivery addresses."""
    token = require_token(cfg)
    return api_service.get_addresses(token=token)


@tool
def place_order(
    shopping_list_uid: str,
    address_uid: str,
    cfg: RunnableConfig
) -> Dict:
    """Finalise checkout and place an order."""
    token = require_token(cfg)
    return api_service.place_order(shopping_list_uid, address_uid, None, token=token)

# ---------------------------------------------------------------------
# 6.  Memory / persistence
# ---------------------------------------------------------------------
db_path = os.path.join(os.path.dirname(__file__), "../chat_history.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)


def get_chat_history(thread_id: str):

    # memory.get() expects a RunnableConfig-like object
    cfg = RunnableConfig(configurable={"thread_id": thread_id})
    checkpoint = memory.get(cfg)

    if checkpoint is None:
        return {"thread_id": thread_id, "message_count": 0, "history": []}

    # Compatible with both dict-like and object-like Checkpoint
    channel_values = getattr(checkpoint, "channel_values", None)
    if channel_values is None and isinstance(checkpoint, dict):
        channel_values = checkpoint.get("channel_values")
    row_messages = channel_values.get("messages", []) if channel_values else []
    history = []
    for msg in row_messages:
        if isinstance(msg, BaseMessage):
            history.append(
                {
                    "role": getattr(msg, "type", "unknown"),
                    "content": msg.content,
                }
            )
        else:
            history.append(msg)

    return {
        "thread_id": thread_id,
        "message_count": len(history),
        "history": history
    }

TOOLS = [
    global_search,
    get_shopping_lists,
    update_shopping_list,
    create_invoice,
    get_addresses,
    place_order,
]


# ---------------------------------------------------------------------
# 4.  Model
# ---------------------------------------------------------------------
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.4).bind_tools(TOOLS)

# ---------------------------------------------------------------------
# 5.  Prompt
# ---------------------------------------------------------------------
SYSTEM_PROMPT = Path("app/guidlines/prompt.md").read_text(encoding="utf-8")

# ---------------------------------------------------------------------
# 6.  Memory / persistence
# ---------------------------------------------------------------------
checkpointer = MemorySaver()

# ---------------------------------------------------------------------
# 7.  Build the ReAct agent
# ---------------------------------------------------------------------
class ConfigSchema(TypedDict):
    user_token: str

shopping_agent = create_react_agent(
    model=llm,
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
    config_schema=ConfigSchema,
    checkpointer=memory
)
