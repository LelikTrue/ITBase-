# Path: app/db/repositories/analytics_repo.py
"""
Репозиторий для аналитических запросов к БД.
Использует агрегацию на уровне SQL для производительности.
"""
from datetime import date, timedelta

from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset_type import AssetType
from app.models.device import Device
from app.models.device_status import DeviceStatus
from app.schemas.analytics import (
    AssetDistributionDTO,
    DashboardDataDTO,
    FinancialStatsDTO,
    RiskAssetDTO,
)

# Константы для бизнес-логики
# TODO: Вынести в конфигурацию или таблицу настроек
STATUS_IN_USE = ['В эксплуатации', 'Выдано']
STATUS_IN_STOCK = ['На складе', 'Резерв']
WEAR_THRESHOLD = 80  # %
OLD_ASSET_YEARS = 5


class SqlAlchemyAnalyticsRepository:
    """Репозиторий аналитики с SQL-агрегацией."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_dashboard_metrics(self) -> DashboardDataDTO:
        """
        Получает все метрики для дашборда в оптимизированном виде.

        Returns:
            DashboardDataDTO: Полный набор данных для дашборда
        """
        # 1. Финансовые метрики (агрегация на уровне БД)
        financials_stmt = select(
            func.coalesce(func.sum(Device.price), 0).label('total'),
            func.coalesce(
                func.sum(
                    case((DeviceStatus.name.in_(STATUS_IN_USE), Device.price), else_=0)
                ),
                0,
            ).label('in_use'),
            func.coalesce(
                func.sum(
                    case(
                        (DeviceStatus.name.in_(STATUS_IN_STOCK), Device.price), else_=0
                    )
                ),
                0,
            ).label('in_stock'),
            func.coalesce(func.avg(Device.current_wear_percentage), 0).label(
                'avg_wear'
            ),
        ).join(Device.status)

        fin_res = (await self._session.execute(financials_stmt)).one()

        financials = FinancialStatsDTO(
            total_cost=float(fin_res.total),
            cost_in_use=float(fin_res.in_use),
            cost_in_stock=float(fin_res.in_stock),
            avg_wear_percent=float(fin_res.avg_wear),
        )

        # 2. Распределение по статусам
        status_stmt = (
            select(
                DeviceStatus.name,
                func.count(Device.id).label('count'),
                func.coalesce(func.sum(Device.price), 0).label('total_price'),
            )
            .join(Device.status)
            .group_by(DeviceStatus.name)
            .order_by(desc(func.count(Device.id)))
        )

        status_res = await self._session.execute(status_stmt)
        by_status = [
            AssetDistributionDTO(
                label=row.name, count=row.count, total_price=float(row.total_price)
            )
            for row in status_res
        ]

        # 3. Распределение по типам
        type_stmt = (
            select(
                AssetType.name,
                func.count(Device.id).label('count'),
                func.coalesce(func.sum(Device.price), 0).label('total_price'),
            )
            .join(Device.asset_type)
            .group_by(AssetType.name)
            .order_by(desc(func.count(Device.id)))
        )

        type_res = await self._session.execute(type_stmt)
        by_type = [
            AssetDistributionDTO(
                label=row.name, count=row.count, total_price=float(row.total_price)
            )
            for row in type_res
        ]

        # 4. Риск-панель (топ проблемных активов)
        today = date.today()
        five_years_ago = today - timedelta(days=365 * OLD_ASSET_YEARS)

        risk_stmt = (
            select(Device)
            .where(
                or_(
                    Device.warranty_end_date < today,
                    Device.current_wear_percentage >= WEAR_THRESHOLD,
                    Device.purchase_date < five_years_ago,
                )
            )
            .limit(20)
        )

        risk_res = await self._session.execute(risk_stmt)
        risks: list[RiskAssetDTO] = []

        for dev in risk_res.scalars():
            issue = 'UNKNOWN'
            criticality = 'MEDIUM'
            date_ref = None

            # Приоритет: износ > гарантия > возраст
            if dev.current_wear_percentage and dev.current_wear_percentage >= WEAR_THRESHOLD:
                issue = 'CRITICAL_WEAR'
                criticality = 'HIGH'
            elif dev.warranty_end_date and dev.warranty_end_date < today:
                issue = 'WARRANTY_EXPIRED'
                date_ref = dev.warranty_end_date
            elif dev.purchase_date and dev.purchase_date < five_years_ago:
                issue = 'OLD_ASSET'
                date_ref = dev.purchase_date

            risks.append(
                RiskAssetDTO(
                    id=dev.id,
                    name=dev.name,
                    inventory_number=dev.inventory_number,
                    issue=issue,
                    criticality=criticality,
                    date_val=date_ref,
                )
            )

        return DashboardDataDTO(
            financials=financials, by_status=by_status, by_type=by_type, risks=risks
        )
