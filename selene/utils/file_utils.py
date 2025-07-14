"""
File handling utilities for SELENE
"""

import os
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import time
import hashlib


def validate_file_exists(file_path: str) -> bool:
    """Check if file exists and is accessible
    
    Args:
        file_path: Path to file
        
    Returns:
        bool: True if file exists and is readable
    """
    try:
        path = Path(file_path)
        return path.exists() and path.is_file() and os.access(path, os.R_OK)
    except Exception:
        return False


def get_file_extension(file_path: str) -> str:
    """Get file extension in lowercase
    
    Args:
        file_path: Path to file
        
    Returns:
        str: File extension including the dot (e.g., '.pdf', '.png')
    """
    return Path(file_path).suffix.lower()


def get_file_size(file_path: str) -> int:
    """Get file size in bytes
    
    Args:
        file_path: Path to file
        
    Returns:
        int: File size in bytes, 0 if file doesn't exist
    """
    try:
        return Path(file_path).stat().st_size
    except Exception:
        return 0


def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get comprehensive file information
    
    Args:
        file_path: Path to file
        
    Returns:
        dict: File information including size, dates, etc.
    """
    info = {
        'path': file_path,
        'exists': False,
        'size_bytes': 0,
        'size_mb': 0.0,
        'extension': '',
        'filename': '',
        'basename': '',
        'created': None,
        'modified': None,
        'is_readable': False,
        'is_writable': False
    }
    
    try:
        path = Path(file_path)
        
        if path.exists():
            stat = path.stat()
            
            info.update({
                'exists': True,
                'size_bytes': stat.st_size,
                'size_mb': stat.st_size / (1024 * 1024),
                'extension': path.suffix.lower(),
                'filename': path.name,
                'basename': path.stem,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'is_readable': os.access(path, os.R_OK),
                'is_writable': os.access(path, os.W_OK)
            })
    
    except Exception as e:
        logging.getLogger(__name__).error(f"Error getting file info for {file_path}: {e}")
    
    return info


def create_temp_directory(prefix: str = "selene_") -> str:
    """Create a temporary directory
    
    Args:
        prefix: Prefix for directory name
        
    Returns:
        str: Path to created temporary directory
    """
    try:
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        logging.getLogger(__name__).info(f"Created temp directory: {temp_dir}")
        return temp_dir
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating temp directory: {e}")
        raise


def cleanup_temp_files(directory: str, max_age_hours: int = 24) -> int:
    """Clean up old temporary files
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum age of files to keep (hours)
        
    Returns:
        int: Number of files deleted
    """
    deleted_count = 0
    logger = logging.getLogger(__name__)
    
    try:
        if not os.path.exists(directory):
            return 0
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in Path(directory).iterdir():
            try:
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old temp file: {file_path}")
                        
            except Exception as e:
                logger.warning(f"Error deleting temp file {file_path}: {e}")
    
    except Exception as e:
        logger.error(f"Error cleaning temp directory {directory}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} temporary files")
    
    return deleted_count


def copy_to_workspace(source_path: str, workspace_dir: str, 
                     new_name: Optional[str] = None) -> str:
    """Copy file to workspace directory
    
    Args:
        source_path: Source file path
        workspace_dir: Destination workspace directory
        new_name: Optional new filename
        
    Returns:
        str: Path to copied file
    """
    logger = logging.getLogger(__name__)
    
    try:
        source = Path(source_path)
        workspace = Path(workspace_dir)
        
        # Create workspace directory if it doesn't exist
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Determine destination filename
        if new_name:
            dest_name = new_name
        else:
            # Add timestamp to avoid conflicts
            timestamp = int(time.time())
            dest_name = f"{source.stem}_{timestamp}{source.suffix}"
        
        dest_path = workspace / dest_name
        
        # Copy file
        shutil.copy2(source, dest_path)
        
        logger.info(f"Copied {source} to {dest_path}")
        return str(dest_path)
        
    except Exception as e:
        logger.error(f"Error copying file {source_path} to workspace: {e}")
        raise


def safe_filename(filename: str, max_length: int = 255) -> str:
    """Create a safe filename by removing/replacing invalid characters
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        str: Safe filename
    """
    # Characters to remove or replace
    invalid_chars = '<>:"/\\|?*'
    
    # Replace invalid characters with underscores
    safe_name = filename
    for char in invalid_chars:
        safe_name = safe_name.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')
    
    # Ensure not empty
    if not safe_name:
        safe_name = "unnamed_file"
    
    # Truncate if too long
    if len(safe_name) > max_length:
        name, ext = os.path.splitext(safe_name)
        max_name_length = max_length - len(ext)
        safe_name = name[:max_name_length] + ext
    
    return safe_name


def ensure_directory_exists(directory_path: str) -> bool:
    """Ensure directory exists, create if necessary
    
    Args:
        directory_path: Path to directory
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating directory {directory_path}: {e}")
        return False


def get_unique_filename(directory: str, base_name: str, extension: str = "") -> str:
    """Get a unique filename in the specified directory
    
    Args:
        directory: Target directory
        base_name: Base filename (without extension)
        extension: File extension (with or without leading dot)
        
    Returns:
        str: Unique filename
    """
    # Ensure extension starts with dot
    if extension and not extension.startswith('.'):
        extension = '.' + extension
    
    dir_path = Path(directory)
    counter = 1
    
    # Try base name first
    filename = f"{base_name}{extension}"
    file_path = dir_path / filename
    
    # If it exists, add counter
    while file_path.exists():
        filename = f"{base_name}_{counter}{extension}"
        file_path = dir_path / filename
        counter += 1
    
    return filename


def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
    """Calculate hash of file contents
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        str: Hex digest of file hash, None if error
    """
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error calculating hash for {file_path}: {e}")
        return None


def find_files_by_pattern(directory: str, pattern: str, recursive: bool = True) -> List[str]:
    """Find files matching a pattern
    
    Args:
        directory: Directory to search
        pattern: Filename pattern (supports wildcards)
        recursive: Whether to search subdirectories
        
    Returns:
        list: List of matching file paths
    """
    try:
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return []
        
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))
        
        # Filter to only files (not directories)
        return [str(f) for f in files if f.is_file()]
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error finding files in {directory}: {e}")
        return []


def backup_file(file_path: str, backup_dir: Optional[str] = None) -> Optional[str]:
    """Create a backup copy of a file
    
    Args:
        file_path: Path to file to backup
        backup_dir: Directory for backup (default: same directory as original)
        
    Returns:
        str: Path to backup file, None if error
    """
    logger = logging.getLogger(__name__)
    
    try:
        source = Path(file_path)
        
        if not source.exists():
            logger.warning(f"Cannot backup non-existent file: {file_path}")
            return None
        
        # Determine backup directory
        if backup_dir:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
        else:
            backup_path = source.parent
        
        # Create backup filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source.stem}_backup_{timestamp}{source.suffix}"
        backup_file = backup_path / backup_name
        
        # Copy file
        shutil.copy2(source, backup_file)
        
        logger.info(f"Created backup: {backup_file}")
        return str(backup_file)
        
    except Exception as e:
        logger.error(f"Error creating backup of {file_path}: {e}")
        return None


def is_file_locked(file_path: str) -> bool:
    """Check if file is locked by another process
    
    Args:
        file_path: Path to file
        
    Returns:
        bool: True if file appears to be locked
    """
    try:
        # Try to open file in exclusive mode
        with open(file_path, 'r+b') as f:
            pass
        return False
    except (PermissionError, IOError):
        return True
    except FileNotFoundError:
        return False


def get_directory_size(directory: str) -> int:
    """Calculate total size of directory and its contents
    
    Args:
        directory: Directory path
        
    Returns:
        int: Total size in bytes
    """
    total_size = 0
    
    try:
        for dir_path, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dir_path, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, FileNotFoundError):
                    # Skip files that can't be accessed
                    continue
    except Exception:
        pass
    
    return total_size


def cleanup_empty_directories(directory: str) -> int:
    """Remove empty directories recursively
    
    Args:
        directory: Root directory to clean
        
    Returns:
        int: Number of directories removed
    """
    removed_count = 0
    logger = logging.getLogger(__name__)
    
    try:
        for root, dirs, files in os.walk(directory, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):  # Directory is empty
                        os.rmdir(dir_path)
                        removed_count += 1
                        logger.debug(f"Removed empty directory: {dir_path}")
                except OSError:
                    # Directory not empty or permission denied
                    continue
    except Exception as e:
        logger.error(f"Error cleaning empty directories in {directory}: {e}")
    
    if removed_count > 0:
        logger.info(f"Removed {removed_count} empty directories")
    
    return removed_count


class WorkspaceManager:
    """Manage workspace directories and files for SELENE"""
    
    def __init__(self, base_workspace: str = "workspace"):
        """Initialize workspace manager
        
        Args:
            base_workspace: Base workspace directory
        """
        self.base_workspace = Path(base_workspace)
        self.logger = logging.getLogger(__name__)
        
        # Create workspace subdirectories
        self.directories = {
            'temp': self.base_workspace / 'temp',
            'uploads': self.base_workspace / 'uploads', 
            'exports': self.base_workspace / 'exports',
            'cache': self.base_workspace / 'cache',
            'logs': self.base_workspace / 'logs'
        }
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all workspace directories exist"""
        try:
            for name, path in self.directories.items():
                path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Ensured {name} directory: {path}")
        except Exception as e:
            self.logger.error(f"Error creating workspace directories: {e}")
            raise
    
    def get_path(self, category: str, filename: str = "") -> str:
        """Get path within workspace category
        
        Args:
            category: Directory category ('temp', 'uploads', etc.)
            filename: Optional filename to append
            
        Returns:
            str: Full path
        """
        if category not in self.directories:
            raise ValueError(f"Unknown workspace category: {category}")
        
        base_path = self.directories[category]
        
        if filename:
            return str(base_path / filename)
        else:
            return str(base_path)
    
    def store_upload(self, source_path: str, file_type: str) -> str:
        """Store an uploaded file in workspace
        
        Args:
            source_path: Source file path
            file_type: Type of file ('schematic', 'datasheet', etc.)
            
        Returns:
            str: Path to stored file
        """
        try:
            source = Path(source_path)
            
            # Create safe filename with timestamp
            timestamp = int(time.time())
            safe_name = safe_filename(f"{file_type}_{timestamp}_{source.name}")
            
            dest_path = self.directories['uploads'] / safe_name
            
            # Copy file
            shutil.copy2(source, dest_path)
            
            self.logger.info(f"Stored {file_type} upload: {dest_path}")
            return str(dest_path)
            
        except Exception as e:
            self.logger.error(f"Error storing upload {source_path}: {e}")
            raise
    
    def create_temp_file(self, suffix: str = "", prefix: str = "temp_") -> str:
        """Create a temporary file in workspace
        
        Args:
            suffix: File suffix/extension
            prefix: Filename prefix
            
        Returns:
            str: Path to temporary file
        """
        try:
            temp_file = tempfile.NamedTemporaryFile(
                dir=self.directories['temp'],
                suffix=suffix,
                prefix=prefix,
                delete=False
            )
            temp_file.close()
            
            self.logger.debug(f"Created temp file: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            self.logger.error(f"Error creating temp file: {e}")
            raise
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """Clean up old temporary files
        
        Args:
            max_age_hours: Maximum age of files to keep
            
        Returns:
            int: Number of files cleaned up
        """
        return cleanup_temp_files(str(self.directories['temp']), max_age_hours)
    
    def export_file(self, source_path: str, export_name: str) -> str:
        """Export a file to exports directory
        
        Args:
            source_path: Source file path
            export_name: Name for exported file
            
        Returns:
            str: Path to exported file
        """
        try:
            source = Path(source_path)
            safe_name = safe_filename(export_name)
            
            # Ensure unique filename
            unique_name = get_unique_filename(
                str(self.directories['exports']),
                Path(safe_name).stem,
                Path(safe_name).suffix
            )
            
            dest_path = self.directories['exports'] / unique_name
            
            if source.exists():
                shutil.copy2(source, dest_path)
            else:
                # Create new file with content
                dest_path.touch()
            
            self.logger.info(f"Exported file: {dest_path}")
            return str(dest_path)
            
        except Exception as e:
            self.logger.error(f"Error exporting file: {e}")
            raise
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """Get information about workspace usage
        
        Returns:
            dict: Workspace information
        """
        info = {
            'base_path': str(self.base_workspace),
            'directories': {},
            'total_size_bytes': 0,
            'file_counts': {}
        }
        
        try:
            for name, path in self.directories.items():
                if path.exists():
                    size = get_directory_size(str(path))
                    file_count = len(find_files_by_pattern(str(path), "*", recursive=True))
                    
                    info['directories'][name] = {
                        'path': str(path),
                        'size_bytes': size,
                        'size_mb': size / (1024 * 1024),
                        'file_count': file_count,
                        'exists': True
                    }
                    
                    info['total_size_bytes'] += size
                    info['file_counts'][name] = file_count
                else:
                    info['directories'][name] = {
                        'path': str(path),
                        'exists': False
                    }
            
            info['total_size_mb'] = info['total_size_bytes'] / (1024 * 1024)
            
        except Exception as e:
            self.logger.error(f"Error getting workspace info: {e}")
        
        return info
    
    def cleanup_workspace(self, keep_exports: bool = True) -> Dict[str, int]:
        """Clean up workspace files
        
        Args:
            keep_exports: Whether to preserve export files
            
        Returns:
            dict: Cleanup statistics
        """
        stats = {
            'temp_files_removed': 0,
            'uploads_removed': 0,
            'cache_files_removed': 0,
            'exports_removed': 0,
            'directories_removed': 0
        }
        
        try:
            # Clean temp files
            stats['temp_files_removed'] = self.cleanup_temp_files(0)  # Remove all temp files
            
            # Clean uploads (older than 7 days)
            stats['uploads_removed'] = cleanup_temp_files(
                str(self.directories['uploads']), 24 * 7
            )
            
            # Clean cache files
            stats['cache_files_removed'] = cleanup_temp_files(
                str(self.directories['cache']), 24 * 3
            )
            
            # Clean exports if requested
            if not keep_exports:
                stats['exports_removed'] = cleanup_temp_files(
                    str(self.directories['exports']), 0
                )
            
            # Remove empty directories
            stats['directories_removed'] = cleanup_empty_directories(str(self.base_workspace))
            
            self.logger.info(f"Workspace cleanup completed: {stats}")
            
        except Exception as e:
            self.logger.error(f"Error during workspace cleanup: {e}")
        
        return stats


if __name__ == "__main__":
    # Test file utilities
    import tempfile
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    # Test basic file operations
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test file content")
        test_file = f.name
    
    print("File Utilities Test:")
    print(f"File exists: {validate_file_exists(test_file)}")
    print(f"File extension: {get_file_extension(test_file)}")
    print(f"File size: {get_file_size(test_file)} bytes")
    
    # Test workspace manager
    workspace = WorkspaceManager("test_workspace")
    print(f"\nWorkspace info: {workspace.get_workspace_info()}")
    
    # Test file operations
    temp_file = workspace.create_temp_file(suffix='.tmp')
    print(f"Created temp file: {temp_file}")
    
    # Clean up test files
    os.unlink(test_file)
    os.unlink(temp_file)
    
    print("File utilities test completed!")