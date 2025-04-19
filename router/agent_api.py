import rag_app
from fastapi import APIRouter, HTTPException, Body, Depends
from schemas.agent_schemas import (
    CreateAgentRequest,
    DeleteAgent,
    GetAgentRequest,
    QuerAgentRequest,
    UpdateAgentRequest,
)
from models import User
from user.auth import get_current_active_user

agent_router = APIRouter()


@agent_router.get("/get_agent/{agent_name}")
async def get_agent(agent_name: str, current_user: User = Depends(get_current_active_user)):
    """
    Endpoint to get Agent Settings for the authenticated user
    """
    try:
        response = await rag_app.get_agent_details(str(current_user.id), agent_name)
        if response:
            return response
        else:
            raise ValueError(f"{agent_name} not found any agent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/list_agents")
async def list_user_agents(current_user: User = Depends(get_current_active_user)):
    """
    Endpoint to get all agents for the authenticated user
    """
    try:
        response = await rag_app.get_all_user_agents(str(current_user.id))
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.post("/create_agent")
async def create_agent(
    request: CreateAgentRequest, 
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint to create Agent settings for the authenticated user.
    """
    try:
        # Ensure the user_id is set to the current authenticated user
        request.user_id = str(current_user.id)
        response = await rag_app.create_agent_logic(request)
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.put("/update_agent")
async def update_agent(
    request: UpdateAgentRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint to update Agent settings for the authenticated user.
    """
    try:
        # Ensure the user_id is set to the current authenticated user
        request.user_id = str(current_user.id)
        response = await rag_app.update_agent_logic(request)
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.put("/agents/{agent_name}")
async def update_agent_by_path(
    agent_name: str, 
    data: dict = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    RESTful endpoint to update Agent settings for the authenticated user by path parameters.
    Used by the frontend update form.
    """
    try:
        # Ensure user_id and agent_name are set correctly in the request data
        data["user_id"] = str(current_user.id)
        data["agent_name"] = agent_name
        
        # Convert the dictionary to an UpdateAgentRequest
        request = UpdateAgentRequest(**data)
        
        # Use the existing update logic
        response = await rag_app.update_agent_logic(request)
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.delete("/delete_agent")
async def delete_agent(
    agent_name: str = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint to delete an Agent index for the authenticated user.
    """
    try:
        # Create DeleteAgent object with current user's ID
        request = DeleteAgent(
            agent_name=agent_name,
            user_id=str(current_user.id)
        )
        response, status_code = await rag_app.delete_agent_logic(request)
        return {"message": response} # Return response with the appropriate status code
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@agent_router.post("/ask_agent")
async def ask_agent(
    request: QuerAgentRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint to query a Agent pipeline based on stored user settings.
    """
    try:
        # Ensure the user_id is set to the current authenticated user
        request.user_id = str(current_user.id)
        response = await rag_app.query_agent_logic(request)
        return response
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Keep compatibility with legacy routes that use user_id in the path
# These routes will be deprecated in the future
@agent_router.get("/get_agent/{user_id}/{agent_name}", deprecated=True)
async def get_agent_legacy(user_id: str, agent_name: str, current_user: User = Depends(get_current_active_user)):
    """
    Legacy endpoint to get Agent Settings for specific users (deprecated)
    """
    # Only allow access if the user_id matches the current user or the user is an admin
    if str(current_user.id) != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this agent")
    
    try:
        response = await rag_app.get_agent_details(user_id, agent_name)
        if response:
            return response
        else:
            raise ValueError(f"{agent_name} not found any agent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@agent_router.get("/list_agents/{user_id}", deprecated=True)
async def list_user_agents_legacy(user_id: str, current_user: User = Depends(get_current_active_user)):
    """
    Legacy endpoint to get all agents for a specific user (deprecated)
    """
    # Only allow access if the user_id matches the current user or the user is an admin
    if str(current_user.id) != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access these agents")
    
    try:
        response = await rag_app.get_all_user_agents(user_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
