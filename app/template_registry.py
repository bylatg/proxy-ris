import re
from typing import Any
# ^/(userinfo|v1/accounts_light|app/bank/messenger/conversations|app/bank/messenger/userInfo|api/prefill/profile/contact)(/.*)?$
# ^.*\.t-bank-app\.ru$
TEMPLATE_REGISTRY: dict[str, dict[str, Any]] = {
    "replace_name": {
        "code": "replace_name",
        "name": "Замена данных в профиле (email / телефон , имя)",
        "description": "Заменяет данные в профиле ",
        "system_defaults": {
            "priority": 100,
            "http_method": "GET",
            "host_pattern": r"^.*\.t-bank-app\.ru$",
            "path_pattern": r"^/(userinfo|v1/accounts_light|app/bank/messenger/conversations|app/bank/messenger/userInfo|api/prefill/profile/contact)(/.*)?$",
            "content_type_pattern": r"application/json",
            "action_type": "regex_replace",
        },
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
        ],
    },
    "replace_amount": {
        "code": "replace_amount",
        "name": "Замена значений суммы только в истории операции",
        "description": "Заменяет  суммы на другое только в истории.",
        "system_defaults": {
            "priority": 100,
            "http_method": "GET",
            "host_pattern": r"^api\.t-bank-app\.ru$",
            "path_pattern": r"^/v1/operations.*",
            "content_type_pattern": r"application/json",
            "action_type": "regex_replace",
        },
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
        ],
    },
    "replace_history": {
        "code": "replace_history",
        "name": "Замена совпадения только в истории операции",
        "description": "Заменяет  совпадения на другое только в истории.",
        "system_defaults": {
            "priority": 100,
            "http_method": "GET",
            "host_pattern": r"^api\.t-bank-app\.ru$",
            "path_pattern": r"^/v1/operations.*",
            "action_type": "regex_replace",
        },
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
        ],
    },
    "replace_sup": {
        "code": "replace_sup",
        "name": "Замена значений в чате с поддержкой",
        "description": "Замена значений в чате с поддержкой.",
        "system_defaults": {
            "priority": 100,
            "http_method": "GET",
            "host_pattern": r"^tm\.t-bank-app\.ru$",
            "path_pattern": r"^/app/bank/messenger/conversations(?:/.*)?$",
            "content_type_pattern": r"application/json.*",
            "action_type": "regex_replace",
        },
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
        ],
    },
}


APP_TEMPLATE_MAP: dict[str, list[str]] = {
    "tbank": ["replace_name", "replace_amount", "replace_sup", "replace_history"],
    # "tbank": ["replace_name", "replace_amount"],
    # "myshop": ["replace_name"],
}


def get_templates_for_app_slug(app_slug: str) -> list[dict[str, Any]]:
    normalized_slug = (app_slug or "").strip().lower()
    codes = APP_TEMPLATE_MAP.get(normalized_slug) or APP_TEMPLATE_MAP.get("default", [])
    return [TEMPLATE_REGISTRY[code] for code in codes if code in TEMPLATE_REGISTRY]


def build_rule_from_template(template_code: str, form_data: dict[str, Any]) -> dict[str, Any]:
    template = TEMPLATE_REGISTRY.get(template_code)
    if not template:
        raise ValueError(f"Unknown template_code: {template_code}")

    defaults = template.get("system_defaults", {})

    if template_code == "replace_name":
        old_value = str(form_data["old_value"]).strip()
        new_value = str(form_data["new_value"]).strip()

        return {
            "name": f"Replace text: {old_value} -> {new_value}",
            "description": template.get("description"),
            "enabled": True,
            "priority": defaults.get("priority", 100),
            "http_method": defaults.get("http_method"),
            "host_pattern": defaults.get("host_pattern"),
            "path_pattern": defaults.get("path_pattern"),
            "content_type_pattern": defaults.get("content_type_pattern"),
            "action_type": defaults.get("action_type", "regex_replace"),
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

        return {
        "name": f"Replace amount: {old_value} -> {new_value}",
        "description": template.get("description"),
        "enabled": True,
        "priority": defaults.get("priority", 100),
        "http_method": defaults.get("http_method"),
        "host_pattern": defaults.get("host_pattern"),
        "path_pattern": defaults.get("path_pattern"),
        "content_type_pattern": defaults.get("content_type_pattern"),
        "action_type": defaults.get("action_type", "regex_replace"),
        "action_config": {
            "replacements": [
                {
                    "pattern": rf'"value"\s*:\s*{re.escape(old_value)}',
                    "replace": f'"value": {new_value}',
                }
            ]
        },
    }
    if template_code == "replace_sup":
        old_value = str(form_data["old_value"]).strip()
        new_value = str(form_data["new_value"]).strip()

        return {
            "name": f"Replace amount: {old_value} -> {new_value}",
            "description": template.get("description"),
            "enabled": True,
            "priority": defaults.get("priority", 100),
            "http_method": defaults.get("http_method"),
            "host_pattern": defaults.get("host_pattern"),
            "path_pattern": defaults.get("path_pattern"),
            "content_type_pattern": defaults.get("content_type_pattern"),
            "action_type": defaults.get("action_type", "regex_replace"),
            "action_config": {
                "replacements": [
                    {
                        "pattern": re.escape(old_value),
                        "replace": new_value,
                    }
                ]
            },
        }
    if template_code == "replace_history":
        old_value = str(form_data["old_value"]).strip()
        new_value = str(form_data["new_value"]).strip()

        return {
            "name": f"Replace amount: {old_value} -> {new_value}",
            "description": template.get("description"),
            "enabled": True,
            "priority": defaults.get("priority", 100),
            "http_method": defaults.get("http_method"),
            "host_pattern": defaults.get("host_pattern"),
            "path_pattern": defaults.get("path_pattern"),
            "content_type_pattern": defaults.get("content_type_pattern"),
            "action_type": defaults.get("action_type", "regex_replace"),
            "action_config": {
                "replacements": [
                    {
                        "pattern": re.escape(old_value),
                        "replace": new_value,
                    }
                ]
            },
        }
    raise ValueError(f"Unknown template_code: {template_code}")