import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

import app.models.api_key
import app.models.job
import app.models.job_transition
import app.models.organization
import app.models.pipeline_state
import app.models.pipeline_telemetry

# Import all models to ensure they are registered with Base metadata
import app.models.user
from app.db.session import engine
from app.models.base import Base


async def init_db():
    print("🚀 Initializing ExcellentInsight Database...")

    try:
        async with engine.begin() as conn:
            # Create extension for UUID if needed (if using postgres)
            if not engine.url.drivername.startswith("sqlite"):
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))

            # Create tables
            print("Creating tables if they don't exist...")
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Database initialization complete!")
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_db())
