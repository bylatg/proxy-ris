from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.app import App
from app.models.user import User

router = APIRouter(prefix="/apps", tags=["apps"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def apps_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(App)

    if not current_user.is_admin:
        stmt = stmt.where(App.owner_user_id == current_user.id)

    apps = db.scalars(stmt.order_by(App.id.desc())).all()

    return templates.TemplateResponse(
        request=request,
        name="apps.html",
        context={
            "apps": apps,
            "current_user": current_user,
        },
    )


@router.post("/create")
def create_app(
    name: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_obj = App(
        name=name.strip(),
        slug=slug.strip(),
        description=description.strip() or None,
        owner_user_id=current_user.id,
        is_active=True,
    )
    db.add(app_obj)
    db.commit()

    return RedirectResponse(url="/apps/", status_code=303)
