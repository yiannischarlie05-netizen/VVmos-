"""
Titan V13.0 — Skills & Knowledge Endpoint
/api/skills — Enumerate available skills, codebase knowledge, and agent capabilities
"""

import os
from fastapi import APIRouter

router = APIRouter(prefix="/api/skills", tags=["skills"])

# Example: Load skills/knowledge from README, DEEP-CODEBASE-ANALYSIS, and module docstrings

SKILL_FILES = [
    "README.md",
    "DEEP-CODEBASE-ANALYSIS.md",
    "GENESIS-PIPELINE-FIXES.md",
]

BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SEARCH_PATHS = [
    BASE_PATH,
    os.path.join(BASE_PATH, "vmos_titan"),
    os.path.join(BASE_PATH, "docs"),
    os.path.join(BASE_PATH, "playground"),
]

EXTENSIONS = [".md", ".txt", ".py"]


def collect_skill_files():
    paths = []
    for root in SEARCH_PATHS:
        if not os.path.exists(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # Skip heavy or irrelevant directories
            skip_dirs = {"__pycache__", "node_modules", ".git", "build", "dist"}
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for fn in filenames:
                if any(fn.lower().endswith(ext) for ext in EXTENSIONS):
                    paths.append(os.path.join(dirpath, fn))
    # Prioritize known root docs first
    unique_paths = []
    seen = set()
    for path in sorted(paths):
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)
    return unique_paths


def load_skills():
    skill_files = SKILL_FILES + collect_skill_files()
    skills = []
    for fpath in skill_files:
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        # for very large files, keep first 150 lines
        lines = content.splitlines()[:150]
        preview = "\n".join(lines)

        skills.append(
            {
                "file": os.path.relpath(fpath, BASE_PATH),
                "size_bytes": os.path.getsize(fpath),
                "snippet": preview,
            }
        )

    return skills


@router.get("/", tags=["skills"])
def get_skills():
    """Return a summary of available skills, codebase knowledge, and agent capabilities."""
    return {"skills": load_skills()}
