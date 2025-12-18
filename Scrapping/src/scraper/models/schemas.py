"""Pydantic data models for Upheal scraper.

GDPR-compliant data structures with validation and export capabilities.
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class Feature(BaseModel):
    """Individual product feature."""

    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = None  # e.g., "AI Features", "Clinical Tools"

    @field_validator('description')
    @classmethod
    def clean_description(cls, v: Optional[str]) -> Optional[str]:
        """Remove excessive whitespace."""
        if v:
            return ' '.join(v.split())
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "AI-Powered Session Notes",
                "description": "Automatically generate clinical notes from session transcripts",
                "category": "AI Features"
            }
        }
    }


class PricingTier(BaseModel):
    """Pricing plan information."""

    name: str = Field(..., min_length=1, max_length=200)
    price: Optional[Decimal] = Field(None, ge=0)
    billing_period: Optional[str] = None  # "monthly", "annually"
    features: List[str] = Field(default_factory=list)
    is_popular: bool = False

    @field_validator('price', mode='before')
    @classmethod
    def parse_price(cls, v) -> Optional[Decimal]:
        """Convert string prices to Decimal.

        Handles formats:
        - "$99.00" -> Decimal("99.00")
        - "99" -> Decimal("99.00")
        - "Free" -> None
        - "Contact us" -> None
        """
        if v is None:
            return None
        if isinstance(v, str):
            # Remove currency symbols and commas
            v = v.replace('$', '').replace(',', '').replace('€', '').replace('£', '').strip()
            if v.lower() in ['free', 'contact us', 'custom', '']:
                return None
        try:
            return Decimal(v) if v else None
        except (ValueError, TypeError):
            return None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Professional",
                "price": "99.00",
                "billing_period": "monthly",
                "features": ["Unlimited sessions", "AI notes", "Priority support"],
                "is_popular": True
            }
        }
    }


class Testimonial(BaseModel):
    """User testimonial (anonymized).

    GDPR-compliant: No personal names or identifying information.
    """

    quote: str = Field(..., min_length=1)
    role: Optional[str] = None  # "Therapist", "Psychologist", etc.
    organization: Optional[str] = None

    # NO personal names - anonymized only

    model_config = {
        "json_schema_extra": {
            "example": {
                "quote": "Upheal has transformed my practice workflow",
                "role": "Licensed Therapist",
                "organization": None
            }
        }
    }


class UphealData(BaseModel):
    """Complete scraped data from Upheal website.

    Main container for all scraped information with export capabilities.
    """

    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    source_url: HttpUrl
    features: List[Feature] = Field(default_factory=list)
    pricing_tiers: List[PricingTier] = Field(default_factory=list)
    testimonials: List[Testimonial] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "scraped_at": "2025-01-15T10:30:00Z",
                "source_url": "https://www.upheal.io/features",
                "features": [],
                "pricing_tiers": [],
                "testimonials": []
            }
        }
    }

    def export_json(self, filepath: str) -> None:
        """Export complete data to JSON file.

        Args:
            filepath: Target JSON file path

        Example:
            data.export_json('output/upheal_data.json')
        """
        import json
        from pathlib import Path

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                self.model_dump(mode='json'),
                f,
                indent=2,
                default=str
            )

    def export_csv(self, filepath: str) -> None:
        """Export features and pricing to separate CSV files.

        Creates two files:
        - {filepath}_features.csv: All features
        - {filepath}_pricing.csv: All pricing tiers

        Args:
            filepath: Base CSV file path (will be suffixed)

        Example:
            data.export_csv('output/upheal.csv')
            # Creates: output/upheal_features.csv, output/upheal_pricing.csv
        """
        import pandas as pd
        from pathlib import Path

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Export features
        if self.features:
            features_df = pd.DataFrame([f.model_dump() for f in self.features])
            features_csv = filepath.replace('.csv', '_features.csv')
            features_df.to_csv(features_csv, index=False, encoding='utf-8')

        # Export pricing
        if self.pricing_tiers:
            pricing_data = []
            for tier in self.pricing_tiers:
                tier_dict = tier.model_dump()
                # Convert list of features to comma-separated string for CSV
                tier_dict['features'] = ', '.join(tier_dict.get('features', []))
                pricing_data.append(tier_dict)

            pricing_df = pd.DataFrame(pricing_data)
            pricing_csv = filepath.replace('.csv', '_pricing.csv')
            pricing_df.to_csv(pricing_csv, index=False, encoding='utf-8')

    def summary(self) -> str:
        """Generate human-readable summary of scraped data.

        Returns:
            Formatted summary string
        """
        return f"""Upheal Data Summary
==================
Scraped at: {self.scraped_at.isoformat()}
Source URL: {self.source_url}

Features: {len(self.features)}
Pricing Tiers: {len(self.pricing_tiers)}
Testimonials: {len(self.testimonials)}

Categories:
{self._summarize_categories()}

Pricing Range:
{self._summarize_pricing()}
"""

    def _summarize_categories(self) -> str:
        """Summarize feature categories."""
        categories = {}
        for feature in self.features:
            cat = feature.category or "Uncategorized"
            categories[cat] = categories.get(cat, 0) + 1

        if not categories:
            return "  No features found"

        return '\n'.join(f"  {cat}: {count}" for cat, count in sorted(categories.items()))

    def _summarize_pricing(self) -> str:
        """Summarize pricing information."""
        prices = [tier.price for tier in self.pricing_tiers if tier.price is not None]

        if not prices:
            return "  No pricing information available"

        min_price = min(prices)
        max_price = max(prices)
        return f"  ${min_price} - ${max_price}"
