#!/usr/bin/env python3
"""
Validation script for therapy session transcripts.
Checks format consistency and audio generation compatibility.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any

class SessionValidator:
    def __init__(self, sessions_dir: str):
        self.sessions_dir = Path(sessions_dir)
        self.results = {}
        self.errors = []
        self.warnings = []

    def validate_all(self) -> Dict[str, Any]:
        """Validate all session files."""
        session_files = sorted(self.sessions_dir.glob("session_*.json"))

        print(f"\n{'='*80}")
        print(f"THERAPY SESSION TRANSCRIPT VALIDATION")
        print(f"{'='*80}\n")
        print(f"Sessions directory: {self.sessions_dir}")
        print(f"Found {len(session_files)} session files\n")

        for session_file in session_files:
            self.validate_session(session_file)

        return self.generate_report()

    def validate_session(self, filepath: Path):
        """Validate a single session file."""
        session_name = filepath.stem
        print(f"Validating {session_name}...")

        errors = []
        warnings = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
            self.results[session_name] = {"status": "FAIL", "errors": errors, "warnings": warnings}
            return
        except Exception as e:
            errors.append(f"File read error: {e}")
            self.results[session_name] = {"status": "FAIL", "errors": errors, "warnings": warnings}
            return

        # 1. Schema validation
        schema_errors = self.validate_schema(data, session_name)
        errors.extend(schema_errors)

        # 2. Speaker distribution check
        dist_errors, dist_warnings = self.validate_speaker_distribution(data)
        errors.extend(dist_errors)
        warnings.extend(dist_warnings)

        # 3. Timestamp validation
        time_errors = self.validate_timestamps(data)
        errors.extend(time_errors)

        # 4. Audio generation compatibility
        audio_errors, audio_warnings = self.validate_audio_compatibility(data)
        errors.extend(audio_errors)
        warnings.extend(audio_warnings)

        # Determine status
        status = "PASS" if len(errors) == 0 else "FAIL"

        self.results[session_name] = {
            "status": status,
            "errors": errors,
            "warnings": warnings
        }

        # Print immediate feedback
        if status == "PASS":
            print(f"  ✅ {session_name}: PASS ({len(warnings)} warnings)")
        else:
            print(f"  ❌ {session_name}: FAIL ({len(errors)} errors, {len(warnings)} warnings)")

    def validate_schema(self, data: Dict, session_name: str) -> List[str]:
        """Validate JSON schema."""
        errors = []

        # Required top-level fields
        required_fields = {
            'id': str,
            'status': str,
            'filename': str,
            'metadata': dict,
            'performance': dict,
            'speakers': list,
            'segments': list,
            'aligned_segments': list,
            'quality': dict
        }

        for field, expected_type in required_fields.items():
            if field not in data:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(data[field], expected_type):
                errors.append(f"Field '{field}' has wrong type: expected {expected_type.__name__}, got {type(data[field]).__name__}")

        # Validate id format
        if 'id' in data:
            expected_prefix = session_name.split('_')[0] + '_' + session_name.split('_')[1]
            if not data['id'].startswith(expected_prefix):
                errors.append(f"ID format incorrect: expected to start with '{expected_prefix}', got '{data['id']}'")

        # Validate status
        if 'status' in data and data['status'] != 'completed':
            errors.append(f"Status should be 'completed', got '{data['status']}'")

        # Validate metadata fields (using actual schema from generated files)
        if 'metadata' in data and isinstance(data['metadata'], dict):
            required_metadata = ['source_file', 'duration', 'language', 'pipeline_type']
            for field in required_metadata:
                if field not in data['metadata']:
                    errors.append(f"Missing metadata field: {field}")

        # Validate performance fields (using actual schema from generated files)
        if 'performance' in data and isinstance(data['performance'], dict):
            required_perf = ['total_processing_time_seconds', 'preprocessing_time_seconds',
                           'transcription_time_seconds', 'diarization_time_seconds']
            for field in required_perf:
                if field not in data['performance']:
                    errors.append(f"Missing performance field: {field}")

        # Validate speakers array
        if 'speakers' in data and isinstance(data['speakers'], list):
            if len(data['speakers']) != 2:
                errors.append(f"Should have exactly 2 speakers, found {len(data['speakers'])}")

            speaker_ids = {s.get('id') for s in data['speakers'] if isinstance(s, dict)}
            if speaker_ids != {'SPEAKER_00', 'SPEAKER_01'}:
                errors.append(f"Speaker IDs should be SPEAKER_00 and SPEAKER_01, found {speaker_ids}")

        return errors

    def validate_speaker_distribution(self, data: Dict) -> tuple[List[str], List[str]]:
        """Validate speaker time distribution."""
        errors = []
        warnings = []

        if 'speakers' not in data or 'metadata' not in data:
            return errors, warnings

        total_duration = data['metadata'].get('duration', 0)
        if total_duration == 0:
            errors.append("Total duration is 0")
            return errors, warnings

        # Calculate speaker percentages
        speaker_stats = {}
        for speaker in data['speakers']:
            if isinstance(speaker, dict):
                speaker_id = speaker.get('id')
                duration = speaker.get('total_duration', 0)
                percentage = (duration / total_duration) * 100
                speaker_stats[speaker_id] = {
                    'duration': duration,
                    'percentage': percentage
                }

        # Validate SPEAKER_00 (therapist: 35-45%)
        if 'SPEAKER_00' in speaker_stats:
            pct = speaker_stats['SPEAKER_00']['percentage']
            if pct < 35 or pct > 45:
                warnings.append(f"SPEAKER_00 percentage {pct:.1f}% outside expected range (35-45%)")

        # Validate SPEAKER_01 (client: 55-65%)
        if 'SPEAKER_01' in speaker_stats:
            pct = speaker_stats['SPEAKER_01']['percentage']
            if pct < 55 or pct > 65:
                warnings.append(f"SPEAKER_01 percentage {pct:.1f}% outside expected range (55-65%)")

        # Check for unknown segments
        if 'quality' in data and isinstance(data['quality'], dict):
            if 'speaker_distribution' in data['quality']:
                dist = data['quality']['speaker_distribution']
                unknown_count = dist.get('UNKNOWN', {}).get('count', 0)
                if unknown_count > 0:
                    errors.append(f"Found {unknown_count} unknown speaker segments")

        return errors, warnings

    def validate_timestamps(self, data: Dict) -> List[str]:
        """Validate timestamp integrity."""
        errors = []

        if 'segments' not in data or 'metadata' not in data:
            return errors

        segments = data['segments']
        total_duration = data['metadata'].get('duration', 0)

        if len(segments) == 0:
            errors.append("No segments found")
            return errors

        # Check first segment starts near 0
        first_start = segments[0].get('start', -1)
        if first_start < 0:
            errors.append("First segment has negative timestamp")
        elif first_start > 5.0:
            errors.append(f"First segment starts at {first_start}s (expected near 0)")

        # Check last segment ends at total duration
        last_end = segments[-1].get('end', -1)
        if abs(last_end - total_duration) > 1.0:
            errors.append(f"Last segment ends at {last_end}s, expected {total_duration}s")

        # Check chronological order and no overlaps
        prev_end = 0
        for i, segment in enumerate(segments):
            start = segment.get('start', -1)
            end = segment.get('end', -1)

            if start < 0 or end < 0:
                errors.append(f"Segment {i} has negative timestamp")
                continue

            if start >= end:
                errors.append(f"Segment {i} has start >= end ({start} >= {end})")

            if start < prev_end - 0.1:  # Allow small floating point errors
                errors.append(f"Segment {i} overlaps with previous segment")

            prev_end = end

        return errors

    def validate_audio_compatibility(self, data: Dict) -> tuple[List[str], List[str]]:
        """Validate audio generation compatibility."""
        errors = []
        warnings = []

        if 'segments' not in data:
            return errors, warnings

        segments = data['segments']

        for i, segment in enumerate(segments):
            # Check for text field
            if 'text' not in segment or not segment['text']:
                errors.append(f"Segment {i} missing or empty text field")
                continue

            # Check text encoding (try to encode as UTF-8)
            try:
                segment['text'].encode('utf-8')
            except UnicodeEncodeError:
                errors.append(f"Segment {i} has non-UTF-8 text")

            # Check segment duration
            if 'start' in segment and 'end' in segment:
                duration = segment['end'] - segment['start']
                if duration > 300:
                    warnings.append(f"Segment {i} is very long ({duration:.1f}s)")

            # Check speaker label consistency
            if 'speaker' in segment:
                speaker = segment['speaker']
                if speaker not in ['SPEAKER_00', 'SPEAKER_01']:
                    errors.append(f"Segment {i} has invalid speaker label: {speaker}")

        return errors, warnings

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        total_files = len(self.results)
        passing_files = sum(1 for r in self.results.values() if r['status'] == 'PASS')
        failing_files = total_files - passing_files

        print(f"\n{'='*80}")
        print(f"VALIDATION REPORT")
        print(f"{'='*80}\n")

        print(f"SUMMARY:")
        print(f"  Total files validated: {total_files}/12")
        print(f"  Files passing all checks: {passing_files}/{total_files}")
        print(f"  Files with errors: {failing_files}/{total_files}")

        if total_files < 12:
            print(f"  ⚠️  Missing files: {12 - total_files}")

        overall_status = "PASS" if failing_files == 0 and total_files == 12 else "FAIL"
        print(f"  Overall validation status: {overall_status}\n")

        print(f"DETAILED RESULTS:\n")
        for session_name, result in sorted(self.results.items()):
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {session_name}: {result['status']}")

            if result['errors']:
                print(f"   Errors:")
                for error in result['errors']:
                    print(f"     - {error}")

            if result['warnings']:
                print(f"   Warnings:")
                for warning in result['warnings']:
                    print(f"     - {warning}")

            print()

        # Final conclusion
        print(f"\n{'='*80}")
        if overall_status == "PASS":
            print("✅ ALL SESSIONS VALIDATED - READY FOR AUDIO GENERATION")
        else:
            sessions_needing_regen = [name for name, r in self.results.items() if r['status'] == 'FAIL']
            missing_count = 12 - total_files

            if missing_count > 0:
                print(f"❌ VALIDATION FAILED - {missing_count} SESSIONS MISSING")

            if sessions_needing_regen:
                print(f"❌ VALIDATION FAILED - {len(sessions_needing_regen)} SESSIONS NEED REGENERATION:")
                for session in sessions_needing_regen:
                    print(f"   - {session}")
        print(f"{'='*80}\n")

        return {
            'total_files': total_files,
            'passing_files': passing_files,
            'failing_files': failing_files,
            'missing_files': 12 - total_files,
            'overall_status': overall_status,
            'results': self.results
        }


if __name__ == '__main__':
    sessions_dir = "/Users/newdldewdl/Global Domination 2/peerbridge proj/mock-therapy-data/sessions"

    validator = SessionValidator(sessions_dir)
    report = validator.validate_all()

    # Exit with error code if validation failed
    exit(0 if report['overall_status'] == 'PASS' else 1)
