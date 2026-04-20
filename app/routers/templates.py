from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.app import App
from app.models.rule import Rule
from app.models.user import User
from app.template_registry import (
    TEMPLATE_REGISTRY,
    build_rule_from_template,
    get_templates_for_app_slug,
)

router = APIRouter(prefix="/apps/{app_id}/templates", tags=["templates"])
templates = Jinja2Templates(directory="templates")


def get_app_or_404(db: Session, app_id: int) -> App:
    app_obj = db.scalar(select(App).where(App.id == app_id))
    if not app_obj:
        raise HTTPException(status_code=404, detail="App not found")
    return app_obj


def ensure_access(app_obj: App, current_user: User) -> None:
    if current_user.is_admin:
        return
    if app_obj.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/", response_class=HTMLResponse)
def template_list(
    app_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_obj = get_app_or_404(db, app_id)
    ensure_access(app_obj, current_user)

    available_templates = get_templates_for_app_slug(app_obj.slug)

    return templates.TemplateResponse(
        request=request,
        name="templates_list.html",
        context={
            "app_obj": app_obj,
            "template_items": available_templates,
        },
    )


@router.get("/{template_code}", response_class=HTMLResponse)
def template_form(
    app_id: int,
    template_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_obj = get_app_or_404(db, app_id)
    ensure_access(app_obj, current_user)

    template_item = TEMPLATE_REGISTRY.get(template_code)
    if not template_item:
        raise HTTPException(status_code=404, detail="Template not found")

    return templates.TemplateResponse(
        request=request,
        name="template_form.html",
        context={
            "app_obj": app_obj,
            "template_item": template_item,
        },
    )


@router.post("/{template_code}/create")
async def create_rule_from_template(
    app_id: int,
    template_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_obj = get_app_or_404(db, app_id)
    ensure_access(app_obj, current_user)

    template_item = TEMPLATE_REGISTRY.get(template_code)
    if not template_item:
        raise HTTPException(status_code=404, detail="Template not found")

    form = await request.form()
    form_data = dict(form)

    generated = build_rule_from_template(template_code, form_data)

    rule = Rule(
        app_id=app_id,
        name=generated["name"],
        description=generated["description"],
        enabled=generated["enabled"],
        priority=generated["priority"],
        http_method=generated["http_method"],
        host_pattern=generated["host_pattern"],
        path_pattern=generated["path_pattern"],
        content_type_pattern=generated["content_type_pattern"],
        action_type=generated["action_type"],
        action_config=generated["action_config"],
    )
    db.add(rule)
    db.commit()

    return RedirectResponse(url=f"/apps/{app_id}/rules/", status_code=303)
