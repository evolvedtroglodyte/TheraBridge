"""
Quick test to verify mood analyzer uses correct model configuration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.mood_analyzer import MoodAnalyzer

def test_default_model():
    """Verify default model is gpt-4o-mini"""
    analyzer = MoodAnalyzer()
    assert analyzer.model == "gpt-4o-mini", f"Expected gpt-4o-mini, got {analyzer.model}"
    assert analyzer.temperature == 0.3, f"Expected 0.3, got {analyzer.temperature}"
    print("✓ Default model configuration: gpt-4o-mini @ temp=0.3")

def test_model_override():
    """Verify model override works"""
    analyzer = MoodAnalyzer(override_model="gpt-4o")
    assert analyzer.model == "gpt-4o", f"Expected gpt-4o, got {analyzer.model}"
    assert analyzer.temperature == 0.3, f"Expected 0.3, got {analyzer.temperature}"
    print("✓ Model override works: gpt-4o @ temp=0.3")

if __name__ == "__main__":
    test_default_model()
    test_model_override()
    print("\n✓ All mood analyzer configuration tests passed!")
