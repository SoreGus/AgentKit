from dataclasses import dataclass
from pathlib import Path
import os


DEFAULT_MAX_FILE_BYTES = 1_000_000
DEFAULT_MAX_RESULTS = 50
DEFAULT_IGNORED_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".DS_Store",
}


class WorkspaceError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Workspace:
    root: Path
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES

    @classmethod
    def open(cls, root: str | Path) -> "Workspace":
        resolved = Path(root).expanduser().resolve(strict=True)

        if not resolved.is_dir():
            raise WorkspaceError(f"Workspace is not a directory: {resolved}")

        return cls(root=resolved)

    def resolve(self, relative_path: str = ".") -> Path:
        candidate = (self.root / relative_path).resolve(strict=True)

        if not candidate.is_relative_to(self.root):
            raise WorkspaceError(
                f"Path is outside the workspace: {relative_path}"
            )

        return candidate

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def is_ignored(self, path: Path) -> bool:
        return any(part in DEFAULT_IGNORED_NAMES for part in path.parts)

    def read_text(self, relative_path: str) -> str:
        path = self.resolve(relative_path)

        if not path.is_file():
            raise WorkspaceError(f"Not a file: {relative_path}")

        if path.stat().st_size > self.max_file_bytes:
            raise WorkspaceError(
                f"File is larger than {self.max_file_bytes} bytes: {relative_path}"
            )

        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise WorkspaceError(
                f"File is not UTF-8 text: {relative_path}"
            ) from error

    def walk_files(self, relative_path: str = "."):
        start = self.resolve(relative_path)

        if start.is_file():
            yield start
            return

        if not start.is_dir():
            raise WorkspaceError(f"Not a directory: {relative_path}")

        for current_root, directories, files in os.walk(start, followlinks=False):
            current = Path(current_root)

            directories[:] = sorted(
                name
                for name in directories
                if name not in DEFAULT_IGNORED_NAMES
                and not (current / name).is_symlink()
            )

            for name in sorted(files):
                path = current / name

                if name in DEFAULT_IGNORED_NAMES or path.is_symlink():
                    continue

                resolved = path.resolve(strict=True)
                if resolved.is_relative_to(self.root):
                    yield resolved
