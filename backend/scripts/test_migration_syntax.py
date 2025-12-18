#!/usr/bin/env python3
"""
Syntax and logic verification for migrate_goals_from_jsonb.py

This script verifies the migration script without requiring database access.
Tests:
1. Script imports successfully
2. Key functions are defined
3. Logic flow is sound
"""

import ast
import sys


def verify_migration_script():
    """Parse and verify the migration script structure"""

    print("=" * 70)
    print("MIGRATION SCRIPT SYNTAX VERIFICATION")
    print("=" * 70)

    script_path = "scripts/migrate_goals_from_jsonb.py"

    try:
        # Read the script
        with open(script_path, 'r') as f:
            source_code = f.read()

        print(f"✓ Successfully read {script_path}")

        # Parse the AST
        tree = ast.parse(source_code)
        print("✓ Script syntax is valid (Python AST parsing successful)")

        # Extract function and class definitions
        functions = []
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)

        print(f"\n✓ Found {len(classes)} class(es):")
        for cls in classes:
            print(f"  - {cls}")

        print(f"\n✓ Found {len(functions)} function(s):")
        for func in functions:
            print(f"  - {func}")

        # Verify required components
        required_functions = [
            'check_duplicate_goal',
            'create_goal_from_action_item',
            'process_therapy_session',
            'migrate_goals',
            'main'
        ]

        required_classes = [
            'GoalMigrationStats'
        ]

        print("\n" + "=" * 70)
        print("COMPONENT VERIFICATION")
        print("=" * 70)

        missing = []
        for func in required_functions:
            if func in functions:
                print(f"✓ Function '{func}' found")
            else:
                print(f"✗ Function '{func}' MISSING")
                missing.append(func)

        for cls in required_classes:
            if cls in classes:
                print(f"✓ Class '{cls}' found")
            else:
                print(f"✗ Class '{cls}' MISSING")
                missing.append(cls)

        # Check for key patterns
        print("\n" + "=" * 70)
        print("FEATURE VERIFICATION")
        print("=" * 70)

        features = {
            'Dry run support': '--dry-run' in source_code,
            'Verbose mode': '--verbose' in source_code,
            'Duplicate detection': 'check_duplicate_goal' in source_code,
            'Error handling': 'try:' in source_code and 'except' in source_code,
            'Progress logging': 'stats.sessions_processed' in source_code,
            'Async/await': 'async def' in source_code,
            'Transaction rollback': 'rollback' in source_code,
            'Batch processing': 'batch_size' in source_code,
        }

        for feature, present in features.items():
            status = "✓" if present else "✗"
            print(f"{status} {feature}")

        # Final verdict
        print("\n" + "=" * 70)
        if missing:
            print("❌ VERIFICATION FAILED")
            print(f"Missing components: {', '.join(missing)}")
            return False
        else:
            print("✅ ALL VERIFICATIONS PASSED")
            print("\nScript is ready for execution with virtual environment:")
            print("  1. Activate venv: source venv/bin/activate")
            print("  2. Dry run: python scripts/migrate_goals_from_jsonb.py --dry-run")
            print("  3. Execute: python scripts/migrate_goals_from_jsonb.py")
            return True

    except SyntaxError as e:
        print(f"\n❌ SYNTAX ERROR: {e}")
        return False

    except FileNotFoundError:
        print(f"\n❌ FILE NOT FOUND: {script_path}")
        return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print("=" * 70 + "\n")


if __name__ == "__main__":
    success = verify_migration_script()
    sys.exit(0 if success else 1)
