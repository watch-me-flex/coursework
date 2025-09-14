from fastapi.applications import FastAPI
from app import create_app
from app.config import settings

app: FastAPI = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app="app.__main__:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )