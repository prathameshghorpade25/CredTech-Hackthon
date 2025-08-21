"""Log rotation and archiving functionality for long-term log management"""

import os
import glob
import gzip
import shutil
import logging
import datetime
from typing import List, Optional
from logging.handlers import RotatingFileHandler

class CompressedRotatingFileHandler(RotatingFileHandler):
    """Extended RotatingFileHandler that compresses rotated logs"""
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.compress_on_rollover = True
        
    def doRollover(self):
        """Override doRollover to compress rotated logs"""
        # Call the parent class's doRollover method first
        super().doRollover()
        
        # Compress the rotated file if compression is enabled
        if self.compress_on_rollover:
            # The rotated file will be named filename.1
            rotated_file = f"{self.baseFilename}.1"
            if os.path.exists(rotated_file):
                self._compress_file(rotated_file)
    
    def _compress_file(self, file_path: str) -> None:
        """Compress a file using gzip and remove the original"""
        try:
            compressed_file = f"{file_path}.gz"
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            # Remove the original file after successful compression
            os.remove(file_path)
        except Exception as e:
            # Log the error but don't raise it to avoid disrupting the application
            logging.error(f"Failed to compress log file {file_path}: {str(e)}")

def setup_log_rotation(log_file: str, max_bytes: int = 10485760, backup_count: int = 5) -> CompressedRotatingFileHandler:
    """Set up log rotation for a log file
    
    Args:
        log_file: Path to the log file
        max_bytes: Maximum size of the log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        
    Returns:
        CompressedRotatingFileHandler: The configured handler
    """
    handler = CompressedRotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,  # 10MB
        backupCount=backup_count,
        encoding='utf-8'
    )
    return handler

def archive_old_logs(log_dir: str, archive_dir: Optional[str] = None, days_threshold: int = 30) -> List[str]:
    """Archive log files older than the specified threshold
    
    Args:
        log_dir: Directory containing log files
        archive_dir: Directory to store archived logs (default: log_dir/archive)
        days_threshold: Age threshold in days (default: 30)
        
    Returns:
        List[str]: List of archived files
    """
    if archive_dir is None:
        archive_dir = os.path.join(log_dir, 'archive')
    
    # Create archive directory if it doesn't exist
    os.makedirs(archive_dir, exist_ok=True)
    
    # Calculate the cutoff date
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_threshold)
    
    # Find all log files in the directory (including compressed ones)
    log_files = glob.glob(os.path.join(log_dir, '*.log*'))
    
    archived_files = []
    for log_file in log_files:
        # Skip the archive directory itself
        if os.path.dirname(log_file) == archive_dir:
            continue
        
        # Get file modification time
        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(log_file))
        
        # If the file is older than the threshold, archive it
        if mod_time < cutoff_date:
            # Create archive filename with timestamp
            base_name = os.path.basename(log_file)
            archive_name = f"{mod_time.strftime('%Y%m%d')}_{base_name}"
            archive_path = os.path.join(archive_dir, archive_name)
            
            # Move the file to the archive directory
            try:
                shutil.move(log_file, archive_path)
                archived_files.append(archive_path)
            except Exception as e:
                logging.error(f"Failed to archive log file {log_file}: {str(e)}")
    
    return archived_files

def cleanup_archives(archive_dir: str, max_age_days: int = 365) -> int:
    """Remove archives older than the specified threshold
    
    Args:
        archive_dir: Directory containing archived logs
        max_age_days: Maximum age in days (default: 365)
        
    Returns:
        int: Number of files removed
    """
    # Calculate the cutoff date
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=max_age_days)
    
    # Find all files in the archive directory
    archive_files = glob.glob(os.path.join(archive_dir, '*'))
    
    removed_count = 0
    for archive_file in archive_files:
        # Get file modification time
        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(archive_file))
        
        # If the file is older than the threshold, remove it
        if mod_time < cutoff_date:
            try:
                os.remove(archive_file)
                removed_count += 1
            except Exception as e:
                logging.error(f"Failed to remove archive file {archive_file}: {str(e)}")
    
    return removed_count

def schedule_log_maintenance(log_dir: str, archive_dir: Optional[str] = None, 
                            archive_days: int = 30, cleanup_days: int = 365) -> None:
    """Schedule log maintenance tasks
    
    This function should be called periodically to archive old logs and clean up archives.
    
    Args:
        log_dir: Directory containing log files
        archive_dir: Directory to store archived logs (default: log_dir/archive)
        archive_days: Age threshold for archiving in days (default: 30)
        cleanup_days: Age threshold for cleanup in days (default: 365)
    """
    if archive_dir is None:
        archive_dir = os.path.join(log_dir, 'archive')
    
    # Archive old logs
    archived_files = archive_old_logs(log_dir, archive_dir, archive_days)
    if archived_files:
        logging.info(f"Archived {len(archived_files)} log files")
    
    # Clean up old archives
    removed_count = cleanup_archives(archive_dir, cleanup_days)
    if removed_count > 0:
        logging.info(f"Removed {removed_count} old archive files")