from json import loads, dumps

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.app import App
from app.models.rule import Rule
from app.models.user import User

router = APIRouter(prefix="/apps/{app_id}/rules", tags=["rules"])
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
def rules_list(
    app_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_obj = get_app_or_404(db, app_id)
    ensure_access(app_obj, current_user)

    rules = db.scalars(
        select(Rule)
        .where(Rule.app_id == app_id)
        .order_by(Rule.priority.asc(), Rule.id.desc())
    ).all()
    rules_pretty = {
        rule.id: dumps(rule.action_config or {}, ensure_ascii=False, indent=2)
        for rule in rules
    }
    return templates.TemplateResponse(
        request=request,
        name="rules.html",
        context={
            "app_obj": app_obj,
            "rules": rules,
            "current_user": current_user,
            "rules_pretty": rules_pretty,
        },
    )


@router.post("/create")
def create_rule(
    app_id: int,
    name: str = Form(...),
    description: str = Form(""),
    enabled: str = Form("true"),
    priority: int = Form(100),
    http_method: str = Form(""),
    host_pattern: str = Form(""),
    path_pattern: str = Form(""),
    content_type_pattern: str = Form(""),
    action_type: str = Form(...),
    action_config_json: str = Form("{}"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_obj = get_app_or_404(db, app_id)
    ensure_access(app_obj, current_user)

    try:
        action_config = loads(action_config_json)
        if not isinstance(action_config, dict):
            raise ValueError("action_config_json must be a JSON object")
    except Exception as e:
        return PlainTextResponse(f"Invalid action_config_json: {e}", status_code=400)

    rule = Rule(
        app_id=app_id,
        name=name.strip(),
        description=description.strip() or None,
        enabled=enabled.lower() == "true",
        priority=priority,
        http_method=http_method.strip() or None,
        host_pattern=host_pattern.strip() or None,
        path_pattern=path_pattern.strip() or None,
        content_type_pattern=content_type_pattern.strip() or None,
        action_type=action_type.strip(),
        action_config=action_config,
    )
    db.add(rule)
    db.commit()

    return RedirectResponse(url=f"/apps/{app_id}/rules/", status_code=303)


@router.get("/{rule_id}/edit-config", response_class=HTMLResponse)
def edit_rule_config_form(
    app_id: int,
    rule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_obj = get_app_or_404(db, app_id)
    ensure_access(app_obj, current_user)

    rule = db.scalar(
        select(Rule).where(Rule.id == rule_id, Rule.app_id == app_id)
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return templates.TemplateResponse(
        request=request,
        name="rule_edit_config.html",
        context={
            "app_obj": app_obj,
            "rule": rule,
            "action_config_pretty": dumps(rule.action_config or {}, ensure_ascii=False, indent=2),
        },
    )


@router.post("/{rule_id}/edit-config")
def edit_rule_config_submit(
    app_id: int,
    rule_id: int,
    action_config_json: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_obj = get_app_or_404(db, app_id)
    ensure_access(app_obj, current_user)

    rule = db.scalar(
        select(Rule).where(Rule.id == rule_id, Rule.app_id == app_id)
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    try:
        action_config = loads(action_config_json)
        if not isinstance(action_config, dict):
            raise ValueError("action_config_json must be a JSON object")
    except Exception as e:
        return PlainTextResponse(f"Invalid action_config_json: {e}", status_code=400)

    rule.action_config = action_config
    db.commit()

    return RedirectResponse(url=f"/apps/{app_id}/rules/", status_code=303)


@router.post("/{rule_id}/delete")
def delete_rule(
    app_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_obj = get_app_or_404(db, app_id)
    ensure_access(app_obj, current_user)

    rule = db.scalar(
        select(Rule).where(Rule.id == rule_id, Rule.app_id == app_id)
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()

    return RedirectResponse(url=f"/apps/{app_id}/rules/", status_code=303)


@router.post("/{rule_id}/toggle")
def toggle_rule(
    app_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_obj = get_app_or_404(db, app_id)
    ensure_access(app_obj, current_user)

    rule = db.scalar(
        select(Rule).where(Rule.id == rule_id, Rule.app_id == app_id)
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.enabled = not rule.enabled
    db.commit()

    return RedirectResponse(url=f"/apps/{app_id}/rules/", status_code=303)