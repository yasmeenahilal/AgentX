import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlmodel import Session, select

from models import PasswordReset, User, get_session
from schemas.users_schemas import (
    PasswordResetConfirm,
    PasswordResetRequest,
    ProfileUpdate,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from user.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)

load_dotenv()

user_router = APIRouter()


# Authentication endpoints
@user_router.post("/login")
async def login_for_access_token(
    login_data: UserLogin, session: Session = Depends(get_session)
):
    """
    Authenticate user and return access token
    """
    user = authenticate_user(session, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username,
            "role": user.role,
            "user_id": str(user.id),
        }
    )

    # Set token in HTTP-only cookie
    cookie_max_age = 60 * ACCESS_TOKEN_EXPIRE_MINUTES  # convert minutes to seconds
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=cookie_max_age,
        samesite="lax",
    )

    return response


# User management endpoints
@user_router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user: UserCreate, session: Session = Depends(get_session)):
    """
    Register a new user
    """
    # Check if username already exists
    existing_user = session.exec(
        select(User).where(User.username == user.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    existing_email = session.exec(select(User).where(User.email == user.email)).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@user_router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information
    """
    return current_user


@user_router.put("/update-profile", response_model=UserResponse)
async def update_profile(
    update_data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """
    Update user profile information
    """
    # Get current user from database to ensure we have latest data
    user = session.get(User, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # If email is being changed, check if it's already in use
    if update_data.email != user.email:
        existing_email = session.exec(
            select(User).where(User.email == update_data.email)
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another user",
            )
        user.email = update_data.email

    # If password change is requested
    if update_data.current_password and update_data.new_password:
        # Verify current password
        if not verify_password(update_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Set new password
        user.hashed_password = get_password_hash(update_data.new_password)

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


# Function to send reset password email
async def send_password_reset_email(email: str, token: str):
    """Send password reset email to the user."""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    sender_email = os.getenv("SENDER_EMAIL", "noreply@agentx.com")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = "Password Reset Request"

    # Create the plain-text and HTML version of your message
    reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:8000')}/reset-password?token={token}"

    text = f"""
    Hello,
    
    You've requested to reset your password. Please click the link below to reset it:
    {reset_url}
    
    If you didn't request a password reset, please ignore this email.
    
    Thanks,
    AgentX Team
    """

    # Turn these into plain/html MIMEText objects
    part = MIMEText(text, "plain")
    message.attach(part)

    # Try to send the email
    try:
        # Create a secure connection with the server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")
        # Here you might want to log the error, but we'll continue
        # since the password reset token is still created


@user_router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    """
    Request a password reset
    """
    # Find user by email
    user = session.exec(select(User).where(User.email == request.email)).first()

    # Even if user not found, return 202 for security reasons
    if not user:
        return {
            "detail": "If an account with this email exists, a password reset link has been sent."
        }

    # Generate a secure token
    token = secrets.token_urlsafe(32)

    # Set expiration to 24 hours from now
    expires_at = datetime.now() + timedelta(hours=24)

    # Create password reset record
    password_reset = PasswordReset(user_id=user.id, token=token, expires_at=expires_at)

    session.add(password_reset)
    session.commit()

    # Send email in background to avoid blocking the response
    background_tasks.add_task(send_password_reset_email, user.email, token)

    return {
        "detail": "If an account with this email exists, a password reset link has been sent."
    }


@user_router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    request: PasswordResetConfirm, session: Session = Depends(get_session)
):
    """
    Confirm a password reset with token and new password
    """
    # Find the password reset record
    password_reset = session.exec(
        select(PasswordReset)
        .where(PasswordReset.token == request.token)
        .where(PasswordReset.is_used == False)
        .where(PasswordReset.expires_at > datetime.now())
    ).first()

    if not password_reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    # Get the user
    user = session.get(User, password_reset.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Update password
    user.hashed_password = get_password_hash(request.new_password)

    # Mark token as used
    password_reset.is_used = True

    session.add(user)
    session.add(password_reset)
    session.commit()

    return {"detail": "Password has been reset successfully"}


@user_router.post("/refresh-token")
async def refresh_access_token(
    request: Request, session: Session = Depends(get_session)
):
    """
    Refresh an access token using the current token (if still valid but near expiry)
    """
    # Get current token
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify the current token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get the user
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create a new token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        # Create response with new token
        response = JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": str(user.id),
            }
        )

        # Set new token in HTTP-only cookie
        cookie_max_age = 60 * ACCESS_TOKEN_EXPIRE_MINUTES
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=cookie_max_age,
            samesite="lax",
        )

        return response

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token - please log in again",
            headers={"WWW-Authenticate": "Bearer"},
        )


@user_router.post("/logout")
async def logout():
    """
    Handle user logout by returning a response that clears the token cookie
    """
    response = JSONResponse(content={"detail": "Successfully logged out"})
    response.delete_cookie(key="access_token")
    return response
