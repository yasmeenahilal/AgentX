import rag_app
from fastapi import APIRouter, HTTPException, Body
from schemas.agent_schemas import (
    CreateAgentRequest,
    DeleteAgent,
    GetAgentRequest,
    QuerAgentRequest,
    UpdateAgentRequest,
)

agent_router = APIRouter()


@agent_router.get("/get_agent/{user_id}/{agent_name}")
async def get_agent(user_id: str, agent_name: str):
    """
    Endpoint to get Agent Settings for specific users
    """
    try:
        response = await rag_app.get_agent_details(user_id, agent_name)
        if response:
            return response
        else:
            raise ValueError(f"{agent_name} not found any agent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/list_agents/{user_id}")
async def list_user_agents(user_id: str):
    """
    Endpoint to get all agents for a specific user
    """
    try:
        response = await rag_app.get_all_user_agents(user_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@agent_router.put("/user/agents/{user_id}/{agent_name}")
async def update_agent_by_path(
    user_id: str, 
    agent_name: str, 
    data: dict = Body(...)
):
    """
    RESTful endpoint to update Agent settings for a user by path parameters.
    Used by the frontend update form.
    """
    try:
        # Ensure user_id and agent_name are set correctly in the request data
        data["user_id"] = user_id
        data["agent_name"] = agent_name
        
        # Convert the dictionary to an UpdateAgentRequest
        request = UpdateAgentRequest(**data)
        
        # Use the existing update logic
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
        print(response)
        return response

    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
