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
    try:
        body = await request.json()
        user_message = body.get("message")
        thread_id = body.get("thread_id", user_token)

        if not user_message:
            raise HTTPException(status_code=400, detail="Message not found in request body")

        inputs = {"messages": [{"role": "user", "content": user_message}]}
        cfg = {"configurable": {"thread_id": thread_id, "user_token": user_token}}

        res = {"payload": None}
        reply = ""

        # Stream responses from the agent
        for chunk in shopping_agent.stream(inputs, config=cfg, stream_mode=["updates"]):
            if "tools" in chunk[1]:
                tools_data = chunk[1]["tools"]
                messages = tools_data.get("messages", [])
                if messages:
                    first_message = messages[0]
                    content = getattr(first_message, "content", "")
                    status = getattr(first_message, "status", "")
                    
                    # Catch 401 and return to client
                    if status == "error" and ("401" in content or "Unauthorized" in content):
                        raise HTTPException(status_code=401, detail=content)
                    
                    # Process normal global_search payload
                    if getattr(first_message, "name", "") == "global_search":
                        try:
                            res["payload"] = json.loads(content)
                        except (json.JSONDecodeError, TypeError):
                            res["payload"] = content
            
            if "agent" in chunk[1]:
                data = chunk[1]["agent"]
                if len(data["messages"][0].content) > 0:
                    reply = data["messages"][0].content

        res["content"] = reply
        return JSONResponse(content=res)

    except HTTPException as e:
        # Let FastAPI return the proper status code (like 401)
        raise e
    except Exception as e:
        # Catch all other errors as 500
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=8000)
