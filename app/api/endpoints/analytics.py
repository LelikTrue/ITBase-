# Path: app/api/endpoints/analytics.py
"""
API endpoints для аналитики и дашборда.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_from_session, get_db
from app.db.repositories.analytics_repo import SqlAlchemyAnalyticsRepository
from app.models.user import User
from app.schemas.analytics import DashboardDataDTO

router = APIRouter()


@router.get("/dashboard", response_model=DashboardDataDTO, name="get_analytics_dashboard")
async def get_analytics_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_session),
):
    """
    Получить данные для аналитического дашборда (JSON).
    """
    repo = SqlAlchemyAnalyticsRepository(db)
    return await repo.get_dashboard_metrics()
