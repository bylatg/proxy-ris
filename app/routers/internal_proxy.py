from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.app import App
from app.models.rule import Rule

router = APIRouter(prefix="/internal/proxy", tags=["internal-proxy"])


def check_internal_token(x_internal_token: str | None = Header(default=None)):
    expected = getattr(settings, "internal_api_token", None)
    if not expected:
        raise HTTPException(status_code=500, detail="Internal API token is not configured")
    if x_internal_token != expected:
        raise HTTPException(status_code=401, detail="Invalid internal token")


@router.get("/apps/{app_id}/rules")
def get_app_rules(
    app_id: int,
    _: None = Depends(check_internal_token),
    db: Session = Depends(get_db),
):
    app_obj = db.scalar(select(App).where(App.id == app_id, App.is_active == True))
    if not app_obj:
        raise HTTPException(status_code=404, detail="App not found")

    rules = db.scalars(
        select(Rule)
        .where(Rule.app_id == app_id, Rule.enabled == True)
        .order_by(Rule.priority.asc(), Rule.id.asc())
    ).all()

    return {
        "app": {
            "id": app_obj.id,
            "name": app_obj.name,
            "slug": app_obj.slug,
        },
        "rules": [
            {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "enabled": rule.enabled,
                "priority": rule.priority,
                "http_method": rule.http_method,
                "host_pattern": rule.host_pattern,
                "path_pattern": rule.path_pattern,
                "content_type_pattern": rule.content_type_pattern,
                "action_type": rule.action_type,
                "action_config": rule.action_config,
            }
            for rule in rules
        ],
    }
