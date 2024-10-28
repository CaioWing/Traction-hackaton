from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
import pymongo
import logging
from contextlib import asynccontextmanager, contextmanager
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection with retry logic
class DatabaseConnection:
    def __init__(self):
        self.client: Optional[pymongo.MongoClient] = None
        self.db: Optional[pymongo.database.Database] = None
        self.is_connected = False

    def connect(self):
        if not self.is_connected:
            try:
                self.client = pymongo.MongoClient(
                    "mongodb://localhost:27017/",
                    serverSelectionTimeoutMS=5000  # 5 second timeout
                )
                # Verify the connection
                self.client.server_info()
                self.db = self.client["Gearing"]
                self.is_connected = True
                logger.info("Successfully connected to MongoDB")
            except pymongo.errors.ServerSelectionTimeoutError:
                logger.warning("Could not connect to MongoDB. Running in no-database mode.")
                self.is_connected = False
            except Exception as e:
                logger.error(f"MongoDB connection error: {str(e)}")
                self.is_connected = False

    def get_db(self):
        if not self.is_connected:
            self.connect()
        return self.db if self.is_connected else None

    def close(self):
        if self.client:
            self.client.close()
            self.is_connected = False

@contextmanager
def get_db_context():
    """Context manager for database operations"""
    try:
        yield db_connection.get_db()
    except Exception as e:
        logger.error(f"Database operation error: {str(e)}")
        raise

# Create global database connection instance
db_connection = DatabaseConnection()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Initialize database connection
    logger.info("Starting up the application...")
    db_connection.connect()
    
    yield
    
    # Shutdown: Close database connection
    logger.info("Shutting down the application...")
    db_connection.close()

# Initialize FastAPI with lifespan
app = FastAPI(
    title="Gearing",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)