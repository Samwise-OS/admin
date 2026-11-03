"""Render and verify the source-derived governance documentation contract.

This is a declaration projection, not a live GitHub acceptance certificate.
"""

import argparse
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = pathlib.Path("docs/generated/declared-governance.md")
SOURCES = (
    "config/organization.json",
    "config/repositories.json",
    ".github/settings.yml",
    ".github/workflows/reconcile.yml",
)


def read_sources(root):
    return {name: (root / name).read_bytes() for name in SOURCES}


def value_text(value):
    """Stable, Markdown-safe representation of a declared JSON value."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False).replace("|", r"\|")


def render(root=ROOT):
    sources = read_sources(root)
    organization = json.loads(sources["config/organization.json"])
    inventory = json.loads(sources["config/repositories.json"])
    settings = json.loads(sources[".github/settings.yml"])
    if not all(isinstance(item, dict) for item in (organization, inventory, settings)):
        raise ValueError("declaration sources must contain JSON objects")
    if (organization.get("organization") != inventory.get("organization") or
            organization.get("organization_id") != inventory.get("organization_id")):
        raise ValueError("organization and inventory identities disagree")

    admin = organization["admin_repository"]
    repositories = inventory["repositories"]
    names = [admin] + [item["name"] for item in repositories]
    if len(names) != len(set(names)):
        raise ValueError("managed repository names are not unique")

    cron_matches = re.findall(
        r"""(?m)^\s*-\s*cron:\s*['"]?([^'"\n]+)""",
        sources[".github/workflows/reconcile.yml"].decode("utf-8"),
    )
    if len(cron_matches) != 1:
        raise ValueError("expected exactly one reconciliation cron declaration")

    q = chr(96)
    lines = [
        "# Declared Samwise-OS governance (generated)",
        "",
        "<!-- GENERATED: python3 scripts/docs_sync.py --write; do not edit by hand. -->",
        "",
        "This page projects version-controlled declarations, **not** observed GitHub",
        "enforcement or device-side acceptance. See [operational acceptance](../acceptance.md)",
        "for independently recorded live evidence.",
        "",
        "## Managed repository identities",
        "",
        "| Repository | Immutable ID | Purpose |",
        "| --- | --- | --- |",
    ]
    lines.append(
        f"| {q}{admin}{q} | {organization['admin_repository_id']} | "
        "Organization control plane |"
    )
    for item in sorted(repositories, key=lambda entry: entry["name"]):
        lines.append(
            f"| {q}{item['name']}{q} | {item['id']} | "
            f"{str(item.get('description', '')).replace('|', r'\|')} |"
        )
    lines.extend(["", f"**Declared managed repository count:** {len(names)}", ""])

    for section, title in (
        ("organization_settings", "Organization policy"),
        ("organization_actions", "GitHub Actions policy"),
        ("organization_workflow_permissions", "Workflow token policy"),
        ("provisioning", "Repository provisioning defaults"),
        ("safe_settings", "Repository settings reconciliation"),
    ):
        values = organization[section]
        if not isinstance(values, dict):
            raise ValueError(f"{section} must be a JSON object")
        lines.extend([f"## {title}", "", "| Field | Declared value |", "| --- | --- |"])
        for key in sorted(values):
            lines.append(f"| {q}{key}{q} | {q}{value_text(values[key])}{q} |")
        lines.append("")

    lines.extend([
        "## Shared repository defaults",
        "",
        "| Field | Declared value |",
        "| --- | --- |",
    ])
    shared = settings["repository"]
    if not isinstance(shared, dict):
        raise ValueError("shared repository settings must be a JSON object")
    for key in sorted(shared):
        lines.append(f"| {q}{key}{q} | {q}{value_text(shared[key])}{q} |")
    lines.extend([
        "",
        "## Reconciliation trigger",
        "",
        f"- Scheduled cron expression: {q}{cron_matches[0].strip()}{q}",
        f"- Scheduled activation declaration: {q}"
        f"{value_text(organization['safe_settings']['schedule_enabled'])}{q}",
        "",
        "## Source fingerprints",
        "",
        "Any change to an authoritative declaration source changes its SHA-256",
        "fingerprint, requiring this generated page to be updated in the same PR.",
        "",
        "| Canonical source | SHA-256 |",
        "| --- | --- |",
    ])
    for name in SOURCES:
        digest = hashlib.sha256(sources[name]).hexdigest()
        lines.append(f"| {q}{name}{q} | {q}{digest}{q} |")
    lines.extend(["", "Regenerate with: " + q + "python3 scripts/docs_sync.py --write" + q, ""])
    return "\n".join(lines)


def verify(root=ROOT):
    target = root / OUTPUT
    try:
        content = target.read_text(encoding="utf-8")
        readme = (root / "README.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return content == render(root) and "docs/generated/declared-governance.md" in readme


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            destination = ROOT / OUTPUT
            destination.parent.mkdir(parents=True, exist_ok=True)
            expected = render(ROOT)
            destination.write_text(expected, encoding="utf-8", newline="\n")
            print(f"Regenerated {OUTPUT}")
            return 0
        if verify(ROOT):
            print("Documentation declaration parity: PASS")
            return 0
        print(
            "Documentation declaration parity: FAIL; regenerate "
            "docs/generated/declared-governance.md and verify README link",
            file=sys.stderr,
        )
        return 1
    except (OSError, UnicodeError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"Documentation parity: FAIL ({type(error).__name__}: {error})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
