import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_engine, Base, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models import User, UserRole
from app.api import auth, jobs, results, workers, schedules, metrics, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("TaskFlowAPI")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if DB reachable
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")

        # Seed default Admin and User if empty
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(User).where(User.email == "admin@taskflow.io"))
            if not res.scalar_one_or_none():
                admin_user = User(
                    name="Admin User",
                    email="admin@taskflow.io",
                    hashed_password=get_password_hash("admin123"),
                    role=UserRole.ADMIN
                )
                demo_user = User(
                    name="Demo User",
                    email="user@taskflow.io",
                    hashed_password=get_password_hash("user123"),
                    role=UserRole.USER
                )
                db.add(admin_user)
                db.add(demo_user)
                await db.commit()
                logger.info("Seeded default users.")
    except Exception as e:
        logger.warning(f"Database setup during startup skipped or offline: {e}")

    yield

    try:
        await async_engine.dispose()
        logger.info("Database pool closed gracefully.")
    except Exception:
        pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-Grade Distributed Job Processing & ML Task Scheduler API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(results.router)
app.include_router(workers.router)
app.include_router(schedules.router)
app.include_router(metrics.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "status": "ONLINE",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
