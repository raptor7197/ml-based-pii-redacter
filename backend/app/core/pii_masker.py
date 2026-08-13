"""
PII Masking Utilities
Provides partial masking for safe display of PII values in UI
"""
import re
from typing import Optional


def mask_pii_value(value: str, pii_type: str) -> str:
    """
    Partially mask a PII value for safe display
    Shows first and last characters, masks the middle

    Examples:
        john@email.com -> j***@e***.com
        123-45-6789 -> 1**-**-***9
        John Doe -> J** D**
    """
    if not value or len(value) <= 2:
        return "*" * len(value)

    masked = _mask_by_type(value, pii_type)
    return masked


def _mask_by_type(value: str, pii_type: str) -> str:
    """Apply type-specific masking strategies"""

    if pii_type == "EMAIL_ADDRESS":
        return _mask_email(value)
    elif pii_type == "PHONE_NUMBER":
        return _mask_phone(value)
    elif pii_type == "SSN":
        return _mask_ssn(value)
    elif pii_type == "CREDIT_CARD":
        return _mask_credit_card(value)
    elif pii_type == "IP_ADDRESS":
        return _mask_ip(value)
    elif pii_type == "URL":
        return _mask_url(value)
    else:
        return _mask_generic(value)


def _mask_email(email: str) -> str:
    """Mask email: j***@e***.com"""
    if "@" not in email:
        return _mask_generic(email)

    local, domain = email.split("@", 1)

    # Mask local part
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * (len(local) - 1)

    # Mask domain
    if "." in domain:
        domain_name, tld = domain.rsplit(".", 1)
        if len(domain_name) <= 2:
            masked_domain = "*" * len(domain_name)
        else:
            masked_domain = domain_name[0] + "*" * (len(domain_name) - 1)
        masked_email = f"{masked_local}@{masked_domain}.{tld}"
    else:
        masked_email = f"{masked_local}@***"

    return masked_email


def _mask_phone(phone: str) -> str:
    """Mask phone: show only last 4 digits"""
    digits = re.sub(r'\D', '', phone)

    if len(digits) < 4:
        return "*" * len(phone)

    # Keep last 4, mask rest
    masked_digits = "*" * (len(digits) - 4) + digits[-4:]

    # Try to preserve original formatting
    result = ""
    digit_idx = 0
    for char in phone:
        if char.isdigit():
            result += masked_digits[digit_idx]
            digit_idx += 1
        else:
            result += char

    return result


def _mask_ssn(ssn: str) -> str:
    """Mask SSN: show only last 4"""
    parts = ssn.split("-")
    if len(parts) == 3:
        return f"***-**-{parts[2]}"
    return "*" * len(ssn)


def _mask_credit_card(card: str) -> str:
    """Mask credit card: show only last 4"""
    digits = re.sub(r'\D', '', card)

    if len(digits) < 4:
        return "*" * len(card)

    masked = "*" * (len(digits) - 4) + digits[-4:]

    # Preserve spacing/dashes
    result = ""
    digit_idx = 0
    for char in card:
        if char.isdigit():
            result += masked[digit_idx]
            digit_idx += 1
        else:
            result += char

    return result


def _mask_ip(ip: str) -> str:
    """Mask IP: show only first octet"""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.*.*.*"
    return "*" * len(ip)


def _mask_url(url: str) -> str:
    """Mask URL: show domain only"""
    # Remove protocol
    clean = re.sub(r'^https?://', '', url)

    # Get domain
    domain = clean.split("/")[0]

    return f"https://{domain}/***"


def _mask_generic(text: str) -> str:
    """Generic masking: show first char and last 2 chars"""
    if len(text) <= 4:
        return "*" * len(text)
    elif len(text) <= 8:
        return text[0] + "*" * (len(text) - 2) + text[-1]
    else:
        return text[0:2] + "*" * (len(text) - 4) + text[-2:]


def mask_text_content(text: str) -> str:
    """
    Scan text for PII patterns and mask all found PII
    Returns text with all PII partially masked
    """
    from app.core.pii_detector import PIIDetector

    detector = PIIDetector()
    findings = detector.detect_pii(text)

    if not findings:
        return text

    # Sort findings by position (reverse order to replace from end to start)
    # to avoid offset issues when replacing
    sorted_findings = sorted(findings, key=lambda x: x.get("start", 0), reverse=True)

    masked_text = text

    # Apply masks in reverse order to preserve positions
    for finding in sorted_findings:
        original = finding.get("text", "")
        pii_type = finding.get("entity_type", "UNKNOWN")
        masked = mask_pii_value(original, pii_type)
        masked_text = masked_text.replace(original, masked, 1)

    return masked_text
