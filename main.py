from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import aiohttp
import asyncio
from datetime import datetime
import os
import ssl
import certifi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import Website, get_db, init_db
import logging
from config import PASSWORD
from starlette.middleware.sessions import SessionMiddleware
from email_sender import send_notification_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-here",  # Change this to a secure secret key
    session_cookie="website_checker_session"
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Create SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Global variable to store the background task
background_task = None

# Check if user is authenticated
async def is_authenticated(request: Request):
    if not request.session.get("authenticated"):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return True

async def check_website_status(session: aiohttp.ClientSession, url: str) -> bool:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        # First try with SSL verification
        async with session.get(url, timeout=5, headers=headers, allow_redirects=True, ssl=ssl_context) as response:
            return 200 <= response.status < 400
    except aiohttp.ClientSSLError:
        # If SSL error occurs, try without SSL verification
        try:
            async with session.get(url, timeout=10, headers=headers, allow_redirects=True, ssl=False) as response:
                return 200 <= response.status < 400
        except:
            return False
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error checking {url}: {str(e)}")
        return False

async def check_all_websites_background():
    """Background task to check all websites periodically"""
    while True:
        try:
            # Get a new database session
            async for db in get_db():
                try:
                    # Get all websites
                    result = await db.execute(select(Website))
                    websites = result.scalars().all()
                    
                    # Check status for all websites
                    async with aiohttp.ClientSession() as session:
                        tasks = [check_website_status(session, website.url) for website in websites]
                        results = await asyncio.gather(*tasks)
                        
                        # Update status in database and send notifications if needed
                        for website, status in zip(websites, results):
                            old_status = website.status
                            website.status = status
                            website.last_checked = datetime.utcnow()
                            
                            # Send notification if website is down and notifications are enabled
                            if website.notify_on_down and not status and (
                                not website.last_notification_sent or 
                                (datetime.utcnow() - website.last_notification_sent).total_seconds() > 3600
                            ):
                                if await send_notification_email(website.url, status):
                                    website.last_notification_sent = datetime.utcnow()
                        
                        await db.commit()
                        logger.info(f"Auto-checked {len(websites)} websites")
                except Exception as e:
                    logger.error(f"Error in background check: {str(e)}")
                    continue
                
        except Exception as e:
            logger.error(f"Major error in background check: {str(e)}")
        
        # Wait for 60 seconds before next check
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    # Initialize database
    await init_db()
    
    # Start background task
    global background_task
    background_task = asyncio.create_task(check_all_websites_background())
    logger.info("Started background website checking task")

@app.on_event("shutdown")
async def shutdown_event():
    # Cancel background task
    global background_task
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass
    logger.info("Stopped background website checking task")

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None}
    )

@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    if password == PASSWORD:
        request.session["authenticated"] = True
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid password"}
    )

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/")
async def home(request: Request, db: AsyncSession = Depends(get_db), _: bool = Depends(is_authenticated)):
    # Get all websites from database
    result = await db.execute(select(Website))
    websites = result.scalars().all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "websites": websites}
    )

@app.post("/add-website")
async def add_website(
    url: str = Form(...),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(is_authenticated)
):
    # Check if website already exists
    result = await db.execute(select(Website).where(Website.url == url))
    existing_website = result.scalar_one_or_none()
    
    if not existing_website:
        # Create new website entry
        website = Website(url=url)
        db.add(website)
        await db.commit()
    
    return {"success": True}

@app.post("/remove-website")
async def remove_website(
    url: str = Form(...),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(is_authenticated)
):
    # Find and remove website
    result = await db.execute(select(Website).where(Website.url == url))
    website = result.scalar_one_or_none()
    if website:
        await db.delete(website)
        await db.commit()
    return {"success": True}

@app.post("/toggle-notification")
async def toggle_notification(
    url: str = Form(...),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(is_authenticated)
):
    # Find website and toggle notification setting
    result = await db.execute(select(Website).where(Website.url == url))
    website = result.scalar_one_or_none()
    if website:
        website.notify_on_down = not website.notify_on_down
        await db.commit()
        return {"success": True, "notify_on_down": website.notify_on_down}
    return {"success": False}

@app.get("/check-status")
async def check_status(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(is_authenticated)
):
    # Return current status from database including notification settings
    result = await db.execute(select(Website))
    websites = result.scalars().all()
    return [
        {
            "url": website.url,
            "status": website.status,
            "last_checked": website.last_checked.isoformat(),
            "notify_on_down": website.notify_on_down
        }
        for website in websites
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 