import json
import os
import re
from typing import Any

RULES_PATH = os.path.join(os.path.dirname(__file__), "rules.json")


def load_rules() -> list[dict[str, Any]]:
    try:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception as e:
        print("LOAD_RULES_ERROR:", e)
    return []


def match_rule(flow, rule: dict[str, Any]) -> bool:
    if not rule.get("enabled", True):
        return False

    host = str(rule.get("host", "")).strip()
    path_contains = str(rule.get("path_contains", "")).strip()

    if host and flow.request.host != host:
        return False

    if path_contains and path_contains not in flow.request.path:
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


def apply_regex_replacements(text: str, replacements: list[dict[str, Any]]) -> tuple[str, bool]:
    changed = False

    for i, item in enumerate(replacements, start=1):
        pattern = item.get("pattern")
        replace = item.get("replace", "")
        flags_value = 0

        flags = item.get("flags", [])
        if "IGNORECASE" in flags:
            flags_value |= re.IGNORECASE
        if "MULTILINE" in flags:
            flags_value |= re.MULTILINE
        if "DOTALL" in flags:
            flags_value |= re.DOTALL

        if not isinstance(pattern, str):
            print(f"REGEX_{i}: invalid pattern")
            continue

        try:
            matches = list(re.finditer(pattern, text, flags=flags_value))
        except Exception as e:
            print(f"REGEX_{i}_COMPILE_ERROR:", e)
            continue

        print(f"REGEX_{i}_PATTERN: {pattern}")
        print(f"REGEX_{i}_MATCHES_COUNT: {len(matches)}")

        if matches:
            preview = matches[0].group(0)
            if len(preview) > 200:
                preview = preview[:200] + "..."
            print(f"REGEX_{i}_FIRST_MATCH: {preview}")
        else:
            print(f"REGEX_{i}_FIRST_MATCH: <none>")

        new_text = re.sub(pattern, replace, text, flags=flags_value)

        if new_text != text:
            print(f"REGEX_{i}: CHANGED")
            text = new_text
            changed = True
        else:
            print(f"REGEX_{i}: NO MATCH")

    return text, changed


def response(flow):
    if flow.response is None:
        return

    content_type = flow.response.headers.get("content-type", "").lower()

    print("=" * 80)
    print("HOST:", flow.request.host)
    print("PATH:", flow.request.path)
    print("METHOD:", flow.request.method)
    print("CONTENT-TYPE:", content_type)

    original_text = flow.response.get_text(strict=False)
    if len(original_text) > 500:
        body_preview = original_text[:500] + "..."
    else:
        body_preview = original_text
    print("BODY_PREVIEW:", body_preview)

    rules = load_rules()
    print("RULES_COUNT:", len(rules))

    changed = False
    updated_text = original_text

    for idx, rule in enumerate(rules, start=1):
        matched = match_rule(flow, rule)
        print(f"RULE_{idx}_MATCHED:", matched)

        if not matched:
            continue

        mode = rule.get("mode", "json_update")
        print(f"RULE_{idx}_MODE:", mode)

        if mode == "regex_replace":
            replacements = rule.get("replacements", [])
            if not isinstance(replacements, list):
                print(f"RULE_{idx}: replacements is not list")
                continue

            updated_text, regex_changed = apply_regex_replacements(updated_text, replacements)
            if regex_changed:
                changed = True

        elif mode == "json_update":
            if "application/json" not in content_type:
                print(f"RULE_{idx}: SKIP json_update, not json")
                continue

            try:
                data = json.loads(updated_text)
            except Exception as e:
                print(f"RULE_{idx}_JSON_PARSE_ERROR:", e)
                continue

            updates = rule.get("updates", {})
            if not isinstance(updates, dict):
                print(f"RULE_{idx}: updates is not dict")
                continue

            rule_changed = False
            for dotted_key, new_value in updates.items():
                ok = set_nested_value(data, dotted_key, new_value)
                print(f"RULE_{idx}_UPDATE {dotted_key} -> {new_value} | success={ok}")
                if ok:
                    rule_changed = True

            if rule_changed:
                updated_text = json.dumps(data, ensure_ascii=False)
                changed = True

        else:
            print(f"RULE_{idx}: unknown mode {mode}")

    if changed:
        flow.response.text = updated_text
        print("RESPONSE_CHANGED: YES")
        if len(updated_text) > 500:
            changed_preview = updated_text[:500] + "..."
        else:
            changed_preview = updated_text
        print("CHANGED_BODY_PREVIEW:", changed_preview)
    else:
        print("RESPONSE_CHANGED: NO")
