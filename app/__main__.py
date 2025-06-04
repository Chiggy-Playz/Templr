import uvicorn
from app.config import settings


def main():
    """Run the FastAPI application using Uvicorn."""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
        workers=settings.workers,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
