from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_CATEGORIES: Dict[str, List[str]] = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".heic"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", ".csv", ".md", ".epub", ".rtf"],
    "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"],
    "Video": [".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".cpp", ".c", ".h", ".rs", ".go", ".java", ".sh", ".yaml", ".yml"],
    "Executables": [".exe", ".msi", ".dmg", ".deb", ".rpm", ".apk", ".appimage"]
}

class Classifier:
    def __init__(self, custom_categories: Optional[Dict[str, List[str]]] = None):
        self.categories = custom_categories or DEFAULT_CATEGORIES
        self._ext_map: Dict[str, str] = {}
        for cat, exts in self.categories.items():
            for ext in exts:
                self._ext_map[ext.lower()] = cat

    def classify_extension(self, path: Path) -> str:
        ext = path.suffix.lower()
        if not ext:
            return "Others"
        return self._ext_map.get(ext, "Others")
