"""Paths for local example outputs, independent of the current directory."""
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "run_result"

def result_path(*parts: str) -> str:
    path = RESULTS.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)

def memory_config():
    from hello_agents.memory import MemoryConfig
    return MemoryConfig(storage_path=result_path("shared", "memory_data"))

from contextlib import contextmanager
import os

@contextmanager
def result_workdir(*parts: str):
    """Scope third-party tools that only support cwd-relative output."""
    directory = Path(result_path(*parts))
    directory.mkdir(parents=True, exist_ok=True)
    previous = Path.cwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(previous)
