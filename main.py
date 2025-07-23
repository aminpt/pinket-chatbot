from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.agent import shopping_agent  # Assuming agent.py is in the same directory
from langchain.schema import AIMessage

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
        reply = shopping_agent.invoke(inputs, config=cfg)
        print(reply)
        # Return the response from the agent (usually an AIMessage or similar response format)
        reply = {"content": reply['messages'][-1].content}

        return JSONResponse(content=reply)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=8000)
