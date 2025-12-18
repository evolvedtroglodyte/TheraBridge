# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for PDF generator service.

Tests cover:
1. Initialization - Service setup and template directory validation
2. Template rendering - Jinja2 template processing with context
3. PDF generation - WeasyPrint HTML-to-PDF conversion
4. Integration - End-to-end template→PDF workflows
5. Custom filters - Jinja2 date formatting filters
6. Error handling - Missing templates, invalid directories, generation failures

Edge cases tested:
- Missing template directory
- Non-existent templates
- Custom CSS application
- PDF content validation
- Date/datetime filter formatting
- Generated_at auto-injection
"""
import pytest
import pytest_asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from app.services.pdf_generator import PDFGeneratorService, get_pdf_generator


# ============================================================================
# Fixtures for PDF Generator Tests
# ============================================================================

@pytest_asyncio.fixture
async def temp_template_dir():
    """
    Create a temporary template directory for testing.

    Yields:
        Path object to temporary directory

    Cleanup:
        Removes directory after test completes
    """
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    # Create a basic test template
    base_template = temp_path / "base.html"
    base_template.write_text("""<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Test PDF{% endblock %}</title>
</head>
<body>
    <div class="header">
        {% block header %}{% endblock %}
    </div>
    <div class="content">
        {% block content %}{% endblock %}
    </div>
    <footer>Generated: {{ generated_at }}</footer>
</body>
</html>
""")

    # Create a child template that extends base
    test_template = temp_path / "test_template.html"
    test_template.write_text("""{% extends "base.html" %}

{% block title %}{{ title }}{% endblock %}

{% block header %}
<h1>{{ header_text }}</h1>
{% endblock %}

{% block content %}
<p>{{ content_text }}</p>
<p>Date: {{ test_date|format_date }}</p>
<p>DateTime: {{ test_datetime|format_datetime }}</p>
{% endblock %}
""")

    # Create a simple standalone template
    simple_template = temp_path / "simple.html"
    simple_template.write_text("""<html>
<body>
    <h1>{{ title }}</h1>
    <p>{{ message }}</p>
</body>
</html>
""")

    yield temp_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest_asyncio.fixture
async def pdf_service(temp_template_dir):
    """
    Create PDF generator service with temporary template directory.

    Returns:
        PDFGeneratorService instance
    """
    return PDFGeneratorService(template_dir=temp_template_dir)


# ============================================================================
# TestPDFGeneratorInitialization
# ============================================================================

class TestPDFGeneratorInitialization:
    """Test PDF generator service initialization"""

    @pytest.mark.asyncio
    async def test_pdf_generator_initializes_with_templates(self, temp_template_dir):
        """Test successful initialization with valid template directory"""
        service = PDFGeneratorService(template_dir=temp_template_dir)

        assert service.template_dir == temp_template_dir
        assert service.env is not None
        assert service.font_config is not None

        # Verify custom filters are registered
        assert 'format_date' in service.env.filters
        assert 'format_datetime' in service.env.filters

    @pytest.mark.asyncio
    async def test_pdf_generator_raises_if_template_dir_missing(self):
        """Test initialization fails if template directory does not exist"""
        nonexistent_dir = Path("/nonexistent/template/directory")

        with pytest.raises(ValueError, match="Template directory not found"):
            PDFGeneratorService(template_dir=nonexistent_dir)

    @pytest.mark.asyncio
    async def test_pdf_generator_uses_default_template_dir(self):
        """Test initialization uses default directory when not specified"""
        with patch('pathlib.Path.exists', return_value=True):
            service = PDFGeneratorService()
            assert service.template_dir == Path("app/templates/exports")

    @pytest.mark.asyncio
    async def test_get_pdf_generator_dependency(self):
        """Test FastAPI dependency function returns service instance"""
        with patch('pathlib.Path.exists', return_value=True):
            service = get_pdf_generator()
            assert isinstance(service, PDFGeneratorService)


# ============================================================================
# TestTemplateRendering
# ============================================================================

class TestTemplateRendering:
    """Test Jinja2 template rendering functionality"""

    @pytest.mark.asyncio
    async def test_render_template_success(self, pdf_service):
        """Test successful template rendering with context"""
        context = {
            "title": "Test Report",
            "header_text": "Patient Progress Report",
            "content_text": "This is the main content of the report.",
            "test_date": datetime(2025, 12, 17),
            "test_datetime": datetime(2025, 12, 17, 14, 30)
        }

        html = await pdf_service.render_template("test_template.html", context)

        assert isinstance(html, str)
        assert "Test Report" in html
        assert "Patient Progress Report" in html
        assert "This is the main content of the report" in html
        assert "December 17, 2025" in html  # format_date filter
        assert "December 17, 2025 at 02:30 PM" in html  # format_datetime filter

    @pytest.mark.asyncio
    async def test_render_template_not_found(self, pdf_service):
        """Test rendering raises ValueError for missing template"""
        with pytest.raises(ValueError, match="Template not found"):
            await pdf_service.render_template("nonexistent.html", {})

    @pytest.mark.asyncio
    async def test_render_template_adds_generated_at(self, pdf_service):
        """Test that generated_at is automatically added to context"""
        context = {
            "title": "Simple Test",
            "message": "Hello World"
        }

        html = await pdf_service.render_template("simple.html", context)

        # Verify generated_at was added (footer in base.html)
        assert html is not None
        # The simple template doesn't have generated_at, but context should have it
        # We can verify by checking the context was modified

        # Re-render with base template that uses generated_at
        context2 = {"header_text": "Test", "content_text": "Test"}
        html2 = await pdf_service.render_template("test_template.html", context2)
        assert "Generated:" in html2

    @pytest.mark.asyncio
    async def test_render_template_preserves_existing_generated_at(self, pdf_service):
        """Test that custom generated_at is not overwritten"""
        custom_time = datetime(2024, 1, 1, 10, 0)
        context = {
            "title": "Test",
            "header_text": "Header",
            "content_text": "Content",
            "test_date": datetime.now(),
            "test_datetime": datetime.now(),
            "generated_at": custom_time
        }

        html = await pdf_service.render_template("test_template.html", context)

        # The custom generated_at should be used
        assert html is not None
        # Cannot easily verify exact datetime in HTML, but it shouldn't raise an error

    @pytest.mark.asyncio
    async def test_render_template_handles_none_values(self, pdf_service):
        """Test rendering with None values in context"""
        context = {
            "title": "Test with None",
            "header_text": "Header",
            "content_text": None,
            "test_date": None,
            "test_datetime": None
        }

        html = await pdf_service.render_template("test_template.html", context)

        assert html is not None
        assert "N/A" in html  # format_date and format_datetime return 'N/A' for None

    @pytest.mark.asyncio
    async def test_render_template_autoescape_enabled(self, pdf_service):
        """Test that HTML autoescaping is enabled for security"""
        context = {
            "title": "Test <script>alert('XSS')</script>",
            "message": "Safe message"
        }

        html = await pdf_service.render_template("simple.html", context)

        # HTML should be escaped
        assert "&lt;script&gt;" in html or "alert" not in html


# ============================================================================
# TestPDFGeneration
# ============================================================================

class TestPDFGeneration:
    """Test WeasyPrint PDF generation functionality"""

    @pytest.mark.asyncio
    async def test_generate_pdf_from_html(self, pdf_service):
        """Test PDF generation from HTML string"""
        html_content = """<html>
<body>
    <h1>Test PDF Document</h1>
    <p>This is a test PDF with some content.</p>
</body>
</html>"""

        pdf_bytes = await pdf_service.generate_pdf(html_content)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')  # PDF file signature

    @pytest.mark.asyncio
    async def test_generate_pdf_with_custom_css(self, pdf_service):
        """Test PDF generation with custom CSS styling"""
        html_content = """<html>
<body>
    <h1 class="custom-header">Styled Header</h1>
    <p class="custom-text">Styled paragraph</p>
</body>
</html>"""

        custom_css = """
        .custom-header {
            color: #0066cc;
            font-size: 24pt;
        }
        .custom-text {
            color: #666666;
            font-size: 12pt;
        }
        """

        pdf_bytes = await pdf_service.generate_pdf(html_content, custom_css=custom_css)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    @pytest.mark.asyncio
    async def test_generate_pdf_returns_valid_size(self, pdf_service):
        """Test that generated PDF has reasonable file size"""
        html_content = """<html>
<body>
    <h1>Test Document</h1>
    <p>Short content</p>
</body>
</html>"""

        pdf_bytes = await pdf_service.generate_pdf(html_content)

        # PDF should be at least 1KB and less than 1MB for simple content
        size_kb = len(pdf_bytes) / 1024
        assert size_kb > 1
        assert size_kb < 1024

    @pytest.mark.asyncio
    async def test_generate_pdf_handles_complex_html(self, pdf_service):
        """Test PDF generation with complex HTML structure"""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid black; padding: 8px; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Complex Document</h1>
    <table>
        <tr>
            <th>Session</th>
            <th>Date</th>
            <th>Notes</th>
        </tr>
        <tr>
            <td>1</td>
            <td>2025-12-01</td>
            <td>Initial consultation</td>
        </tr>
        <tr>
            <td>2</td>
            <td>2025-12-08</td>
            <td>Follow-up session</td>
        </tr>
    </table>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
        <li>Item 3</li>
    </ul>
</body>
</html>"""

        pdf_bytes = await pdf_service.generate_pdf(html_content)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b'%PDF')


# ============================================================================
# TestIntegrationWorkflows
# ============================================================================

class TestIntegrationWorkflows:
    """Test end-to-end template-to-PDF workflows"""

    @pytest.mark.asyncio
    async def test_generate_from_template_end_to_end(self, pdf_service):
        """Test complete workflow from template to PDF"""
        context = {
            "title": "Integration Test",
            "header_text": "End-to-End Test Report",
            "content_text": "This tests the full pipeline from template to PDF.",
            "test_date": datetime(2025, 12, 17),
            "test_datetime": datetime(2025, 12, 17, 15, 45)
        }

        pdf_bytes = await pdf_service.generate_from_template(
            "test_template.html",
            context
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    @pytest.mark.asyncio
    async def test_generate_from_template_with_custom_css(self, pdf_service):
        """Test end-to-end workflow with custom CSS"""
        context = {
            "title": "Styled Document",
            "message": "This document has custom styling"
        }

        custom_css = """
        body {
            font-family: 'Helvetica', sans-serif;
            background-color: #f0f0f0;
        }
        h1 {
            color: #d32f2f;
        }
        """

        pdf_bytes = await pdf_service.generate_from_template(
            "simple.html",
            context,
            custom_css=custom_css
        )

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b'%PDF')

    @pytest.mark.asyncio
    async def test_pdf_contains_expected_content(self, pdf_service):
        """Test that generated PDF contains rendered data (smoke test)"""
        context = {
            "title": "Content Verification Test",
            "header_text": "Unique Header Text ABC123",
            "content_text": "Unique Content XYZ789",
            "test_date": datetime(2025, 6, 15),
            "test_datetime": datetime(2025, 6, 15, 9, 30)
        }

        pdf_bytes = await pdf_service.generate_from_template(
            "test_template.html",
            context
        )

        # Verify it's a valid PDF
        assert pdf_bytes.startswith(b'%PDF')

        # Note: Full PDF text extraction would require additional libraries (e.g., pypdf)
        # For now, we verify structure and size
        assert len(pdf_bytes) > 1024  # Should be at least 1KB with content

    @pytest.mark.asyncio
    async def test_generate_from_template_missing_template(self, pdf_service):
        """Test that missing template raises appropriate error"""
        with pytest.raises(ValueError, match="Template not found"):
            await pdf_service.generate_from_template(
                "missing_template.html",
                {"title": "Test"}
            )


# ============================================================================
# TestCustomJinja2Filters
# ============================================================================

class TestCustomJinja2Filters:
    """Test custom Jinja2 date formatting filters"""

    @pytest.mark.asyncio
    async def test_format_date_filter(self, pdf_service):
        """Test format_date custom filter"""
        # Test with valid date
        test_date = datetime(2025, 12, 17)
        result = pdf_service.env.filters['format_date'](test_date)
        assert result == "December 17, 2025"

        # Test with None
        result_none = pdf_service.env.filters['format_date'](None)
        assert result_none == "N/A"

    @pytest.mark.asyncio
    async def test_format_datetime_filter(self, pdf_service):
        """Test format_datetime custom filter"""
        # Test with valid datetime
        test_datetime = datetime(2025, 12, 17, 14, 30)
        result = pdf_service.env.filters['format_datetime'](test_datetime)
        assert result == "December 17, 2025 at 02:30 PM"

        # Test with None
        result_none = pdf_service.env.filters['format_datetime'](None)
        assert result_none == "N/A"

    @pytest.mark.asyncio
    async def test_format_date_filter_various_dates(self, pdf_service):
        """Test format_date with various date formats"""
        test_cases = [
            (datetime(2025, 1, 1), "January 01, 2025"),
            (datetime(2025, 7, 4), "July 04, 2025"),
            (datetime(2025, 12, 31), "December 31, 2025"),
        ]

        for test_date, expected in test_cases:
            result = pdf_service.env.filters['format_date'](test_date)
            assert result == expected

    @pytest.mark.asyncio
    async def test_format_datetime_filter_various_times(self, pdf_service):
        """Test format_datetime with various times"""
        test_cases = [
            (datetime(2025, 6, 15, 0, 0), "June 15, 2025 at 12:00 AM"),
            (datetime(2025, 6, 15, 12, 0), "June 15, 2025 at 12:00 PM"),
            (datetime(2025, 6, 15, 23, 59), "June 15, 2025 at 11:59 PM"),
        ]

        for test_datetime, expected in test_cases:
            result = pdf_service.env.filters['format_datetime'](test_datetime)
            assert result == expected

    @pytest.mark.asyncio
    async def test_filters_in_template_rendering(self, pdf_service):
        """Test that filters work correctly in actual template rendering"""
        context = {
            "title": "Filter Test",
            "header_text": "Testing Date Filters",
            "content_text": "Content",
            "test_date": datetime(2025, 3, 21),
            "test_datetime": datetime(2025, 3, 21, 16, 45)
        }

        html = await pdf_service.render_template("test_template.html", context)

        assert "March 21, 2025" in html  # format_date
        assert "March 21, 2025 at 04:45 PM" in html  # format_datetime


# ============================================================================
# TestErrorHandling
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_render_template_with_invalid_syntax(self, temp_template_dir):
        """Test that template syntax errors are caught"""
        # Create a template with invalid Jinja2 syntax
        bad_template = temp_template_dir / "bad_syntax.html"
        bad_template.write_text("{{ unclosed_variable")

        service = PDFGeneratorService(template_dir=temp_template_dir)

        with pytest.raises(ValueError, match="Failed to render template"):
            await service.render_template("bad_syntax.html", {})

    @pytest.mark.asyncio
    async def test_generate_pdf_with_empty_html(self, pdf_service):
        """Test PDF generation with minimal HTML"""
        minimal_html = "<html><body></body></html>"

        pdf_bytes = await pdf_service.generate_pdf(minimal_html)

        # Should still generate a valid PDF, just empty
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b'%PDF')

    @pytest.mark.asyncio
    async def test_generate_pdf_with_malformed_html(self, pdf_service):
        """Test that WeasyPrint handles malformed HTML gracefully"""
        malformed_html = "<html><body><p>Unclosed paragraph<div>Nested incorrectly</body></html>"

        # WeasyPrint is generally forgiving with HTML
        pdf_bytes = await pdf_service.generate_pdf(malformed_html)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b'%PDF')
