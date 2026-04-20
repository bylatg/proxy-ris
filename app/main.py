from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
from app.routers import auth, apps, rules, internal_proxy, templates

app = FastAPI(title=settings.app_name)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.include_router(auth.router)
app.include_router(apps.router)
app.include_router(rules.router)
app.include_router(internal_proxy.router)
app.include_router(templates.router)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def root():
    return RedirectResponse(url="/apps/", status_code=303)
