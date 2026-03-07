import asyncio
import shutil
from pathlib import Path

import redis.asyncio as redis
from sqlalchemy import text

from app.config import get_settings
from app.db.session import async_session_factory

settings = get_settings()


async def cleanup():
    print("🧹 Starting ExcellentInsight Cleanup Process...")

    # 1. Clear Uploads
    upload_path = Path(settings.STORAGE_LOCAL_PATH)
    if upload_path.exists():
        print(f"📁 Clearing files in {upload_path}...")
        for item in upload_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        print("✅ Uploads cleared.")
    else:
        print("ℹ️ Uploads directory not found. Skipping.")

    # 2. Clear Database (Analysis Jobs)
    print("🗄️ Truncating analysis_jobs table...")
    async with async_session_factory() as db:
        try:
            # Using TRUNCATE with CASCADE to ensure related data is cleared
            # and RESTART IDENTITY to reset IDs
            await db.execute(text("TRUNCATE TABLE analysis_jobs RESTART IDENTITY CASCADE"))
            await db.commit()
            print("✅ Database jobs cleared.")
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
            await db.rollback()

    # 3. Flush Redis
    print("🚀 Flushing Redis cache...")
    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.flushall()
        await r.close()
        print("✅ Redis flushed.")
    except Exception as e:
        print(f"❌ Error flushing Redis: {e}")

    print("\n✨ Cleanup Complete! ExcellentInsight is now reset for fresh analysis.")


if __name__ == "__main__":
    asyncio.run(cleanup())
