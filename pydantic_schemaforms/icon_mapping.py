"""
Icon mapping utility for pydantic-schemaforms.

This module provides a system to switch between different icon frameworks
(Bootstrap Icons vs Material Design Icons) based on the UI framework being used.
"""

from typing import Optional

# Icon mapping dictionary - maps semantic icon names to framework-specific icons
ICON_MAPPING = {
    # User and Person icons
    "person": {"bootstrap": "bi bi-person", "material": "person"},
    "person-badge": {"bootstrap": "bi bi-person-badge", "material": "badge"},
    "person-exclamation": {"bootstrap": "bi bi-person-exclamation", "material": "person_alert"},
    "people": {"bootstrap": "bi bi-people", "material": "people"},
    # Communication icons
    "envelope": {"bootstrap": "bi bi-envelope", "material": "email"},
    "email": {"bootstrap": "bi bi-envelope", "material": "email"},
    "envelope-heart": {"bootstrap": "bi bi-envelope-heart", "material": "favorite"},
    "telephone": {"bootstrap": "bi bi-telephone", "material": "phone"},
    "at": {"bootstrap": "bi bi-at", "material": "alternate_email"},
    # Security icons
    "lock": {"bootstrap": "bi bi-lock", "material": "lock"},
    "lock-fill": {"bootstrap": "bi bi-lock-fill", "material": "lock"},
    "shield": {"bootstrap": "bi bi-shield", "material": "shield"},
    "shield-check": {"bootstrap": "bi bi-shield-check", "material": "verified_user"},
    "shield-lock": {"bootstrap": "bi bi-shield-lock", "material": "security"},
    "shield-exclamation": {"bootstrap": "bi bi-shield-exclamation", "material": "warning"},
    # Animals and Pets
    "heart": {"bootstrap": "bi bi-heart", "material": "favorite_border"},
    "heart-fill": {"bootstrap": "bi bi-heart-fill", "material": "favorite"},
    "heart-pulse": {"bootstrap": "bi bi-heart-pulse", "material": "monitor_heart"},
    # UI and Selection
    "collection": {"bootstrap": "bi bi-collection", "material": "collections"},
    "list": {"bootstrap": "bi bi-list", "material": "list"},
    "list-check": {"bootstrap": "bi bi-list-check", "material": "checklist"},
    "check-square": {"bootstrap": "bi bi-check-square", "material": "check_box"},
    "check2-square": {"bootstrap": "bi bi-check2-square", "material": "check_box"},
    "ui-radios": {"bootstrap": "bi bi-ui-radios", "material": "radio_button_checked"},
    "toggle-on": {"bootstrap": "bi bi-toggle-on", "material": "toggle_on"},
    # Numbers and Math
    "calendar": {"bootstrap": "bi bi-calendar", "material": "calendar_today"},
    "calendar-date": {"bootstrap": "bi bi-calendar-date", "material": "event"},
    "calendar-event": {"bootstrap": "bi bi-calendar-event", "material": "event"},
    "clock": {"bootstrap": "bi bi-clock", "material": "schedule"},
    "hash": {"bootstrap": "bi bi-hash", "material": "numbers"},
    "123": {"bootstrap": "bi bi-123", "material": "numbers"},
    "calculator": {"bootstrap": "bi bi-calculator", "material": "calculate"},
    "speedometer2": {"bootstrap": "bi bi-speedometer2", "material": "speed"},
    "sliders": {"bootstrap": "bi bi-sliders", "material": "tune"},
    # Visual and Media
    "palette": {"bootstrap": "bi bi-palette", "material": "palette"},
    "star": {"bootstrap": "bi bi-star", "material": "star"},
    "trophy": {"bootstrap": "bi bi-trophy", "material": "emoji_events"},
    "award": {"bootstrap": "bi bi-award", "material": "military_tech"},
    # Location and Places
    "house": {"bootstrap": "bi bi-house", "material": "home"},
    "globe": {"bootstrap": "bi bi-globe", "material": "public"},
    # Technology
    "cpu": {"bootstrap": "bi bi-cpu", "material": "memory"},
    "link-45deg": {"bootstrap": "bi bi-link-45deg", "material": "link"},
    "cloud-upload": {"bootstrap": "bi bi-cloud-upload", "material": "cloud_upload"},
    "search": {"bootstrap": "bi bi-search", "material": "search"},
    # Communication and Messaging
    "chat-left-text": {"bootstrap": "bi bi-chat-left-text", "material": "chat"},
    "chat-left-dots": {"bootstrap": "bi bi-chat-left-dots", "material": "chat_bubble"},
    "chat-dots": {"bootstrap": "bi bi-chat-dots", "material": "chat_bubble_outline"},
    "mailbox": {"bootstrap": "bi bi-mailbox", "material": "mail"},
    "newspaper": {"bootstrap": "bi bi-newspaper", "material": "newspaper"},
    "bell": {"bootstrap": "bi bi-bell", "material": "notifications"},
    # UI Elements
    "textarea-resize": {"bootstrap": "bi bi-textarea-resize", "material": "text_fields"},
    "exclamation-triangle": {"bootstrap": "bi bi-exclamation-triangle", "material": "warning"},
    # Additional specific icons
    "person-lines-fill": {"bootstrap": "bi bi-person-lines-fill", "material": "contact_page"},
}


def get_icon(semantic_name: str, framework: str = "bootstrap") -> Optional[str]:
    """
    Get the appropriate icon class for a given semantic name and framework.

    Args:
        semantic_name: The semantic name of the icon (e.g., "person", "envelope")
        framework: The UI framework ("bootstrap" or "material")

    Returns:
        The framework-specific icon class, or None if not found
    """
    if semantic_name in ICON_MAPPING:
        return ICON_MAPPING[semantic_name].get(framework)
    return None


def map_icon_for_framework(icon_value: str, target_framework: str = "bootstrap") -> str:
    """
    Convert an icon value to the appropriate framework.

    Args:
        icon_value: Current icon value (could be Bootstrap "bi bi-person" or semantic "person")
        target_framework: Target framework ("bootstrap" or "material")

    Returns:
        The icon value for the target framework
    """
    # If it's already a bootstrap icon, extract the semantic name
    if icon_value.startswith("bi bi-"):
        semantic_name = icon_value.replace("bi bi-", "")
        mapped_icon = get_icon(semantic_name, target_framework)
        return mapped_icon if mapped_icon else icon_value

    # If it's a semantic name, map it directly
    mapped_icon = get_icon(icon_value, target_framework)
    return mapped_icon if mapped_icon else icon_value


def update_field_icons_for_framework(form_fields: dict, framework: str = "bootstrap") -> dict:
    """
    Update all icon values in form fields for a specific framework.

    Args:
        form_fields: Dictionary of form field definitions
        framework: Target framework ("bootstrap" or "material")

    Returns:
        Updated form fields dictionary with framework-appropriate icons
    """
    updated_fields = {}

    for field_name, field_config in form_fields.items():
        updated_config = field_config.copy()

        if "icon" in updated_config:
            updated_config["icon"] = map_icon_for_framework(updated_config["icon"], framework)

        updated_fields[field_name] = updated_config

    return updated_fields


# Convenience functions for specific frameworks
def get_bootstrap_icon(semantic_name: str) -> Optional[str]:
    """Get Bootstrap icon class for semantic name."""
    return get_icon(semantic_name, "bootstrap")


def get_material_icon(semantic_name: str) -> Optional[str]:
    """Get Material Design icon class for semantic name."""
    return get_icon(semantic_name, "material")
