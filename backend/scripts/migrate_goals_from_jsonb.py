#!/usr/bin/env python3
"""
Data Migration Script: Backfill treatment_goals from JSONB action_items

This script migrates action_items stored in therapy_sessions.extracted_notes JSONB
to the structured treatment_goals table. It is idempotent and can be run multiple
times safely.

Usage:
    # Dry run (no database changes)
    python scripts/migrate_goals_from_jsonb.py --dry-run

    # Execute migration
    python scripts/migrate_goals_from_jsonb.py

    # Verbose output
    python scripts/migrate_goals_from_jsonb.py --verbose

Requirements:
    - Backend .env file must be configured with DATABASE_URL
    - treatment_goals table must exist (run alembic migrations first)
    - Script uses async SQLAlchemy sessions

Author: Database Engineer #1 (Wave 1, Feature 6 Goal Tracking)
Created: 2025-12-18
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.db_models import TherapySession
from app.models.goal_models import TreatmentGoal


class GoalMigrationStats:
    """Statistics tracker for migration progress"""

    def __init__(self):
        self.sessions_processed = 0
        self.sessions_with_action_items = 0
        self.goals_created = 0
        self.goals_skipped_duplicate = 0
        self.goals_skipped_invalid = 0
        self.errors: List[str] = []
        self.start_time = datetime.utcnow()

    def report(self) -> str:
        """Generate migration summary report"""
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()

        report = [
            "\n" + "=" * 70,
            "GOAL MIGRATION SUMMARY",
            "=" * 70,
            f"Execution Time: {elapsed:.2f} seconds",
            f"Sessions Processed: {self.sessions_processed}",
            f"Sessions with Action Items: {self.sessions_with_action_items}",
            f"Goals Created: {self.goals_created}",
            f"Goals Skipped (Duplicate): {self.goals_skipped_duplicate}",
            f"Goals Skipped (Invalid): {self.goals_skipped_invalid}",
            f"Errors Encountered: {len(self.errors)}",
        ]

        if self.errors:
            report.append("\nERRORS:")
            for error in self.errors[:10]:  # Show first 10 errors
                report.append(f"  - {error}")
            if len(self.errors) > 10:
                report.append(f"  ... and {len(self.errors) - 10} more errors")

        report.append("=" * 70 + "\n")
        return "\n".join(report)


async def check_duplicate_goal(
    session: AsyncSession,
    patient_id: UUID,
    description: str,
    verbose: bool = False
) -> bool:
    """
    Check if a goal with the same description already exists for this patient.

    Args:
        session: Database session
        patient_id: Patient UUID
        description: Goal description to check
        verbose: Enable verbose logging

    Returns:
        True if duplicate exists, False otherwise
    """
    stmt = select(TreatmentGoal).where(
        and_(
            TreatmentGoal.patient_id == patient_id,
            TreatmentGoal.description == description
        )
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing and verbose:
        print(f"    ⚠ Duplicate goal found for patient {patient_id}: '{description[:50]}...'")

    return existing is not None


async def create_goal_from_action_item(
    session: AsyncSession,
    action_item: Dict[str, Any],
    therapy_session: TherapySession,
    stats: GoalMigrationStats,
    dry_run: bool = False,
    verbose: bool = False
) -> Optional[TreatmentGoal]:
    """
    Create a TreatmentGoal record from an action_item dictionary.

    Args:
        session: Database session
        action_item: Action item dict with keys: task, category, details
        therapy_session: Source therapy session
        stats: Statistics tracker
        dry_run: If True, don't commit to database
        verbose: Enable verbose logging

    Returns:
        Created TreatmentGoal or None if skipped
    """
    # Validate required fields
    task = action_item.get('task', '').strip()
    if not task:
        stats.goals_skipped_invalid += 1
        if verbose:
            print(f"    ⚠ Skipping action_item with empty task")
        return None

    # Extract fields with safe defaults
    category = action_item.get('category', 'general')
    details = action_item.get('details', '')

    # Construct full description (task + details if present)
    description = task
    if details:
        description = f"{task} - {details}"

    # Check for duplicate
    is_duplicate = await check_duplicate_goal(
        session,
        therapy_session.patient_id,
        description,
        verbose
    )

    if is_duplicate:
        stats.goals_skipped_duplicate += 1
        return None

    # Create new TreatmentGoal
    goal = TreatmentGoal(
        patient_id=therapy_session.patient_id,
        therapist_id=therapy_session.therapist_id,
        session_id=therapy_session.id,
        description=description,
        category=category,
        status='assigned',
        created_at=therapy_session.session_date  # Use session date as creation date
    )

    if not dry_run:
        session.add(goal)
        stats.goals_created += 1

        if verbose:
            print(f"    ✓ Created goal: [{category}] {description[:60]}...")
    else:
        stats.goals_created += 1
        if verbose:
            print(f"    [DRY RUN] Would create goal: [{category}] {description[:60]}...")

    return goal


async def process_therapy_session(
    session: AsyncSession,
    therapy_session: TherapySession,
    stats: GoalMigrationStats,
    dry_run: bool = False,
    verbose: bool = False
) -> None:
    """
    Process a single therapy session and migrate its action_items to goals.

    Args:
        session: Database session
        therapy_session: TherapySession record to process
        stats: Statistics tracker
        dry_run: If True, don't commit to database
        verbose: Enable verbose logging
    """
    try:
        stats.sessions_processed += 1

        # Extract action_items from JSONB
        extracted_notes = therapy_session.extracted_notes or {}
        action_items = extracted_notes.get('action_items', [])

        if not action_items:
            if verbose:
                print(f"  Session {therapy_session.id} has no action_items")
            return

        stats.sessions_with_action_items += 1

        if verbose:
            print(f"\n  Processing Session {therapy_session.id}")
            print(f"  Date: {therapy_session.session_date}")
            print(f"  Patient ID: {therapy_session.patient_id}")
            print(f"  Action Items Found: {len(action_items)}")

        # Process each action_item
        for idx, action_item in enumerate(action_items, 1):
            if verbose:
                print(f"\n  Action Item {idx}/{len(action_items)}:")

            await create_goal_from_action_item(
                session=session,
                action_item=action_item,
                therapy_session=therapy_session,
                stats=stats,
                dry_run=dry_run,
                verbose=verbose
            )

        # Commit after each session (for progress tracking)
        if not dry_run:
            await session.commit()

    except Exception as e:
        error_msg = f"Error processing session {therapy_session.id}: {str(e)}"
        stats.errors.append(error_msg)
        print(f"\n❌ {error_msg}")

        if not dry_run:
            await session.rollback()


async def migrate_goals(
    dry_run: bool = False,
    verbose: bool = False,
    batch_size: int = 50
) -> GoalMigrationStats:
    """
    Main migration function: Backfill treatment_goals from action_items.

    Args:
        dry_run: If True, don't commit changes to database
        verbose: Enable verbose logging
        batch_size: Number of sessions to process per batch

    Returns:
        GoalMigrationStats object with migration results
    """
    stats = GoalMigrationStats()

    print("\n" + "=" * 70)
    print("STARTING GOAL MIGRATION FROM JSONB ACTION_ITEMS")
    print("=" * 70)

    if dry_run:
        print("🔍 DRY RUN MODE - No database changes will be made")

    print(f"Batch Size: {batch_size}")
    print(f"Verbose Mode: {verbose}")
    print()

    async with AsyncSessionLocal() as session:
        try:
            # Count total sessions with action_items
            count_stmt = select(func.count(TherapySession.id)).where(
                TherapySession.extracted_notes['action_items'].isnot(None)
            )
            result = await session.execute(count_stmt)
            total_sessions = result.scalar()

            print(f"Found {total_sessions} sessions with extracted_notes.action_items")
            print()

            if total_sessions == 0:
                print("✓ No sessions to process. Migration complete.")
                return stats

            # Query all therapy sessions with action_items (ordered by date)
            stmt = select(TherapySession).where(
                TherapySession.extracted_notes['action_items'].isnot(None)
            ).order_by(TherapySession.session_date.asc())

            result = await session.execute(stmt)
            therapy_sessions = result.scalars().all()

            # Process sessions in batches
            for i, therapy_session in enumerate(therapy_sessions, 1):
                if i % 10 == 0 or i == len(therapy_sessions):
                    print(f"\n⏳ Progress: {i}/{len(therapy_sessions)} sessions processed...")

                await process_therapy_session(
                    session=session,
                    therapy_session=therapy_session,
                    stats=stats,
                    dry_run=dry_run,
                    verbose=verbose
                )

            print("\n✅ Migration completed successfully!")

        except Exception as e:
            error_msg = f"Fatal error during migration: {str(e)}"
            stats.errors.append(error_msg)
            print(f"\n❌ {error_msg}")

            if not dry_run:
                await session.rollback()

            raise

    return stats


async def main():
    """CLI entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Migrate action_items from therapy_sessions.extracted_notes to treatment_goals table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview changes
  python scripts/migrate_goals_from_jsonb.py --dry-run --verbose

  # Execute migration
  python scripts/migrate_goals_from_jsonb.py

  # Execute with verbose output
  python scripts/migrate_goals_from_jsonb.py --verbose
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying database'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of sessions to process per batch (default: 50)'
    )

    args = parser.parse_args()

    # Run migration
    try:
        stats = await migrate_goals(
            dry_run=args.dry_run,
            verbose=args.verbose,
            batch_size=args.batch_size
        )

        # Print summary report
        print(stats.report())

        # Exit with error code if there were errors
        if stats.errors:
            sys.exit(1)

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠ Migration interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
