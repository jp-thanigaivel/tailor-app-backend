import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from app.core.config import enrich_app_secret, settings
from app.core.exceptions import (
    BaseAppException,
    app_exception_handler,
    validation_exception_handler,
    global_exception_handler
)
from app.db.mongo import MongoDBManager
from app.middleware.auth import AuthMiddleware
from app.modules.customer.router import router as customer_router
from app.modules.user.router import router as user_router
from app.modules.profile.router import router as profile_router
from app.modules.order.router import router as order_router
from app.utils.app_constant import COLL_TODO_APP_SECRET
from app.core.logging_config import setup_logging

# Initialize logging
setup_logging()

logger = logging.getLogger(__name__)


def load_secrets():
    """Initial secret loading from MongoDB."""
    db_name = settings.data_base
    db_coll = COLL_TODO_APP_SECRET
    logger.info(f"Loading secrets from {db_name}.{db_coll}")
    try:
        MongoDBManager.initialize()
        db = MongoDBManager.get_db()
        secret_doc = db[db_coll].find_one({})
        
        if not secret_doc:
            logger.critical(f"CRITICAL: No configuration found in {db_name}.{db_coll}. Application cannot start.")
            sys.exit(1)
            
        enrich_app_secret(secret_doc)
        logger.info("Secrets loaded and enriched successfully")
        
    except Exception as e:
        logger.critical(f"FATAL ERROR during startup: {str(e)}")
        sys.exit(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application starting up")
    load_secrets()
    # Initialize Telemetry
    # from app.core.config import get_otel_config # (if we have it)
    # TelemetryManager.initialize(get_otel_config())
    
    yield
    # Shutdown
    logger.info("Application shutting down")
    MongoDBManager.close()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Tailor App",
        lifespan=lifespan)

    app.add_middleware(AuthMiddleware)

    # Middleware
    # app.add_middleware(
    #    CORSMiddleware,
    #    allow_origins=["*"],
    #    allow_credentials=True,
    #    allow_methods=["*"],
    #    allow_headers=["*"],
    #)

    # Exception Handlers
    app.add_exception_handler(BaseAppException, app_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # Routes
    api_prefix = "/tailor/api/v1"
    app.include_router(user_router, prefix=api_prefix)
    app.include_router(customer_router, prefix=api_prefix)
    app.include_router(profile_router, prefix=api_prefix)
    app.include_router(order_router, prefix=api_prefix)

    return app

app = create_app()