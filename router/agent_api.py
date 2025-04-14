import rag_app
from fastapi import APIRouter, HTTPException
from schemas.agent_schemas import (
    CreateAgentRequest,
    DeleteAgent,
    GetAgentRequest,
    QuerAgentRequest,
    UpdateAgentRequest,
)

agent_router = APIRouter()


@agent_router.post("/get_agent")
async def get_agent(request: GetAgentRequest):
    """
    Endpoint to get Agent Settings for specific users
    """
    try:
        response = await rag_app.get_agent_details(request)
        if response:
            return {"details": response}
        else:
            raise ValueError(f"{request.agent_name}not found any agent")
    except Exception as e:
        print(f"Error at agent_api.get_agent {e}")


@agent_router.post("/create_agent")
async def create_agent(request: CreateAgentRequest):
    """
    Endpoint to create Agent settings for a user.
    """
    try:
        response = await rag_app.create_agent_logic(request)
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.put("/update_agent")
async def update_agent(request: UpdateAgentRequest):
    """
    Endpoint to update Agent settings for a user.
    """
    try:
        response = await rag_app.update_agent_logic(request)
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.delete("/delete_agent")
async def delete_agent(request: DeleteAgent):
    """
    Endpoint to delete an Agent index for a user.
    """
    try:
        response, status_code = await rag_app.delete_agent_logic(request)
        print(response)
        return {"message": response } # Return response with the appropriate status code
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@agent_router.post("/ask_agent")
async def ask_agent(request: QuerAgentRequest):
    """
    Endpoint to query a Agent pipeline based on stored user settings.
    """
    try:
        response = await rag_app.query_agent_logic(request)
        return response

    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
