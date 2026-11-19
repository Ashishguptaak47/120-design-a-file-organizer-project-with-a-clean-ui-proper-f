from __future__ import annotations
import os
import shutil
import json
import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Dict, Any
from core.classifier import Classifier

@dataclass
class PlanItem:
    src: Path
    dest: Path
    category: str
    size: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "src": str(self.src.resolve()),
            "dest": str(self.dest.resolve()),
            "category": self.category,
            "size": self.size
        }

class FileOrganizer:
    def __init__(self, classifier: Optional[Classifier] = None):
        self.classifier = classifier or Classifier()

    def build_plan(
        self,
        source_dir: Path,
        target_dir: Optional[Path] = None,
        mode: str = "category",
        recursive: bool = False
    ) -> List[PlanItem]:
        source_dir = Path(source_dir).resolve()
        target_root = Path(target_dir).resolve() if target_dir else source_dir
        plan: List[PlanItem] = []

        if not source_dir.is_dir():
            raise ValueError(f"Source directory does not exist: {source_dir}")

        iterator = source_dir.rglob("*") if recursive else source_dir.iterdir()
        for item in iterator:
            if not item.is_file():
                continue
            # Skip files located directly inside target directory sub-folders
            if target_root != source_dir and target_root in item.parents:
                continue

            category = self._determine_category(item, mode)
            dest_folder = target_root / category
            dest_file = dest_folder / item.name
            plan.append(PlanItem(
                src=item,
                dest=dest_file,
                category=category,
                size=item.stat().st_size
            ))
        return plan

    def _determine_category(self, path: Path, mode: str) -> str:
        if mode == "category":
            return self.classifier.classify_extension(path)
        elif mode == "date":
            mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
            return mtime.strftime("%Y/%B")
        elif mode == "extension":
            ext = path.suffix.lower().lstrip(".")
            return ext.upper() if ext else "NO_EXT"
        return "Others"

    def execute_plan(
        self,
        plan: List[PlanItem],
        copy_mode: bool = False,
        conflict_strategy: str = "rename",
        log_dir: Optional[Path] = None,
        progress_cb: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[int, Path]:
        log_dir = Path(log_dir) if log_dir else Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_path = log_dir / f"transaction_{timestamp}.json"

        history: List[Dict[str, Any]] = []
        total = len(plan)
        processed = 0

        for idx, item in enumerate(plan, start=1):
            if not item.src.exists():
                continue

            target_dest = self._resolve_conflict(item.dest, conflict_strategy)
            if target_dest is None:
                # Strategy was 'skip'
                continue

            target_dest.parent.mkdir(parents=True, exist_ok=True)

            if copy_mode:
                shutil.copy2(item.src, target_dest)
            else:
                shutil.move(item.src, target_dest)

            history.append({
                "source": str(item.src.resolve()),
                "destination": str(target_dest.resolve()),
                "action": "copy" if copy_mode else "move",
                "timestamp": datetime.datetime.now().isoformat()
            })
            processed += 1
            if progress_cb:
                progress_cb(idx, total, item.src.name)

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"created_at": timestamp, "copy_mode": copy_mode, "operations": history}, f, indent=2)

        return processed, manifest_path

    def rollback(self, manifest_file: Path) -> int:
        manifest_file = Path(manifest_file)
        if not manifest_file.exists():
            raise FileNotFoundError(f"Manifest file not found: {manifest_file}")

        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        restored = 0
        operations = data.get("operations", [])
        # Reverse chronological rollback
        for op in reversed(operations):
            src = Path(op["source"])
            dest = Path(op["destination"])
            action = op.get("action", "move")

            if action == "move":
                if dest.exists():
                    src.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(dest, src)
                    restored += 1
            elif action == "copy":
                if dest.exists():
                    dest.unlink()
                    restored += 1
        return restored

    def _resolve_conflict(self, dest: Path, strategy: str) -> Optional[Path]:
        if not dest.exists():
            return dest
        if strategy == "overwrite":
            return dest
        elif strategy == "skip":
            return None
        elif strategy == "rename":
            parent = dest.parent
            stem = dest.stem
            suffix = dest.suffix
            counter = 1
            while True:
                new_path = parent / f"{stem} ({counter}){suffix}"
                if not new_path.exists():
                    return new_path
                counter += 1
        return dest
