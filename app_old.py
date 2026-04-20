import json
import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(__file__)
RULES_PATH = os.path.join(BASE_DIR, "rules.json")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = FastAPI()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def load_rules():
    if not os.path.exists(RULES_PATH):
        return []

    try:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_rules(rules):
    tmp_path = RULES_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, RULES_PATH)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    rules = load_rules()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "rules": rules,
        },
    )


@app.get("/raw", response_class=PlainTextResponse)
async def raw_rules():
    if not os.path.exists(RULES_PATH):
        return "[]"
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return f.read()


@app.post("/add")
async def add_rule(
    enabled: str = Form("true"),
    host: str = Form(""),
    path_contains: str = Form(""),
    mode: str = Form(...),
    replacements_json: str = Form("[]"),
    updates_json: str = Form("{}"),
):
    rules = load_rules()

    rule = {
        "enabled": enabled.lower() == "true",
        "host": host.strip(),
        "path_contains": path_contains.strip(),
        "mode": mode,
    }

    if mode == "regex_replace":
        try:
            replacements = json.loads(replacements_json)
            if not isinstance(replacements, list):
                raise ValueError("replacements_json must be a JSON array")
        except Exception as e:
            return PlainTextResponse(
                f"Ошибка в replacements_json: {e}",
                status_code=400,
            )
        rule["replacements"] = replacements

    elif mode == "json_update":
        try:
            updates = json.loads(updates_json)
            if not isinstance(updates, dict):
                raise ValueError("updates_json must be a JSON object")
        except Exception as e:
            return PlainTextResponse(
                f"Ошибка в updates_json: {e}",
                status_code=400,
            )
        rule["updates"] = updates

    else:
        return PlainTextResponse("Неизвестный mode", status_code=400)

    rules.append(rule)
    save_rules(rules)
    return RedirectResponse("/", status_code=303)


@app.post("/delete/{rule_id}")
async def delete_rule(rule_id: int):
    rules = load_rules()
    if 0 <= rule_id < len(rules):
        del rules[rule_id]
        save_rules(rules)
    return RedirectResponse("/", status_code=303)


@app.post("/toggle/{rule_id}")
async def toggle_rule(rule_id: int):
    rules = load_rules()
    if 0 <= rule_id < len(rules):
        rules[rule_id]["enabled"] = not bool(rules[rule_id].get("enabled", True))
        save_rules(rules)
    return RedirectResponse("/", status_code=303)


@app.post("/update/{rule_id}")
async def update_rule(
    rule_id: int,
    enabled: str = Form("true"),
    host: str = Form(""),
    path_contains: str = Form(""),
    mode: str = Form(...),
    replacements_json: str = Form("[]"),
    updates_json: str = Form("{}"),
):
    rules = load_rules()

    if not (0 <= rule_id < len(rules)):
        return PlainTextResponse("Правило не найдено", status_code=404)

    updated_rule = {
        "enabled": enabled.lower() == "true",
        "host": host.strip(),
        "path_contains": path_contains.strip(),
        "mode": mode,
    }

    if mode == "regex_replace":
        try:
            replacements = json.loads(replacements_json)
            if not isinstance(replacements, list):
                raise ValueError("replacements_json must be a JSON array")
        except Exception as e:
            return PlainTextResponse(
                f"Ошибка в replacements_json: {e}",
                status_code=400,
            )
        updated_rule["replacements"] = replacements

    elif mode == "json_update":
        try:
            updates = json.loads(updates_json)
            if not isinstance(updates, dict):
                raise ValueError("updates_json must be a JSON object")
        except Exception as e:
            return PlainTextResponse(
                f"Ошибка в updates_json: {e}",
                status_code=400,
            )
        updated_rule["updates"] = updates

    else:
        return PlainTextResponse("Неизвестный mode", status_code=400)

    rules[rule_id] = updated_rule
    save_rules(rules)
    return RedirectResponse("/", status_code=303)
