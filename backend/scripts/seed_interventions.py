#!/usr/bin/env python3
"""
Seed the interventions table with built-in therapy interventions.
This script loads interventions from the JSON library and populates the database.
Can be run standalone: python backend/scripts/seed_interventions.py
"""
import asyncio
import json
import sys
from pathlib import Path
from sqlalchemy import select

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models.treatment_models import Intervention


async def seed_interventions():
    """
    Load interventions from JSON library and insert into database.
    Checks for duplicates by name to avoid re-inserting existing interventions.
    """
    # Load interventions from JSON file
    json_path = Path(__file__).parent.parent / "app" / "data" / "interventions_library.json"

    if not json_path.exists():
        print(f"ERROR: Interventions library not found at {json_path}")
        return

    with open(json_path, "r") as f:
        interventions_data = json.load(f)

    print(f"Loaded {len(interventions_data)} interventions from library")
    print("-" * 60)

    # Connect to database
    async with AsyncSessionLocal() as session:
        # Get existing intervention names to avoid duplicates
        result = await session.execute(select(Intervention.name))
        existing_names = {row[0] for row in result.fetchall()}

        print(f"Found {len(existing_names)} existing interventions in database")
        print("-" * 60)

        # Track statistics
        added_count = 0
        skipped_count = 0
        by_modality = {}

        # Insert interventions
        for intervention_data in interventions_data:
            name = intervention_data["name"]
            modality = intervention_data.get("modality", "Unknown")

            # Track by modality
            if modality not in by_modality:
                by_modality[modality] = 0

            # Skip if already exists
            if name in existing_names:
                print(f"SKIP: '{name}' already exists")
                skipped_count += 1
                continue

            # Create intervention with is_system=True, created_by=None
            intervention = Intervention(
                name=name,
                description=intervention_data.get("description"),
                modality=modality,
                evidence_level=intervention_data.get("evidence_level"),
                is_system=True,  # System-defined intervention
                created_by=None  # No specific creator for system interventions
            )

            session.add(intervention)
            by_modality[modality] += 1
            added_count += 1
            print(f"ADD: '{name}' ({modality}, {intervention_data.get('evidence_level')})")

        # Commit changes
        if added_count > 0:
            await session.commit()
            print("-" * 60)
            print(f"Successfully committed {added_count} new interventions")
        else:
            print("-" * 60)
            print("No new interventions to add")

    # Print summary
    print("\n" + "=" * 60)
    print("SEEDING SUMMARY")
    print("=" * 60)
    print(f"Total interventions in library: {len(interventions_data)}")
    print(f"New interventions added:        {added_count}")
    print(f"Existing interventions skipped: {skipped_count}")
    print()
    print("Interventions by modality:")
    for modality in sorted(by_modality.keys()):
        count = by_modality[modality]
        print(f"  - {modality:20s}: {count} intervention{'s' if count != 1 else ''}")
    print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("INTERVENTIONS LIBRARY SEEDING SCRIPT")
    print("=" * 60)
    print()

    try:
        asyncio.run(seed_interventions())
        print("\nSeeding completed successfully!")
    except Exception as e:
        print(f"\nERROR: Seeding failed with exception:")
        print(f"{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
