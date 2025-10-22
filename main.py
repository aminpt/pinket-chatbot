from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.agent import shopping_agent  # Assuming agent.py is in the same directory
from langchain.schema import AIMessage
import json
# Initialize FastAPI app
app = FastAPI()

# Authorization header schema to fetch token
security = HTTPBearer()

# Helper function to extract the token from the Authorization header
def get_token_from_header(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Token missing or invalid")
    return token

@app.post("/shopping-assistant")
async def shopping_assistant(request: Request, user_token: str = Depends(get_token_from_header)):
    """
    Endpoint to interact with the shopping assistant graph.
    Expects a user message and returns a response using the agent.
    """
    # Parse the incoming JSON body
    try:
        body = await request.json()
        user_message = body.get("message")
        thread_id = body.get("thread_id", user_token)  # If thread_id is not provided, use user_token

        if not user_message:
            raise HTTPException(status_code=400, detail="Message not found in request body")

        # Prepare the inputs for the agent
        inputs = {"messages": [{"role": "user", "content": user_message}]}
        
        # Prepare the configuration with user token and thread_id
        cfg = {
            "configurable": {"thread_id": thread_id, "user_token": user_token}
        }

        # Get the response from the agent
        # reply = shopping_agent.invoke(inputs, config=cfg)
        res = {"payload": None}
        reply = ""
        for chunk in shopping_agent.stream(inputs, config=cfg, stream_mode=["updates"]):
            print("#" * 50)
            print(chunk)

            if "tools" in chunk[1]:
                tools_data = chunk[1]["tools"]
                messages = tools_data.get("messages", [])
                if messages:
                    first_message = messages[0]
                    status = getattr(first_message, "status", "")
                    content = getattr(first_message, "content", "")
            
                    # --------------- چک خطای 401 -----------------
                    if status == "error" and ("401" in content or "Unauthorized" in content):
                        raise HTTPException(status_code=401, detail=content)
                    # ---------------------------------------------
            
                    # پردازش معمولی global_search
                    if getattr(first_message, "name", "") == "global_search":
                        try:
                            res["payload"] = json.loads(content)
                        except (json.JSONDecodeError, TypeError):
                            res["payload"] = content
            if "agent" in chunk[1]:
                data = chunk[1]["agent"]
                if len(data["messages"][0].content) > 0:
                    reply = data["messages"][0].content
        # print(reply)
        # Return the response from the agent (usually an AIMessage or similar response format)
        # reply = {"content": reply['messages'][-1].content}
        # res = json.loads(res)
        res["content"] = reply
        return JSONResponse(content=res)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=8000)
