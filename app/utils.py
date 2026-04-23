"""
Utility functions for the GMB Dashboard API
"""
import os
from datetime import datetime, timedelta  # Fixed: Added timedelta
import secrets
import string
import hashlib
from typing import Optional, Dict, Any, List  # Fixed: Added List
import json
import re  # Fixed: Moved to top level


# ==========================================
# EXISTING FUNCTION (PRESERVED)
# ==========================================

def generate_csv_path(api_key: str) -> str:
    """
    Generate CSV path for leads export (existing function)
    
    Args:
        api_key: API key identifier
        
    Returns:
        Full path to CSV file
    """
    filename = f"leads_export_{api_key}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    path = os.path.join("/tmp", filename)
    return path


# ==========================================
# NEW GMB DASHBOARD UTILITIES
# ==========================================

def generate_export_path(filename: str, export_type: str = "csv") -> str:
    """
    Generate path for GMB dashboard exports
    
    Args:
        filename: Base name for the file
        export_type: Type of export (csv, pdf, json)
        
    Returns:
        Full path to the export file
    """
    # Create exports directory if it doesn't exist
    if os.name == 'nt':  # Windows
        exports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
    else:  # Linux/Mac
        exports_dir = "/tmp/gmb_exports"
    
    os.makedirs(exports_dir, exist_ok=True)
    
    # Add timestamp to filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_filename = sanitize_filename(filename)
    export_filename = f"{clean_filename}_{timestamp}.{export_type}"
    
    return os.path.join(exports_dir, export_filename)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system operations
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    sanitized = ''.join(c for c in filename if c in valid_chars)
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized or "export"


def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure random API key
    
    Args:
        length: Length of the API key
        
    Returns:
        Random API key string (URL-safe)
    """
    return secrets.token_urlsafe(length)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage
    
    Args:
        api_key: Plain text API key
        
    Returns:
        SHA256 hash of the API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def format_phone_number(phone: str, country_code: str = "+91") -> str:
    """
    Format phone number to standard format (Indian by default)
    
    Args:
        phone: Raw phone number
        country_code: Country code prefix
        
    Returns:
        Formatted phone number
    """
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Format for Indian numbers (10 digits)
    if len(digits) == 10:
        return f"{country_code}-{digits[:5]}-{digits[5:]}"
    elif len(digits) == 12 and digits.startswith('91'):
        return f"+91-{digits[2:7]}-{digits[7:]}"
    elif len(digits) == 11 and digits.startswith('1'):  # US numbers
        return f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
    
    # Return original if format not recognized
    return phone


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values
    
    Args:
        old_value: Previous value
        new_value: Current value
        
    Returns:
        Percentage change (positive or negative)
    """
    if old_value == 0:
        return 0 if new_value == 0 else 100.0
    
    change = ((new_value - old_value) / old_value) * 100
    return round(change, 2)


def calculate_growth_rate(values: List[float], period: str = "daily") -> float:
    """
    Calculate growth rate over a period
    
    Args:
        values: List of values over time
        period: Time period (daily, weekly, monthly)
        
    Returns:
        Average growth rate percentage
    """
    if len(values) < 2:
        return 0.0
    
    changes = []
    for i in range(1, len(values)):
        if values[i-1] != 0:
            change = ((values[i] - values[i-1]) / values[i-1]) * 100
            changes.append(change)
    
    return round(sum(changes) / len(changes), 2) if changes else 0.0


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    truncated_length = max_length - len(suffix)
    return text[:truncated_length].rstrip() + suffix


def format_currency(amount: float, currency: str = "INR", symbol: str = "₹") -> str:
    """
    Format amount as currency
    
    Args:
        amount: Amount to format
        currency: Currency code
        symbol: Currency symbol
        
    Returns:
        Formatted currency string
    """
    if currency == "INR":
        # Indian numbering system (lakhs, crores)
        if amount >= 10000000:  # 1 crore
            return f"{symbol}{amount/10000000:.2f} Cr"
        elif amount >= 100000:  # 1 lakh
            return f"{symbol}{amount/100000:.2f} L"
        else:
            return f"{symbol}{amount:,.2f}"
    else:
        # International format
        return f"{symbol}{amount:,.2f}"


def parse_date_range(date_string: str) -> tuple:
    """
    Parse date range string to start and end dates
    
    Args:
        date_string: Date range like "last_7_days", "last_30_days", "this_month"
        
    Returns:
        Tuple of (start_date, end_date)
    """
    now = datetime.now()
    
    if date_string == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif date_string == "yesterday":
        start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(hour=23, minute=59, second=59)
    elif date_string == "last_7_days":
        start = now - timedelta(days=7)
        end = now
    elif date_string == "last_30_days":
        start = now - timedelta(days=30)
        end = now
    elif date_string == "last_90_days":
        start = now - timedelta(days=90)
        end = now
    elif date_string == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif date_string == "last_month":
        first_day_this_month = now.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        start = last_day_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = last_day_last_month.replace(hour=23, minute=59, second=59)
    else:
        # Default to last 30 days
        start = now - timedelta(days=30)
        end = now
    
    return start, end


def calculate_roi(investment: float, revenue: float) -> float:
    """
    Calculate Return on Investment percentage
    
    Args:
        investment: Amount invested
        revenue: Revenue generated
        
    Returns:
        ROI percentage
    """
    if investment == 0:
        return 0.0
    
    roi = ((revenue - investment) / investment) * 100
    return round(roi, 2)


def validate_url(url: str) -> bool:
    """
    Validate if string is a valid URL
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(url))


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL
    
    Args:
        url: Full URL
        
    Returns:
        Domain name or None
    """
    match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', url)
    return match.group(1) if match else None


def generate_slug(text: str) -> str:
    """
    Generate URL-friendly slug from text
    
    Args:
        text: Text to convert
        
    Returns:
        URL-friendly slug
    """
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    
    # Remove special characters
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    
    # Remove consecutive hyphens
    while '--' in slug:
        slug = slug.replace('--', '-')
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug


def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """
    Mask sensitive data (email, phone, API key)
    
    Args:
        data: Sensitive data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to keep visible
        
    Returns:
        Masked string
    """
    if len(data) <= visible_chars:
        return data
    
    visible_part = data[-visible_chars:]
    masked_part = mask_char * (len(data) - visible_chars)
    
    return masked_part + visible_part


def generate_color_from_string(text: str) -> str:
    """
    Generate consistent color hex code from string (for avatars, badges)
    
    Args:
        text: Input text
        
    Returns:
        Hex color code
    """
    hash_value = hashlib.md5(text.encode()).hexdigest()
    return f"#{hash_value[:6]}"


def time_ago(dt: datetime) -> str:
    """
    Convert datetime to human-readable "time ago" format
    
    Args:
        dt: Datetime object
        
    Returns:
        Human-readable time string
    """
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


def batch_process(items: List[Any], batch_size: int = 100):
    """
    Generator to process items in batches
    
    Args:
        items: List of items to process
        batch_size: Size of each batch
        
    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is 0
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        Division result or default
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


# ==========================================
# JSON HELPERS
# ==========================================

def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """
    Safely parse JSON string
    
    Args:
        json_string: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely convert object to JSON string
    
    Args:
        obj: Object to convert
        default: Default value if conversion fails
        
    Returns:
        JSON string or default
    """
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default