"""Shared helpers for Colab notebooks in this repo."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_URL = "https://github.com/spatialft/spatialft.github.io.git"
DEFAULT_REPO_DIR = Path("/content/spatialft.github.io")
NOTEBOOK_DEPS_SENTINEL_VERSION = "v3"


def bootstrap_colab_repo(
    repo_dir: str | Path = DEFAULT_REPO_DIR,
    repo_url: str = REPO_URL,
) -> Path:
    """Clone the repo into the Colab workspace if needed and enter notebooks/."""

    repo_path = Path(repo_dir)
    if not repo_path.exists():
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", repo_url, str(repo_path)], check=True)

    notebooks_dir = repo_path / "notebooks"
    os.chdir(notebooks_dir)

    repo_str = str(repo_path)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    return repo_path


def get_repo_paths(repo_root: str | Path = DEFAULT_REPO_DIR) -> dict[str, Path]:
    """Return the local repo paths used across notebooks."""

    repo_path = Path(repo_root)
    return {
        "repo_root": repo_path,
        "notebooks_dir": repo_path / "notebooks",
        "data_root": repo_path / "data",
        "results_root": repo_path / "results",
        "adapter_dir": repo_path / "results" / "finetuned" / "lora_adapter",
    }


def prepare_notebook(
    repo_root: str | Path = DEFAULT_REPO_DIR,
    *,
    pull_latest: bool = False,
) -> tuple[Path, dict[str, Path]]:
    """Bootstrap the repo and optionally pull latest main before returning paths."""

    repo_path = bootstrap_colab_repo(repo_root)
    if pull_latest:
        # Authenticate with GITHUB_TOKEN if available — Colab's git can reject
        # anonymous HTTPS pulls even on public repos.
        try:
            from google.colab import userdata
            token = userdata.get("GITHUB_TOKEN")
        except Exception:
            token = None

        if token:
            authed_url = f"https://x-access-token:{token}@github.com/spatialft/spatialft.github.io.git"
            subprocess.run(["git", "remote", "set-url", "origin", authed_url], check=True, cwd=repo_path)

        try:
            subprocess.run(["git", "pull", "origin", "main"], check=True, cwd=repo_path)
        except subprocess.CalledProcessError:
            print("Warning: git pull failed — continuing with local repo state.")

    return repo_path, get_repo_paths(repo_path)


def ensure_notebook_requirements(
    notebook_name: str,
    *,
    requirements_path: str | Path = "../requirements.txt",
) -> None:
    """Install notebook dependencies once per notebook/version and restart runtime."""

    sentinel = Path(f"/tmp/spatialft_{notebook_name}_deps_{NOTEBOOK_DEPS_SENTINEL_VERSION}")
    if sentinel.exists():
        print(f"Dependencies ready for {notebook_name}.")
        return

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "-U",
            "--upgrade-strategy",
            "only-if-needed",
            "-r",
            str(requirements_path),
        ],
        check=True,
    )
    sentinel.write_text("ok")
    # SIGKILL restarts the Colab runtime so bitsandbytes loads against the
    # correct CUDA binaries. Without this, quantized inference silently fails.
    print("Dependencies updated. Restarting runtime for clean CUDA bindings...")
    os.kill(os.getpid(), 9)


def require_local_adapter(repo_root: str | Path = DEFAULT_REPO_DIR) -> Path:
    """Return the local adapter directory or raise with a clear notebook dependency."""

    adapter_dir = get_repo_paths(repo_root)["adapter_dir"]
    if adapter_dir.exists():
        return adapter_dir
    raise FileNotFoundError(
        "LoRA adapter not found in the repo workspace. Run notebook 03 and publish the "
        "adapter, then pull latest main in notebook 04 so the adapter exists at "
        f"{adapter_dir}."
    )


def publish_artifacts(
    paths: Iterable[str | Path],
    message: str,
    repo_dir: str | Path = DEFAULT_REPO_DIR,
    dry_run: bool = False,
) -> bool:
    """Commit and push generated notebook artifacts from Colab.

    Pass ``dry_run=True`` to print what would be committed without pushing.
    Returns ``True`` when a commit was created and pushed, otherwise ``False``.
    """

    try:
        from google.colab import userdata
    except ImportError as exc:
        raise RuntimeError("GitHub publishing is only supported from Colab.") from exc

    token = userdata.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Missing Colab secret GITHUB_TOKEN.")

    repo_path = Path(repo_dir)
    rel_paths = [str(Path(p)) for p in paths]
    missing_paths = [path for path in rel_paths if not (repo_path / path).exists()]
    if missing_paths:
        raise FileNotFoundError(
            "Cannot publish notebook artifacts because these files do not exist yet: "
            + ", ".join(missing_paths)
        )

    repo_url = f"https://x-access-token:{token}@github.com/spatialft/spatialft.github.io.git"
    stash_name = "colab-artifacts-publish"

    subprocess.run(["git", "config", "user.email", "colab-bot@spatialft"], check=True, cwd=repo_path)
    subprocess.run(["git", "config", "user.name", "Colab Bot"], check=True, cwd=repo_path)
    subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=True, cwd=repo_path)

    stash_push = subprocess.run(
        ["git", "stash", "push", "--include-untracked", "-m", stash_name, "--", *rel_paths],
        check=True,
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    stashed = "No local changes to save" not in stash_push.stdout

    try:
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True, cwd=repo_path)
    except subprocess.CalledProcessError as exc:
        if stashed:
            subprocess.run(["git", "stash", "pop"], check=True, cwd=repo_path)
        raise RuntimeError(
            "git pull --rebase failed while preparing to publish notebook artifacts. "
            "Check for unrelated local changes or remote conflicts and retry."
        ) from exc

    if stashed:
        subprocess.run(["git", "stash", "pop"], check=True, cwd=repo_path)

    subprocess.run(["git", "add", "--", *rel_paths], check=True, cwd=repo_path)

    diff = subprocess.run(["git", "diff", "--cached", "--quiet", "--", *rel_paths], cwd=repo_path)
    if diff.returncode == 0:
        print("No artifact changes to commit.")
        return False
    if diff.returncode != 1:
        raise RuntimeError("git diff --cached failed while checking staged notebook artifacts.")

    if dry_run:
        print(f"[dry_run] Would commit to main: {', '.join(rel_paths)}")
        print(f"[dry_run] Message: {message}")
        return False

    subprocess.run(["git", "commit", "-m", message], check=True, cwd=repo_path)
    subprocess.run(["git", "push", "origin", "main"], check=True, cwd=repo_path)
    print(f"Pushed artifacts: {', '.join(rel_paths)}")
    return True
