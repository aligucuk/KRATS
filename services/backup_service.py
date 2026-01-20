# services/backup_service.py

import os
import shutil
import zipfile
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Callable, Optional

from config import settings
from utils.logger import get_logger
from database.db_manager import DatabaseManager

logger = get_logger(__name__)


class BackupService:
    """Database and file backup service"""
    
    def __init__(self, db: DatabaseManager):
        """Initialize backup service
        
        Args:
            db: Database manager instance
        """
        self.db = db
        self.backup_dir = Path(settings.BASE_DIR) / settings.BACKUP_DIRECTORY
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Backup service initialized - Directory: {self.backup_dir}")
    
    def create_backup(
        self, include_files: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Tuple[bool, str]:
        """Create full backup
        
        Args:
            include_files: Include uploaded files in backup
            progress_callback: Optional progress callback (0.0 to 1.0)
            
        Returns:
            Tuple of (success, message/filepath)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"KRATS_Backup_{timestamp}.zip"
            backup_path = self.backup_dir / backup_filename
            
            logger.info(f"Creating backup: {backup_filename}")
            
            # Report progress
            if progress_callback:
                progress_callback(0.1)
            
            # Create temporary backup of database
            temp_db_path = self.backup_dir / f"temp_db_{timestamp}.db"
            
            try:
                # Use SQLite backup API for safe backup
                source_db = settings.get_database_path()
                
                if source_db and source_db.exists():
                    src_conn = sqlite3.connect(str(source_db))
                    dst_conn = sqlite3.connect(str(temp_db_path))
                    
                    with dst_conn:
                        src_conn.backup(dst_conn)
                    
                    dst_conn.close()
                    src_conn.close()
                    
                    logger.info("Database backup completed")
                else:
                    return False, "Database file not found"
                
                if progress_callback:
                    progress_callback(0.5)
                
                # Create ZIP archive
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    # Add database
                    zf.write(temp_db_path, "krats.db")
                    
                    # Add uploaded files if requested
                    if include_files:
                        upload_dir = settings.BASE_DIR / settings.UPLOAD_DIRECTORY
                        if upload_dir.exists():
                            for root, dirs, files in os.walk(upload_dir):
                                for file in files:
                                    file_path = Path(root) / file
                                    arcname = file_path.relative_to(settings.BASE_DIR)
                                    zf.write(file_path, arcname)
                    
                    # Add configuration (without secrets)
                    # env_example = settings.BASE_DIR / ".env.example"
                    # if env_example.exists():
                    #     zf.write(env_example, ".env.example")
                
                if progress_callback:
                    progress_callback(0.9)
                
                # Cleanup temporary database
                if temp_db_path.exists():
                    temp_db_path.unlink()
                
                # Cleanup old backups
                self._cleanup_old_backups()
                
                if progress_callback:
                    progress_callback(1.0)
                
                logger.info(f"Backup created successfully: {backup_path}")
                return True, str(backup_path)
                
            finally:
                # Ensure temp file is cleaned up
                if temp_db_path.exists():
                    try:
                        temp_db_path.unlink()
                    except:
                        pass
        
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False, f"Yedekleme hatası: {str(e)}"
    
    def restore_backup(self, backup_path: str) -> Tuple[bool, str]:
        """Restore from backup
        
        Args:
            backup_path: Path to backup ZIP file
            
        Returns:
            Tuple of (success, message)
        """
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return False, "Yedek dosyası bulunamadı"
            
            logger.info(f"Restoring backup: {backup_file}")
            
            # Create restore directory
            restore_dir = self.backup_dir / "restore_temp"
            restore_dir.mkdir(exist_ok=True)
            
            try:
                # Extract backup
                with zipfile.ZipFile(backup_file, 'r') as zf:
                    zf.extractall(restore_dir)
                
                # Restore database
                restored_db = restore_dir / "krats.db"
                target_db = settings.get_database_path()
                
                if restored_db.exists() and target_db:
                    # Backup current database first
                    current_backup = target_db.with_suffix('.db.backup')
                    if target_db.exists():
                        shutil.copy2(target_db, current_backup)
                    
                    # Replace with restored database
                    shutil.copy2(restored_db, target_db)
                    
                    logger.info("Database restored successfully")
                
                # Restore files
                upload_dir = restore_dir / settings.UPLOAD_DIRECTORY
                if upload_dir.exists():
                    target_upload = settings.BASE_DIR / settings.UPLOAD_DIRECTORY
                    target_upload.mkdir(exist_ok=True)
                    
                    for item in upload_dir.iterdir():
                        target_item = target_upload / item.name
                        if item.is_file():
                            shutil.copy2(item, target_item)
                        elif item.is_dir():
                            shutil.copytree(item, target_item, dirs_exist_ok=True)
                
                logger.info("Backup restored successfully")
                return True, "Yedek başarıyla geri yüklendi"
                
            finally:
                # Cleanup restore directory
                if restore_dir.exists():
                    shutil.rmtree(restore_dir, ignore_errors=True)
        
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False, f"Geri yükleme hatası: {str(e)}"
    
    def _cleanup_old_backups(self):
        """Remove backups older than retention period"""
        try:
            retention_days = settings.BACKUP_RETENTION_DAYS
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            deleted_count = 0
            
            for backup_file in self.backup_dir.glob("KRATS_Backup_*.zip"):
                # Get file modification time
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old backup: {backup_file.name}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backups")
        
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    def list_backups(self) -> list:
        """List available backups
        
        Returns:
            List of backup info dictionaries
        """
        backups = []
        
        try:
            for backup_file in sorted(
                self.backup_dir.glob("KRATS_Backup_*.zip"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            ):
                stat = backup_file.stat()
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_mtime),
                    'created_str': datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
                })
        
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def get_backup_size(self) -> int:
        """Get total size of backups in bytes"""
        total_size = 0
        
        try:
            for backup_file in self.backup_dir.glob("KRATS_Backup_*.zip"):
                total_size += backup_file.stat().st_size
        except Exception as e:
            logger.error(f"Failed to calculate backup size: {e}")
        
        return total_size