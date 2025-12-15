# run.py - entrypoint to start the FastAPI app
# Usage: python run.py
import uvicorn
from app.main import app
from app.config import settings

if __name__ == '__main__':
    uvicorn.run("app.main:app", host=settings['server']['host'], port=int(settings['server']['port']), reload=False)
