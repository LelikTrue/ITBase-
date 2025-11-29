# Path: app/schemas/analytics.py
"""
Схемы данных для аналитического дашборда.
Используются для строгой типизации API ответов.
"""
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class FinancialStatsDTO(BaseModel):
    """Финансовые метрики активов."""

    total_cost: float = Field(..., description='Полная стоимость всех активов')
    cost_in_use: float = Field(
        ..., description='Стоимость активов в эксплуатации'
    )
    cost_in_stock: float = Field(..., description='Стоимость активов на складе')
    avg_wear_percent: float = Field(..., description='Средний процент износа')

    model_config = ConfigDict(from_attributes=True)


class AssetDistributionDTO(BaseModel):
    """Распределение активов по категориям (статус/тип)."""

    label: str = Field(..., description='Название категории')
    count: int = Field(..., description='Количество активов')
    total_price: float = Field(..., description='Суммарная стоимость')

    model_config = ConfigDict(from_attributes=True)


class RiskAssetDTO(BaseModel):
    """Проблемный актив, требующий внимания."""

    id: int
    name: str
    inventory_number: str
    issue: str = Field(
        ...,
        description='Тип проблемы: CRITICAL_WEAR | WARRANTY_EXPIRED | OLD_ASSET',
    )
    criticality: str = Field(..., description='Критичность: HIGH | MEDIUM')
    date_val: date | None = Field(
        None, description='Дата окончания гарантии или покупки'
    )

    model_config = ConfigDict(from_attributes=True)


class DashboardDataDTO(BaseModel):
    """Полный набор данных для дашборда."""

    financials: FinancialStatsDTO
    by_status: list[AssetDistributionDTO]
    by_type: list[AssetDistributionDTO]
    risks: list[RiskAssetDTO]

    model_config = ConfigDict(from_attributes=True)
