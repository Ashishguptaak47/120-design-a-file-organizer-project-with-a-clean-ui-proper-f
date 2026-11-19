from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Dict, List, Set

def calculate_file_hash(path: Path, chunk_size: int = 65536) -> str:
    """Computes SHA-256 for a given file incrementally."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()

def find_duplicates(file_paths: List[Path]) -> Dict[str, List[Path]]:
    """Finds duplicate files based on file size and SHA-256 hash."""
    size_map: Dict[int, List[Path]] = {}
    for p in file_paths:
        if p.is_file():
            size = p.stat().st_size
            size_map.setdefault(size, []).append(p)

    duplicates: Dict[str, List[Path]] = {}
    for size, paths in size_map.items():
        if len(paths) > 1 and size > 0:
            hash_map: Dict[str, List[Path]] = {}
            for path in paths:
                try:
                    file_hash = calculate_file_hash(path)
                    hash_map.setdefault(file_hash, []).append(path)
                except (OSError, PermissionError):
                    continue
            for h, group in hash_map.items():
                if len(group) > 1:
                    duplicates[h] = group
    return duplicates
