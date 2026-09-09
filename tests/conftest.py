# Vellum test suite — shared fixtures (design-spec.md section 14).
"""Shared pytest fixtures: the sample-project root (copied per test so tests
can mutate freely), a resolved-interpreter invocation helper for
scripts/vellum, and a hook-script runner under Git Bash."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "sample-project"
sys.path.insert(0, str(FIXTURE_DIR))
import seed as fixture_seed  # noqa: E402  (fixture project seeder)

HOOKS_SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"
ENGINE = PLUGIN_ROOT / "scripts" / "vellum"

IS_WINDOWS = os.name == "nt"


def _find_bash():
    """Git Bash (Windows) or /bin/bash elsewhere; None when unavailable."""
    bash = shutil.which("bash")
    if bash:
        return bash
    for cand in (r"C:\Program Files\Git\bin\bash.exe",
                 r"C:\Program Files\Git\usr\bin\bash.exe"):
        if os.path.exists(cand):
            return cand
    return None


@pytest.fixture(scope="session")
def plugin_root():
    return PLUGIN_ROOT


@pytest.fixture()
def project(tmp_path):
    """A fresh seeded fixture project (one instance of every deterministic
    error class, per spec 14). The seeder lives at
    tests/fixtures/sample-project/seed.py and is the shipped form of the
    fixture (a directory of generated files would duplicate the schemas)."""
    dst = tmp_path / "sample-project"
    dst.mkdir()
    fixture_seed.seed(str(dst))
    return dst


@pytest.fixture()
def engine(project):
    """Callable: engine(*args) -> CompletedProcess run with the current
    interpreter from inside the project root."""
    def run(*args, root=None):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env.pop("CLAUDE_PROJECT_DIR", None)
        return subprocess.run(
            [sys.executable, str(ENGINE), *args],
            cwd=str(root or project), capture_output=True, text=True,
            encoding="utf-8", env=env, timeout=120)
    return run


@pytest.fixture()
def hook(project):
    """Callable: hook("<name>.sh", payload_dict) -> CompletedProcess running
    the hook script under bash with the payload piped via stdin (never
    exported to the environment — the E2BIG lesson)."""
    bash = _find_bash()
    if bash is None:
        pytest.skip("bash not available for hook-contract tests")

    def run(name, payload=None, root=None, extra_env=None):
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = str(root or project)
        env["LC_ALL"] = "C"
        if extra_env:
            env.update(extra_env)
        stdin_data = json.dumps(payload) if payload is not None else ""
        return subprocess.run(
            [bash, str(HOOKS_SCRIPTS / name)],
            input=stdin_data, cwd=str(root or project), capture_output=True,
            text=True, encoding="utf-8", errors="replace", env=env,
            timeout=180)
    return run


@pytest.fixture()
def findings(engine):
    """Callable: findings("ledger", "check") -> list of finding dicts parsed
    from the engine's JSON-lines stdout."""
    def parse(*args):
        r = engine(*args)
        out = []
        for line in (r.stdout or "").split("\n"):
            line = line.strip()
            if line.startswith("{"):
                out.append(json.loads(line))
        return out
    return parse
