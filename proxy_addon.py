import json
import os
import re
import time
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


BACKEND_BASE_URL = os.getenv("PROXY_BACKEND_BASE_URL", "http://app:8000")
INTERNAL_API_TOKEN = os.getenv("PROXY_INTERNAL_TOKEN", "oh9HPBSXyccTU5cJjEHEAv2nnDrqJhet")
APP_ID = int(os.getenv("PROXY_APP_ID", "1"))
CACHE_TTL_SECONDS = int(os.getenv("PROXY_CACHE_TTL_SECONDS", "5"))

_rules_cache: dict[str, Any] = {
    "fetched_at": 0,
    "rules": [],
}


def fetch_rules() -> list[dict[str, Any]]:
    global _rules_cache

    now = time.time()
    if now - _rules_cache["fetched_at"] < CACHE_TTL_SECONDS:
        return _rules_cache["rules"]

    url = f"{BACKEND_BASE_URL}/internal/proxy/apps/{APP_ID}/rules"

    try:
        req = Request(
            url,
            headers={"X-Internal-Token": INTERNAL_API_TOKEN},
            method="GET",
        )
        with urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)

        rules = data.get("rules", [])
        if not isinstance(rules, list):
            rules = []

        _rules_cache = {
            "fetched_at": now,
            "rules": rules,
        }
        print(f"[proxy] loaded {len(rules)} rules from backend")
        return rules

    except HTTPError as e:
        print(f"[proxy] failed to fetch rules: HTTP {e.code}")
    except URLError as e:
        print(f"[proxy] failed to fetch rules: {e}")
    except Exception as e:
        print(f"[proxy] failed to fetch rules: {e}")

    return _rules_cache["rules"]

def match_regex(pattern: str | None, value: str | None) -> bool:
    if not pattern:
        return True
    if value is None:
        return False
    try:
        return re.search(pattern, value) is not None
    except re.error as e:
        print(f"[proxy] invalid regex pattern={pattern!r}: {e}")
        return False


def match_rule(flow, rule: dict[str, Any]) -> bool:
    http_method = rule.get("http_method")
    host_pattern = rule.get("host_pattern")
    path_pattern = rule.get("path_pattern")
    content_type_pattern = rule.get("content_type_pattern")

    if http_method and flow.request.method.upper() != str(http_method).upper():
        return False

    if not match_regex(host_pattern, flow.request.host):
        return False

    if not match_regex(path_pattern, flow.request.path):
        return False

    content_type = flow.response.headers.get("content-type", "")
    if not match_regex(content_type_pattern, content_type):
        return False

    return True


def set_nested_value(obj: Any, dotted_key: str, value: Any) -> bool:
    parts = dotted_key.split(".")
    cur = obj

    for part in parts[:-1]:
        if isinstance(cur, dict):
            if part not in cur:
                return False
            cur = cur[part]
        elif isinstance(cur, list):
            if not part.isdigit():
                return False
            idx = int(part)
            if idx < 0 or idx >= len(cur):
                return False
            cur = cur[idx]
        else:
            return False

    last = parts[-1]

    if isinstance(cur, dict):
        if last not in cur:
            return False
        cur[last] = value
        return True

    if isinstance(cur, list):
        if not last.isdigit():
            return False
        idx = int(last)
        if idx < 0 or idx >= len(cur):
            return False
        cur[idx] = value
        return True

    return False


def apply_regex_replace(text: str, action_config: dict[str, Any]) -> tuple[str, bool]:
    replacements = action_config.get("replacements", [])
    if not isinstance(replacements, list):
        return text, False

    changed = False

    for item in replacements:
        pattern = item.get("pattern")
        replace = item.get("replace", "")
        flags = item.get("flags", [])

        if not isinstance(pattern, str):
            continue

        flags_value = 0
        if "IGNORECASE" in flags:
            flags_value |= re.IGNORECASE
        if "MULTILINE" in flags:
            flags_value |= re.MULTILINE
        if "DOTALL" in flags:
            flags_value |= re.DOTALL

        try:
            new_text = re.sub(pattern, replace, text, flags=flags_value)
        except re.error as e:
            print(f"[proxy] regex error in rule pattern={pattern!r}: {e}")
            continue

        if new_text != text:
            changed = True
            text = new_text

    return text, changed


def apply_json_update(text: str, action_config: dict[str, Any]) -> tuple[str, bool]:
    updates = action_config.get("updates", {})
    if not isinstance(updates, dict):
        return text, False

    try:
        data = json.loads(text)
    except Exception:
        return text, False

    changed = False

    for dotted_key, new_value in updates.items():
        ok = set_nested_value(data, dotted_key, new_value)
        if ok:
            changed = True

    if not changed:
        return text, False

    return json.dumps(data, ensure_ascii=False), True


def apply_mock_response(flow, action_config: dict[str, Any]) -> bool:
    status_code = action_config.get("status_code", 200)
    content_type = action_config.get("content_type", "application/json")
    body = action_config.get("body", {})

    if isinstance(body, (dict, list)):
        body_text = json.dumps(body, ensure_ascii=False)
    else:
        body_text = str(body)

    flow.response.status_code = int(status_code)
    flow.response.text = body_text
    flow.response.headers["content-type"] = content_type
    return True


def response(flow):
    if flow.response is None:
        return

    rules = fetch_rules()
    if not rules:
        return

    original_text = flow.response.get_text(strict=False)
    updated_text = original_text
    changed = False

    for rule in rules:
        if not match_rule(flow, rule):
            continue

        action_type = rule.get("action_type")
        action_config = rule.get("action_config") or {}

        print(f"[proxy] matched rule id={rule.get('id')} name={rule.get('name')} action={action_type}")

        if action_type == "regex_replace":
            updated_text, rule_changed = apply_regex_replace(updated_text, action_config)
            if rule_changed:
                changed = True

        elif action_type == "json_update":
            updated_text, rule_changed = apply_json_update(updated_text, action_config)
            if rule_changed:
                changed = True

        elif action_type == "mock_response":
            if apply_mock_response(flow, action_config):
                print(f"[proxy] mock_response applied for rule id={rule.get('id')}")
                return

        else:
            print(f"[proxy] unknown action_type={action_type!r}")

    if changed:
        flow.response.text = updated_text
        print("[proxy] response changed")
