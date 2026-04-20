import re
from typing import Any


TEMPLATE_REGISTRY: dict[str, dict[str, Any]] = {
    "replace_name": {
        "code": "replace_name",
        "name": "Замена имени",
        "description": "Заменяет одно текстовое значение на другое в ответе.",
        "fields": [
            {
                "name": "old_value",
                "label": "Старое значение",
                "type": "text",
                "required": True,
            },
            {
                "name": "new_value",
                "label": "Новое значение",
                "type": "text",
                "required": True,
            },
            {
                "name": "host_pattern",
                "label": "Host pattern",
                "type": "text",
                "required": False,
                "default": ".*",
            },
            {
                "name": "path_pattern",
                "label": "Path pattern",
                "type": "text",
                "required": False,
                "default": ".*",
            },
            {
                "name": "content_type_pattern",
                "label": "Content-Type pattern",
                "type": "text",
                "required": False,
                "default": "application/json",
            },
        ],
    },
    "replace_amount": {
        "code": "replace_amount",
        "name": "Замена суммы",
        "description": "Заменяет одно числовое значение на другое.",
        "fields": [
            {
                "name": "old_value",
                "label": "Старое число",
                "type": "text",
                "required": True,
            },
            {
                "name": "new_value",
                "label": "Новое число",
                "type": "text",
                "required": True,
            },
            {
                "name": "host_pattern",
                "label": "Host pattern",
                "type": "text",
                "required": False,
                "default": ".*",
            },
            {
                "name": "path_pattern",
                "label": "Path pattern",
                "type": "text",
                "required": False,
                "default": ".*",
            },
            {
                "name": "content_type_pattern",
                "label": "Content-Type pattern",
                "type": "text",
                "required": False,
                "default": "application/json",
            },
        ],
    },
}


APP_TEMPLATE_MAP: dict[str, list[str]] = {
    "default": ["replace_name", "replace_amount"],
    # "tbank": ["replace_name", "replace_amount"],
    # "myshop": ["replace_name"],
}


def get_templates_for_app_slug(app_slug: str) -> list[dict[str, Any]]:
    codes = APP_TEMPLATE_MAP.get(app_slug, APP_TEMPLATE_MAP["default"])
    return [TEMPLATE_REGISTRY[code] for code in codes if code in TEMPLATE_REGISTRY]


def build_rule_from_template(template_code: str, form_data: dict[str, Any]) -> dict[str, Any]:
    if template_code == "replace_name":
        old_value = str(form_data["old_value"]).strip()
        new_value = str(form_data["new_value"]).strip()

        return {
            "name": f"Replace text: {old_value} -> {new_value}",
            "description": "Generated from template replace_name",
            "enabled": True,
            "priority": 100,
            "http_method": None,
            "host_pattern": form_data.get("host_pattern") or ".*",
            "path_pattern": form_data.get("path_pattern") or ".*",
            "content_type_pattern": form_data.get("content_type_pattern") or "application/json",
            "action_type": "regex_replace",
            "action_config": {
                "replacements": [
                    {
                        "pattern": re.escape(old_value),
                        "replace": new_value,
                    }
                ]
            },
        }

    if template_code == "replace_amount":
        old_value = str(form_data["old_value"]).strip()
        new_value = str(form_data["new_value"]).strip()

        escaped_old = re.escape(old_value)

        return {
            "name": f"Replace amount: {old_value} -> {new_value}",
            "description": "Generated from template replace_amount",
            "enabled": True,
            "priority": 100,
            "http_method": None,
            "host_pattern": form_data.get("host_pattern") or ".*",
            "path_pattern": form_data.get("path_pattern") or ".*",
            "content_type_pattern": form_data.get("content_type_pattern") or "application/json",
            "action_type": "regex_replace",
            "action_config": {
                "replacements": [
                    {
                        "pattern": escaped_old,
                        "replace": new_value,
                    }
                ]
            },
        }

    raise ValueError(f"Unknown template_code: {template_code}")
