"""
Technique Library Loader and Validator

Provides access to the comprehensive clinical technique reference library
and utilities for matching/validating extracted techniques.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
from dataclasses import dataclass


@dataclass
class Technique:
    """Represents a clinical technique with metadata"""
    name: str
    modality: str
    full_modality_name: str
    definition: str
    aliases: List[str]

    @property
    def formatted_name(self) -> str:
        """Returns technique in standard format: 'MODALITY - TECHNIQUE'"""
        return f"{self.modality} - {self.name}"


class TechniqueLibrary:
    """
    Loads and provides access to the clinical technique reference library.

    Supports:
    - Exact matching by technique name
    - Fuzzy matching using string similarity
    - Alias resolution
    - Technique lookup by modality
    """

    def __init__(self, library_path: Optional[Path] = None):
        """
        Initialize the technique library.

        Args:
            library_path: Path to technique_library.json. If None, uses default location.
        """
        if library_path is None:
            # Path is backend/config/technique_library.json (not app/config)
            library_path = Path(__file__).parent.parent.parent / "config" / "technique_library.json"

        self.library_path = library_path
        self.techniques: List[Technique] = []
        self.modalities: Dict[str, str] = {}  # short_name -> full_name
        self._load_library()

    def _load_library(self):
        """Load the technique library from JSON file"""
        with open(self.library_path, 'r') as f:
            data = json.load(f)

        # Extract modality metadata
        for short_name, modality_data in data["modalities"].items():
            self.modalities[short_name] = modality_data["full_name"]

            # Create Technique objects
            for tech_data in modality_data["techniques"]:
                technique = Technique(
                    name=tech_data["name"],
                    modality=short_name,
                    full_modality_name=modality_data["full_name"],
                    definition=tech_data["definition"],
                    aliases=tech_data.get("aliases", [])
                )
                self.techniques.append(technique)

    def get_all_techniques(self) -> List[Technique]:
        """Get all techniques in the library"""
        return self.techniques

    def get_techniques_by_modality(self, modality: str) -> List[Technique]:
        """Get all techniques for a specific modality"""
        return [t for t in self.techniques if t.modality == modality]

    def exact_match(self, technique_str: str) -> Optional[Technique]:
        """
        Find exact match for a technique name or alias.

        Args:
            technique_str: Technique name to match (case-insensitive)

        Returns:
            Technique object if exact match found, None otherwise
        """
        technique_lower = technique_str.lower().strip()

        for technique in self.techniques:
            # Check technique name
            if technique.name.lower() == technique_lower:
                return technique

            # Check formatted name (e.g., "CBT - Cognitive Restructuring")
            if technique.formatted_name.lower() == technique_lower:
                return technique

            # Check aliases
            for alias in technique.aliases:
                if alias.lower() == technique_lower:
                    return technique

        return None

    def fuzzy_match(
        self,
        technique_str: str,
        threshold: float = 0.8
    ) -> Optional[Tuple[Technique, float]]:
        """
        Find best fuzzy match for a technique using string similarity.

        Args:
            technique_str: Technique name to match
            threshold: Minimum similarity score (0.0 to 1.0)

        Returns:
            Tuple of (Technique, confidence_score) if match found, None otherwise
        """
        technique_lower = technique_str.lower().strip()
        best_match = None
        best_score = 0.0

        for technique in self.techniques:
            # Check technique name similarity
            score = SequenceMatcher(None, technique_lower, technique.name.lower()).ratio()
            if score > best_score:
                best_score = score
                best_match = technique

            # Check alias similarities
            for alias in technique.aliases:
                score = SequenceMatcher(None, technique_lower, alias.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = technique

        if best_score >= threshold:
            return (best_match, best_score)

        return None

    def validate_and_standardize(
        self,
        technique_str: str,
        fuzzy_threshold: float = 0.8
    ) -> Tuple[Optional[str], float, str]:
        """
        Validate a technique string and return standardized format.

        Strategy:
        1. Try exact match first
        2. If no exact match, try fuzzy match
        3. If no match, return None

        Args:
            technique_str: Raw technique string from AI
            fuzzy_threshold: Minimum similarity for fuzzy matching

        Returns:
            Tuple of (standardized_technique, confidence, match_type)
            - standardized_technique: "MODALITY - TECHNIQUE" or None
            - confidence: 1.0 for exact, 0.8-1.0 for fuzzy, 0.0 for no match
            - match_type: "exact", "fuzzy", or "none"
        """
        if not technique_str or technique_str.strip() == "":
            return (None, 0.0, "none")

        # Try exact match
        exact = self.exact_match(technique_str)
        if exact:
            return (exact.formatted_name, 1.0, "exact")

        # Try fuzzy match
        fuzzy = self.fuzzy_match(technique_str, threshold=fuzzy_threshold)
        if fuzzy:
            technique, score = fuzzy
            return (technique.formatted_name, score, "fuzzy")

        # No match
        return (None, 0.0, "none")

    def get_technique_definition(self, formatted_name: str) -> Optional[str]:
        """
        Get definition for a technique given its formatted name.

        Args:
            formatted_name: "MODALITY - TECHNIQUE" format

        Returns:
            Definition string or None if not found
        """
        for technique in self.techniques:
            if technique.formatted_name == formatted_name:
                return technique.definition
        return None

    def get_all_formatted_names(self) -> List[str]:
        """Get all technique names in standardized format"""
        return [t.formatted_name for t in self.techniques]


# Singleton instance
_library_instance = None

def get_technique_library() -> TechniqueLibrary:
    """Get singleton instance of TechniqueLibrary"""
    global _library_instance
    if _library_instance is None:
        _library_instance = TechniqueLibrary()
    return _library_instance
