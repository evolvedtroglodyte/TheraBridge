"""
Enhanced storage utilities for scraped data.

Provides additional storage capabilities beyond basic Pydantic export methods:
- Automatic timestamping
- Data versioning and comparison
- Storage cleanup and management
- Summary statistics
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging
from ..models.schemas import UphealData
from ..config import settings

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Manages storage and retrieval of scraped data.
    Provides utilities beyond basic export (versioning, comparison, cleanup).
    """

    def __init__(self, base_dir: Path = None):
        """
        Initialize storage manager.

        Args:
            base_dir: Base directory for storage (defaults to settings.processed_data_dir)
        """
        self.base_dir = base_dir or settings.processed_data_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"StorageManager initialized: {self.base_dir}")

    def save_with_timestamp(self, data: UphealData, prefix: str = "upheal") -> dict:
        """
        Save data with automatic timestamped filename.

        Args:
            data: UphealData to save
            prefix: Filename prefix (default: "upheal")

        Returns:
            Dict with paths: {'json': path, 'csv': path, 'timestamp': timestamp}
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Generate filenames
        json_path = self.base_dir / f"{prefix}_{timestamp}.json"
        csv_path = self.base_dir / f"{prefix}_{timestamp}.csv"

        # Export using model methods
        data.export_json(str(json_path))
        data.export_csv(str(csv_path))

        logger.info(f"Saved data: JSON={json_path.name}, CSV={csv_path.name}")

        return {
            'json': str(json_path),
            'csv': str(csv_path),
            'timestamp': timestamp
        }

    def list_saved_data(self, pattern: str = "upheal_*.json") -> List[Path]:
        """
        List all saved data files matching pattern.

        Args:
            pattern: Glob pattern for files (default: upheal_*.json)

        Returns:
            List of Path objects sorted by modification time (newest first)
        """
        files = sorted(
            self.base_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        logger.info(f"Found {len(files)} saved data files")
        return files

    def load_latest(self, pattern: str = "upheal_*.json") -> Optional[UphealData]:
        """
        Load the most recently saved data file.

        Args:
            pattern: Glob pattern for files

        Returns:
            UphealData object or None if no files found
        """
        files = self.list_saved_data(pattern)

        if not files:
            logger.warning(f"No files found matching pattern: {pattern}")
            return None

        latest_file = files[0]
        logger.info(f"Loading latest data: {latest_file.name}")

        with open(latest_file, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)

        return UphealData(**data_dict)

    def compare_data(self, old_data: UphealData, new_data: UphealData) -> dict:
        """
        Compare two scraping runs to identify changes.

        Args:
            old_data: Previous scrape
            new_data: Current scrape

        Returns:
            Dict with comparison results
        """
        comparison = {
            'features': {
                'old_count': len(old_data.features),
                'new_count': len(new_data.features),
                'added': [],
                'removed': []
            },
            'pricing': {
                'old_count': len(old_data.pricing_tiers),
                'new_count': len(new_data.pricing_tiers),
                'added': [],
                'removed': [],
                'price_changes': []
            }
        }

        # Compare features by name
        old_feature_names = {f.name for f in old_data.features}
        new_feature_names = {f.name for f in new_data.features}

        comparison['features']['added'] = list(new_feature_names - old_feature_names)
        comparison['features']['removed'] = list(old_feature_names - new_feature_names)

        # Compare pricing tiers
        old_pricing_names = {p.name for p in old_data.pricing_tiers}
        new_pricing_names = {p.name for p in new_data.pricing_tiers}

        comparison['pricing']['added'] = list(new_pricing_names - old_pricing_names)
        comparison['pricing']['removed'] = list(old_pricing_names - new_pricing_names)

        # Check for price changes
        old_pricing = {p.name: p.price for p in old_data.pricing_tiers}
        new_pricing = {p.name: p.price for p in new_data.pricing_tiers}

        for name in old_pricing_names & new_pricing_names:
            if old_pricing[name] != new_pricing[name]:
                comparison['pricing']['price_changes'].append({
                    'tier': name,
                    'old_price': float(old_pricing[name]) if old_pricing[name] else None,
                    'new_price': float(new_pricing[name]) if new_pricing[name] else None
                })

        logger.info(
            f"Comparison: Features +{len(comparison['features']['added'])}/-{len(comparison['features']['removed'])}, "
            f"Pricing +{len(comparison['pricing']['added'])}/-{len(comparison['pricing']['removed'])}, "
            f"Price changes: {len(comparison['pricing']['price_changes'])}"
        )

        return comparison

    def cleanup_old_files(self, keep_recent: int = 10, pattern: str = "upheal_*") -> int:
        """
        Delete old data files, keeping only the N most recent.

        Args:
            keep_recent: Number of recent files to keep (default: 10)
            pattern: Glob pattern for files

        Returns:
            Number of files deleted
        """
        files = self.list_saved_data(f"{pattern}.json")

        if len(files) <= keep_recent:
            logger.info(f"No cleanup needed: {len(files)} files ≤ {keep_recent} threshold")
            return 0

        # Delete oldest files
        files_to_delete = files[keep_recent:]
        deleted_count = 0

        for file_path in files_to_delete:
            try:
                # Delete JSON and corresponding CSV
                file_path.unlink()
                csv_path = file_path.with_suffix('.csv')
                if csv_path.exists():
                    csv_path.unlink()

                deleted_count += 1
                logger.debug(f"Deleted old file: {file_path.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {file_path.name}: {e}")

        logger.info(f"Cleanup complete: deleted {deleted_count} old files")
        return deleted_count

    def get_summary_report(self) -> dict:
        """
        Get summary statistics about stored data.

        Returns:
            Dict with storage statistics
        """
        files = self.list_saved_data()

        if not files:
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'oldest_file': None,
                'newest_file': None
            }

        total_size = sum(f.stat().st_size for f in files)

        return {
            'total_files': len(files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'oldest_file': files[-1].name if files else None,
            'newest_file': files[0].name if files else None,
            'storage_dir': str(self.base_dir)
        }


# Global storage manager instance
storage_manager = StorageManager()
