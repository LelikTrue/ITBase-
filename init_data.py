import asyncio
import logging
import sys
from app.db.database import AsyncSessionFactory
from app.services.initial_data_service import InitialDataService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting initial data seeding process...")

    async with AsyncSessionFactory() as session:
        service = InitialDataService(session)
        try:
            await service.load_from_yaml("initial_data.yaml")
            logger.info("✅ SUCCESS: Database seeded successfully.")
        except Exception as e:
            logger.error(f"❌ FAILED: Data seeding error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
