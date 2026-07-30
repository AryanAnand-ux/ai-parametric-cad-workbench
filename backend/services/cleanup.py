import os
import time
import logging
from pathlib import Path
from config import TEMP_DIR, MODELS_DIR

logger = logging.getLogger("cad_workbench.cleanup")

class ArtifactCleanupManager:
    """
    Manages temporary file lifecycle, cleaning up execution scripts and stale mesh artifacts.
    """
    
    @staticmethod
    def cleanup_old_artifacts(max_age_seconds: int = 86400) -> int:
        """
        Deletes temporary files in TEMP_DIR and MODELS_DIR older than max_age_seconds (default 24 hours).
        Returns count of removed files.
        """
        now = time.time()
        removed_count = 0
        
        target_dirs = [TEMP_DIR, MODELS_DIR]
        
        for directory in target_dirs:
            if not directory.exists():
                continue
                
            for file_path in directory.glob("*"):
                if file_path.is_file():
                    # Calculate file age
                    file_age = now - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            file_path.unlink()
                            removed_count += 1
                            logger.info(f"Cleaned up stale artifact: {file_path.name}")
                        except Exception as e:
                            logger.warning(f"Failed to delete {file_path.name}: {e}")
                            
        return removed_count

    @staticmethod
    def remove_file_safely(file_path: Path):
        """Safely removes a single file if it exists."""
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove temp file {file_path}: {e}")
