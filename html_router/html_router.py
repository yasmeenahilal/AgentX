from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models import User
from user.auth import get_current_user

html_app = APIRouter()
templates = Jinja2Templates(directory="templates")

# Middleware to check if user is logged in
async def get_user_or_none(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token:
            from user.auth import get_current_user
            user = await get_current_user(token)
            return user
        return None
    except Exception:
        return None

@html_app.get("/", response_class=HTMLResponse)
async def welcome(request: Request, user = Depends(get_user_or_none)):
    # If user is logged in, redirect to home
    if user:
        return RedirectResponse(url="/home")
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_page": "index"
    })

@html_app.get("/home", response_class=HTMLResponse)
async def home(request: Request, user = Depends(get_current_user)):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "active_page": "home",
        "user": user
    })

@html_app.get("/html/insert_data_to_index", response_class=HTMLResponse)
async def show_upload_form(request: Request, user = Depends(get_current_user)):
    return templates.TemplateResponse("insert_data_to_index.html", {
        "request": request,
        "active_page": "upload",
        "user": user
    })

@html_app.get("/html/create_agent", response_class=HTMLResponse)
async def create_agent(request: Request, user = Depends(get_current_user)):
    return templates.TemplateResponse("create_agent.html", {
        "request": request,
        "active_page": "create_agent",
        "user": user
    })

@html_app.get("/html/list_agents", response_class=HTMLResponse)
async def list_agents(request: Request, user = Depends(get_current_user)):
    return templates.TemplateResponse("agent_crud.html", {
        "request": request,
        "active_page": "agent_crud",
        "user": user
    })

@html_app.get("/html/agent_crud", response_class=HTMLResponse)
async def agent_crud(request: Request, user = Depends(get_current_user)):
    return templates.TemplateResponse("agent_crud.html", {
        "request": request,
        "active_page": "agent_crud",
        "user": user
    })

@html_app.get("/html/delete_agent", response_class=HTMLResponse)
async def delete_agent(request: Request, user = Depends(get_current_user)):
    return templates.TemplateResponse("delete_agent.html", {
        "request": request,
        "active_page": "delete_agent",
        "user": user
    })

@html_app.get("/html/ask_agent", response_class=HTMLResponse)
async def ask_agent(request: Request, user = Depends(get_current_user)):
    return templates.TemplateResponse("ask_agent.html", {
        "request": request,
        "active_page": "ask_agent",
        "user": user
    })

@html_app.get("/html/profile", response_class=HTMLResponse)
async def profile(request: Request, user = Depends(get_current_user)):
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "active_page": "profile",
        "user": user
    })

@html_app.get("/html/deployment", response_class=HTMLResponse)
async def deployment(request: Request, user = Depends(get_current_user)):
    return templates.TemplateResponse("deployment.html", {
        "request": request,
        "active_page": "deployment",
        "user": user
    })

@html_app.get("/demo", response_class=HTMLResponse)
async def widget_demo(request: Request):
    """
    Serve the demo page for the chat widget
    """
    with open("static/demo.html", "r") as file:
        content = file.read()
    return HTMLResponse(content=content)

@html_app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    """
    Display terms and conditions page
    """
    return templates.TemplateResponse("terms.html", {
        "request": request,
        "active_page": "terms"
    })
