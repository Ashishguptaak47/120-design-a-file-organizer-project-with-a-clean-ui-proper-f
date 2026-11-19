import os
import shutil
import tempfile
import unittest
from pathlib import Path
from core.classifier import Classifier
from core.hasher import find_duplicates, calculate_file_hash
from core.organizer import FileOrganizer

class TestFileOrganizer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.src_dir = Path(self.test_dir) / "src"
        self.src_dir.mkdir()
        self.organizer = FileOrganizer()

        # Create dummy test files
        (self.src_dir / "doc.pdf").write_text("test pdf content")
        (self.src_dir / "photo.png").write_text("test image content")
        (self.src_dir / "audio.mp3").write_text("test audio content")
        (self.src_dir / "script.py").write_text("print('hello')")
        (self.src_dir / "archive.zip").write_text("zip binary")
        (self.src_dir / "unknown.xyz123").write_text("unknown format")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_classifier(self):
        classifier = Classifier()
        self.assertEqual(classifier.classify_extension(Path("sample.pdf")), "Documents")
        self.assertEqual(classifier.classify_extension(Path("sample.jpg")), "Images")
        self.assertEqual(classifier.classify_extension(Path("sample.unknown")), "Others")

    def test_build_plan_categorization(self):
        plan = self.organizer.build_plan(self.src_dir, mode="category")
        cat_map = {item.src.name: item.category for item in plan}
        self.assertEqual(cat_map.get("doc.pdf"), "Documents")
        self.assertEqual(cat_map.get("photo.png"), "Images")
        self.assertEqual(cat_map.get("audio.mp3"), "Audio")
        self.assertEqual(cat_map.get("script.py"), "Code")
        self.assertEqual(cat_map.get("archive.zip"), "Archives")
        self.assertEqual(cat_map.get("unknown.xyz123"), "Others")

    def test_execution_and_rollback(self):
        plan = self.organizer.build_plan(self.src_dir, mode="category")
        log_dir = Path(self.test_dir) / "logs"
        count, manifest = self.organizer.execute_plan(plan, copy_mode=False, log_dir=log_dir)
        self.assertEqual(count, 6)
        self.assertTrue(manifest.exists())

        # Check files were moved to sub-folders
        doc_path = self.src_dir / "Documents" / "doc.pdf"
        self.assertTrue(doc_path.exists())
        self.assertFalse((self.src_dir / "doc.pdf").exists())

        # Perform rollback
        restored = self.organizer.rollback(manifest)
        self.assertEqual(restored, 6)
        self.assertTrue((self.src_dir / "doc.pdf").exists())
        self.assertFalse(doc_path.exists())

    def test_conflict_rename(self):
        target_dir = Path(self.test_dir) / "target"
        target_dir.mkdir()
        dest_doc = target_dir / "Documents" / "doc.pdf"
        dest_doc.parent.mkdir(parents=True, exist_ok=True)
        dest_doc.write_text("pre-existing file")

        plan = self.organizer.build_plan(self.src_dir, target_dir=target_dir, mode="category")
        self.organizer.execute_plan(plan, conflict_strategy="rename")

        # Original kept, new file renamed to 'doc (1).pdf'
        self.assertTrue(dest_doc.exists())
        renamed = target_dir / "Documents" / "doc (1).pdf"
        self.assertTrue(renamed.exists())

    def test_duplicate_detection(self):
        dup1 = self.src_dir / "original.txt"
        dup2 = self.src_dir / "copy.txt"
        dup1.write_text("Identical content for duplicate test")
        dup2.write_text("Identical content for duplicate test")

        duplicates = find_duplicates([dup1, dup2])
        self.assertEqual(len(duplicates), 1)
        paths = list(duplicates.values())[0]
        self.assertEqual(len(paths), 2)

if __name__ == "__main__":
    unittest.main()
