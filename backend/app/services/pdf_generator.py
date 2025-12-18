"""PDF generation service using WeasyPrint and Jinja2"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

logger = logging.getLogger(__name__)


class PDFGeneratorService:
    """Service for generating PDF documents from templates"""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize PDF generator with template directory"""
        self.template_dir = template_dir or Path("app/templates/exports")

        if not self.template_dir.exists():
            raise ValueError(f"Template directory not found: {self.template_dir}")

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        self.env.filters['format_date'] = lambda d: d.strftime('%B %d, %Y') if d else 'N/A'
        self.env.filters['format_datetime'] = lambda d: d.strftime('%B %d, %Y at %I:%M %p') if d else 'N/A'

        # WeasyPrint font configuration
        self.font_config = FontConfiguration()

    async def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render Jinja2 template to HTML.

        Args:
            template_name: Template filename (e.g., 'progress_report.html')
            context: Template context variables

        Returns:
            Rendered HTML string

        Raises:
            ValueError: If template not found or rendering fails
        """
        try:
            template = self.env.get_template(template_name)

            # Add default context variables
            context.setdefault('generated_at', datetime.utcnow())

            html_content = template.render(**context)
            logger.info(f"Template rendered successfully: {template_name}")
            return html_content

        except TemplateNotFound:
            raise ValueError(f"Template not found: {template_name}")
        except Exception as e:
            logger.error(f"Template rendering failed: {e}", exc_info=True)
            raise ValueError(f"Failed to render template: {str(e)}")

    async def generate_pdf(
        self,
        html_content: str,
        custom_css: Optional[str] = None
    ) -> bytes:
        """
        Convert HTML to PDF using WeasyPrint.

        Args:
            html_content: Rendered HTML string
            custom_css: Optional custom CSS string

        Returns:
            PDF file as bytes

        Raises:
            ValueError: If PDF generation fails
        """
        try:
            logger.info("Starting PDF generation")
            start_time = datetime.utcnow()

            # Create WeasyPrint HTML object
            html = HTML(string=html_content)

            # Generate PDF with optional custom CSS
            if custom_css:
                css = CSS(string=custom_css, font_config=self.font_config)
                pdf_bytes = html.write_pdf(stylesheets=[css], font_config=self.font_config)
            else:
                pdf_bytes = html.write_pdf(font_config=self.font_config)

            duration = (datetime.utcnow() - start_time).total_seconds()
            size_kb = len(pdf_bytes) / 1024

            logger.info(
                f"PDF generated successfully",
                extra={
                    "duration_seconds": duration,
                    "size_kb": round(size_kb, 2)
                }
            )

            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            raise ValueError(f"Failed to generate PDF: {str(e)}")

    async def generate_from_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        custom_css: Optional[str] = None
    ) -> bytes:
        """
        Render template and generate PDF in one step.

        Args:
            template_name: Template filename
            context: Template context variables
            custom_css: Optional custom CSS

        Returns:
            PDF file as bytes
        """
        html_content = await self.render_template(template_name, context)
        pdf_bytes = await self.generate_pdf(html_content, custom_css)
        return pdf_bytes


def get_pdf_generator() -> PDFGeneratorService:
    """FastAPI dependency to provide PDF generator service"""
    return PDFGeneratorService()
