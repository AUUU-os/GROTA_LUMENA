import logging
from sqlmodel import SQLModel, create_engine
from corex.config import settings

logger = logging.getLogger("SCHEMA-EVOLVER")

class SchemaEvolver:
    """Handles dynamic schema expansion for the Dream Engine."""
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite"))

    async def evolve_schema(self):
        """Creates missing tables based on registered models."""
        logger.info("đź§Ş Initiating Automated Schema Evolution...")
        try:
            # In a real async environment, we run this sync call in a thread or use specialized libs
            SQLModel.metadata.create_all(self.engine)
            logger.info("âś… Schema synchronized with OMEGA models.")
        except Exception as e:
            logger.error(f"Schema Evolution failed: {e}")

schema_evolver = SchemaEvolver()
