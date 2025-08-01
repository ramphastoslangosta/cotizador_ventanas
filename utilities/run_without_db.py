#!/usr/bin/env python3
"""
Temporary script to run the FastAPI application without database dependencies
for testing purposes when the database is not accessible.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Create a simple FastAPI app for testing
app = FastAPI(
    title="Sistema de Cotización de Ventanas - Test Mode",
    description="Running in test mode without database",
    version="5.0.0-test"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def read_root():
    return {"message": "✅ FastAPI application is running!", 
            "status": "healthy", 
            "mode": "test_without_database"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "not_connected"}

@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """Test template rendering"""
    try:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "title": "Test Mode - Templates Working"
        })
    except Exception as e:
        return HTMLResponse(f"<h1>Template Error</h1><p>{str(e)}</p>")

if __name__ == "__main__":
    print("🚀 Starting FastAPI in TEST MODE (without database)")
    print("🌐 Web: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🧪 Template Test: http://localhost:8000/test")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)