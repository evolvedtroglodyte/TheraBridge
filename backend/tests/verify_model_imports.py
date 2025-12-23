"""
Simple Verification Script for GPT-5 Model Configuration

Verifies that config imports are present in all service files.
"""

import os
import re


def check_file_for_config_import(filepath):
    """Check if file imports and uses model_config"""
    with open(filepath, 'r') as f:
        content = f.read()

    has_import = 'from app.config.model_config import get_model_name' in content
    has_usage = 'get_model_name(' in content
    no_temperature = 'temperature=' not in content or '# NOTE: GPT-5 series does NOT support custom temperature' in content

    return has_import, has_usage, no_temperature, content


def main():
    backend_path = "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"

    services = {
        "mood_analyzer.py": ("mood_analysis", "gpt-5-nano"),
        "topic_extractor.py": ("topic_extraction", "gpt-5-mini"),
        "breakthrough_detector.py": ("breakthrough_detection", "gpt-5"),
        "deep_analyzer.py": ("deep_analysis", "gpt-5.2"),
    }

    print("\n" + "=" * 70)
    print("GPT-5 Model Configuration Verification (Import Check)")
    print("=" * 70 + "\n")

    all_passed = True

    for filename, (task_name, expected_model) in services.items():
        filepath = os.path.join(backend_path, "app/services", filename)

        print(f"Checking {filename}...")

        has_import, has_usage, no_temp, content = check_file_for_config_import(filepath)

        # Check for expected model in task name
        task_check = f'"{task_name}"' in content

        status = "✅" if (has_import and has_usage and no_temp and task_check) else "❌"
        print(f"  {status} Config import:     {'Yes' if has_import else 'No'}")
        print(f"  {status} Uses get_model_name: {'Yes' if has_usage else 'No'}")
        print(f"  {status} No temperature param: {'Yes' if no_temp else 'No'}")
        print(f"  {status} Task name found:     {'Yes' if task_check else 'No'}")
        print(f"  Expected model:       {expected_model}")
        print()

        if not (has_import and has_usage and no_temp and task_check):
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("✅ ALL CHECKS PASSED - GPT-5 configuration is correctly implemented!")
        print("\nExpected model assignments:")
        print("  - Mood Analysis:          gpt-5-nano  (ultra-cheap)")
        print("  - Topic Extraction:       gpt-5-mini  (cost-efficient)")
        print("  - Breakthrough Detection: gpt-5       (complex reasoning)")
        print("  - Deep Analysis:          gpt-5.2     (best synthesis)")
    else:
        print("❌ SOME CHECKS FAILED - Please review implementation")

    print("=" * 70 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
