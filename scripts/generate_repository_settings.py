"""Generate the bounded Safe-Settings scope and per-repository rulesets."""

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_safe_settings import expected_ruleset, managed_repositories


def render(value):
    return (json.dumps(value, indent=2) + "\n").encode("utf-8")


def generate(root=ROOT, check=False):
    root = pathlib.Path(root).resolve(strict=True)
    admin, managed = managed_repositories(root)
    github = root / ".github"
    repos = github / "repos"
    deployment = github / "deployment-settings.yml"
    if github.is_symlink() or (github.exists() and not github.is_dir()):
        raise ValueError(".github must be a real directory")
    if deployment.is_symlink():
        raise ValueError("deployment-settings.yml must not be a symlink")
    if repos.is_symlink() or (repos.exists() and not repos.is_dir()):
        raise ValueError(".github/repos must be a real directory")
    existing = set()
    if repos.exists():
        for entry in repos.iterdir():
            if entry.is_symlink() or not entry.is_file():
                raise ValueError(f"Unsafe generated repository configuration path: {entry.name}")
            if entry.name not in {f"{name}.yml" for name in managed}:
                raise ValueError(f"{entry.name} is outside the generated repository set")
            existing.add(entry.name)

    outputs = {
        deployment: render({"restrictedRepos": {"include": managed}}),
    }
    for name in managed:
        context = "governance" if name == admin else "baseline / standards"
        outputs[repos / f"{name}.yml"] = render({"rulesets": [expected_ruleset(context)]})

    if check:
        drift = [str(path.relative_to(root)) for path, content in outputs.items()
                 if not path.is_file() or path.read_bytes() != content]
        if drift:
            raise ValueError(f"Generated repository settings drift: {', '.join(drift)}")
        return

    repos.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated settings have drifted")
    arguments = parser.parse_args()
    try:
        generate(check=arguments.check)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print("Generated repository settings are up to date." if arguments.check else
          "Generated repository settings from the organization manifests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
