import logging
from typing import Dict, Any, List, Optional
import datetime

from ..config import settings

logger = logging.getLogger(__name__)


class ReceiptFormatter:
    """Formats processed shopping lists for receipt-style output."""
    
    def __init__(self):
        self.width = settings.receipt_width
    
    def format_for_receipt(self, content: str, store_name: Optional[str] = None) -> str:
        """
        Format the processed list for receipt-style printing.
        
        Args:
            content: The processed list content from the LLM
            store_name: Optional store name to include in header
            
        Returns:
            Formatted text ready for receipt printing
        """
        store = store_name or settings.default_store
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Create header
        header = [
            self._center_text(f"SHOPPING LIST"),
            self._center_text(store),
            self._center_text(date),
            "-" * self.width
        ]
        
        # Format the main content
        # No need to modify the content as the LLM should have
        # already formatted it correctly for our receipt width
        
        # Create footer
        footer = [
            "-" * self.width,
            self._center_text("Happy Shopping!")
        ]
        
        # Combine all parts
        formatted_list = "\n".join(header) + "\n" + content + "\n" + "\n".join(footer)
        return formatted_list
    
    def format_for_html(self, content: str, store_name: Optional[str] = None) -> str:
        """
        Format the processed list as HTML for web display.
        
        Args:
            content: The processed list content from the LLM
            store_name: Optional store name to include in header
            
        Returns:
            HTML formatted version of the list
        """
        store = store_name or settings.default_store
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Replace newlines with <br> tags
        html_content = content.replace("\n", "<br>")
        
        # Simple HTML wrapper
        html = f"""
        <div class="receipt">
            <div class="receipt-header">
                <h2>SHOPPING LIST</h2>
                <h3>{store}</h3>
                <p>{date}</p>
                <hr>
            </div>
            <div class="receipt-content">
                {html_content}
            </div>
            <div class="receipt-footer">
                <hr>
                <p>Happy Shopping!</p>
            </div>
        </div>
        """
        
        return html
    
    def _center_text(self, text: str) -> str:
        """Center text within the receipt width."""
        return text.center(self.width)


# Factory function for getting the formatter
def get_formatter():
    return ReceiptFormatter()