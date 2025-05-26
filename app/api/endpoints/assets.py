# app/api/endpoints/assets.py (фрагмент, только для подтверждения)
# ...
from sqlalchemy import func # Убедитесь, что func импортирован здесь

# ... другие роуты ...

@router.get("/dashboard", response_class=HTMLResponse, name="read_assets") # Важно: name="read_assets"
async def read_assets(request: Request, db: Session = Depends(get_db)):
    """
    Отображает список всех активов на дашборде.
    """
    try:
        assets = db.execute(
            select(Device)
            .options(
                joinedload(Device.device_model).joinedload(DeviceModel.manufacturer),
                joinedload(Device.asset_type),
                joinedload(Device.status),
                joinedload(Device.department),
                joinedload(Device.location),
                joinedload(Device.employee)
            )
            .order_by(Device.added_at.desc())
            .limit(10)
        ).scalars().all()

        device_types_count = db.execute(
            select(AssetType.name, func.count(Device.id))
            .join(Device, Device.asset_type_id == AssetType.id)
            .group_by(AssetType.name)
        ).all()

        device_statuses_count = db.execute(
            select(DeviceStatus.name, func.count(Device.id))
            .join(Device, Device.status_id == DeviceStatus.id)
            .group_by(DeviceStatus.name)
        ).all()

    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        assets = []
        device_types_count = []
        device_statuses_count = []

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "assets": assets,
            "device_types_count": device_types_count,
            "device_statuses_count": device_statuses_count
        }
    )