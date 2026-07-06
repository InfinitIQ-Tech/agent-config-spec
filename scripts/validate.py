#!/usr/bin/env python3
"""Validate example manifests against the AgentConfig JSON Schema.

Every manifest in examples/ must validate; every manifest in
examples/invalid/ must fail validation. Exits non-zero on any surprise.

Requires: pip install jsonschema
"""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "agent-config.v2.schema.json"
EXAMPLES_DIR = ROOT / "examples"
INVALID_DIR = EXAMPLES_DIR / "invalid"


def best_error(validator: Draft202012Validator, instance: dict) -> str:
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    lines = []
    for error in errors:
        location = "$" + "".join(
            f"[{p}]" if isinstance(p, int) else f".{p}" for p in error.absolute_path
        )
        lines.append(f"    {location}: {error.message}")
    return "\n".join(lines)


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    failures = 0

    valid_examples = sorted(p for p in EXAMPLES_DIR.glob("*.json"))
    invalid_examples = sorted(INVALID_DIR.glob("*.json"))
    if not valid_examples or not invalid_examples:
        print("error: expected manifests in both examples/ and examples/invalid/")
        return 1

    for path in valid_examples:
        instance = json.loads(path.read_text())
        if validator.is_valid(instance):
            print(f"PASS  {path.relative_to(ROOT)}")
        else:
            failures += 1
            print(f"FAIL  {path.relative_to(ROOT)} should validate but did not:")
            print(best_error(validator, instance))

    for path in invalid_examples:
        instance = json.loads(path.read_text())
        if validator.is_valid(instance):
            failures += 1
            print(f"FAIL  {path.relative_to(ROOT)} should be rejected but validated")
        else:
            print(f"PASS  {path.relative_to(ROOT)} rejected as expected:")
            print(best_error(validator, instance))

    if failures:
        print(f"\n{failures} failure(s)")
        return 1
    print("\nAll examples behaved as expected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
