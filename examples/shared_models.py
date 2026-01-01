"""
Shared form models for Pydantic SchemaForms examples.

This module contains all the form models used across different framework examples
(Flask, FastAPI, etc.) to demonstrate Pydantic SchemaForms capabilities.
"""

import os
import sys
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
from collections import defaultdict

from pydantic import EmailStr, field_validator

from pydantic_schemaforms.form_field import FormField
from pydantic_schemaforms.form_layouts import HorizontalLayout, TabbedLayout, VerticalLayout
from pydantic_schemaforms.schema_form import FormModel
from pydantic_schemaforms.validation import validate_form_data

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class Priority(str, Enum):
    """Priority levels for forms."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class UserRole(str, Enum):
    """User roles."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class Country(str, Enum):
    """Countries for selection."""
    US = "United States"
    CA = "Canada"
    UK = "United Kingdom"
    AU = "Australia"
    DE = "Germany"
    FR = "France"
    JP = "Japan"

# ============================================================================
# BASIC FORM MODELS
# ============================================================================

class PetModel(FormModel):
    """Enhanced pet information model showcasing various input types."""

    name: str = FormField(
        title="Pet's Name",
        input_type="text",
        placeholder="Enter your pet's name",
        help_text="The name of your pet",
        icon="heart",
        min_length=1,
        max_length=50
    )

    species: str = FormField(
        title="Species",
        input_type="select",
        options=[
            {"value": "Dog", "label": "Dog 🐕"},
            {"value": "Cat", "label": "Cat 🐱"},
            {"value": "Bird", "label": "Bird 🐦"},
            {"value": "Fish", "label": "Fish 🐠"},
            {"value": "Rabbit", "label": "Rabbit 🐰"},
            {"value": "Hamster", "label": "Hamster 🐹"},
            {"value": "Reptile", "label": "Reptile 🦎"},
            {"value": "Other", "label": "Other 🐾"}
        ],
        help_text="What type of animal is your pet?",
        icon="collection"
    )

    age: Optional[int] = FormField(
        None,
        title="Age",
        input_type="number",
        placeholder="Pet's age in years",
        help_text="How old is your pet? (optional)",
        icon="calendar",
        min_value=0,
        max_value=50
    )

    weight: Optional[float] = FormField(
        None,
        title="Weight (lbs)",
        input_type="number",
        placeholder="Pet's weight",
        help_text="Weight in pounds (optional - enter 0.01 for tiny pets like birds)",
        icon="speedometer2",
        min_value=0.01,
        max_value=500.0
    )

    is_vaccinated: bool = FormField(
        False,
        title="Vaccinated",
        input_type="checkbox",
        help_text="Is your pet up to date with vaccinations?",
        icon="shield-check"
    )

    microchipped: bool = FormField(
        False,
        title="Microchipped",
        input_type="checkbox",
        help_text="Does your pet have a microchip?",
        icon="cpu"
    )

    breed: Optional[str] = FormField(
        None,
        title="Breed",
        input_type="text",
        placeholder="e.g., Golden Retriever, Persian Cat",
        help_text="Specific breed of your pet (optional)",
        icon="award",
        max_length=100
    )

    color: Optional[str] = FormField(
        None,
        title="Primary Color",
        input_type="color",
        help_text="Primary color of your pet (optional)",
        icon="palette"
    )

    last_vet_visit: Optional[date] = FormField(
        None,
        title="Last Vet Visit",
        input_type="date",
        help_text="When was the last veterinary checkup? (optional)",
        icon="calendar-date"
    )

    special_needs: Optional[str] = FormField(
        None,
        title="Special Needs",
        input_type="textarea",
        placeholder="Any special care requirements, medications, allergies, etc.",
        help_text="Describe any special care requirements (optional)",
        icon="heart-pulse",
        max_length=500
    )

class MinimalLoginForm(FormModel):
    """Minimal form example - Simple login form."""

    username: str = FormField(
        title="Username",
        input_type="text",
        placeholder="Enter your username",
        help_text="Your username or email address",
        icon="person",
        min_length=3,
        max_length=50
    )

    password: str = FormField(
        title="Password",
        input_type="password",
        placeholder="Enter your password",
        help_text="Your account password",
        icon="lock",
        min_length=6
    )

    remember_me: bool = FormField(
        False,
        title="Remember me",
        input_type="checkbox",
        help_text="Keep me logged in on this device",
        icon="check2-square"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v.strip()

class UserRegistrationForm(FormModel):
    """User registration form with username, email, and password."""

    username: str = FormField(
        title="Username",
        input_type="text",
        placeholder="Choose a username",
        help_text="Your unique username (3-50 characters)",
        icon="person",
        min_length=3,
        max_length=50
    )

    email: EmailStr = FormField(
        title="Email Address",
        input_type="email",
        placeholder="your.email@example.com",
        help_text="Your email address for account verification",
        icon="email"
    )

    password: str = FormField(
        title="Password",
        input_type="password",
        placeholder="Create a strong password",
        help_text="Password must be at least 8 characters",
        icon="lock",
        min_length=8
    )

    confirm_password: str = FormField(
        title="Confirm Password",
        input_type="password",
        placeholder="Confirm your password",
        help_text="Re-enter your password to confirm",
        icon="lock"
    )

    age: Optional[int] = FormField(
        None,
        title="Age",
        input_type="number",
        placeholder="Your age (optional)",
        help_text="Your age in years",
        icon="calendar",
        min_value=13,
        max_value=120
    )

    role: UserRole = FormField(
        UserRole.USER,
        title="Account Type",
        input_type="select",
        options=[
            {"value": "user", "label": "👤 User"},
            {"value": "admin", "label": "🔑 Admin"},
            {"value": "moderator", "label": "🛡️ Moderator"}
        ],
        help_text="Select your account type",
        icon="shield"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError("Username cannot be empty")
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Username can only contain letters, numbers, hyphens, and underscores")
        return v.strip()

    @field_validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError("Passwords do not match")
        return v

class PetOwnerForm(FormModel):
    """Form that demonstrates ListLayout for pet management."""

    owner_name: str = FormField(
        title="Owner Name",
        input_type="text",
        placeholder="Enter your full name",
        help_text="Your full name as the pet owner",
        icon="person",
        min_length=2,
        max_length=100
    )

    email: EmailStr = FormField(
        title="Email Address",
        input_type="email",
        placeholder="your.email@example.com",
        help_text="Your contact email address",
        icon="envelope"
    )

    address: Optional[str] = FormField(
        None,
        title="Address",
        input_type="textarea",
        placeholder="Enter your full address...",
        help_text="Your home address (optional)",
        icon="house",
        max_length=500
    )

    emergency_contact: Optional[str] = FormField(
        None,
        title="Emergency Contact",
        input_type="text",
        placeholder="Emergency contact name and phone",
        help_text="Someone to contact in case of emergency",
        icon="person-exclamation",
        max_length=100
    )

class PetRegistrationForm(FormModel):
    """Complete pet registration form with owner information and pets list."""

    # Owner Information Section
    owner_name: str = FormField(
        title="Owner Name",
        input_type="text",
        placeholder="Enter your full name",
        help_text="Your full name as the pet owner",
        icon="person",
        min_length=2,
        max_length=100
    )

    email: EmailStr = FormField(
        title="Email Address",
        input_type="email",
        placeholder="your.email@example.com",
        help_text="Your contact email address",
        icon="envelope"
    )

    address: Optional[str] = FormField(
        None,
        title="Address",
        input_type="textarea",
        placeholder="Enter your full address...",
        help_text="Your home address (optional)",
        icon="house",
        max_length=500
    )

    emergency_contact: Optional[str] = FormField(
        None,
        title="Emergency Contact",
        input_type="text",
        placeholder="Emergency contact name and phone",
        help_text="Someone to contact in case of emergency",
        icon="person-exclamation",
        max_length=100
    )

    # Pets List Section - using model_list with collapsible cards
    pets: List[PetModel] = FormField(
        default_factory=list,
        title="Your Pets",
        input_type="model_list",
        help_text="Add information about each of your pets",
        icon="heart",
        min_length=1,
        max_length=10,
        model_class=PetModel,
        add_button_text="Add Another Pet",
        remove_button_text="Remove Pet",
        collapsible_items=True,
        items_expanded=False,  # Start collapsed to show the feature
        item_title_template="Pet #{index}: {name}",  # Dynamic titles
        section_design={
            "section_title": "Pet Registry",
            "section_description": "Register each of your beloved pets with detailed information",
            "icon": "bi bi-heart-fill",
            "collapsible": True,
            "collapsed": False
        }
    )

class MediumContactForm(FormModel):
    """Medium complexity form - Contact form with validation."""

    # Personal Information
    first_name: str = FormField(
        title="First Name",
        input_type="text",
        placeholder="Enter your first name",
        help_text="Your given name",
        icon="person",
        min_length=2,
        max_length=50
    )

    last_name: str = FormField(
        title="Last Name",
        input_type="text",
        placeholder="Enter your last name",
        help_text="Your family name",
        icon="person",
        min_length=2,
        max_length=50
    )

    email: EmailStr = FormField(
        title="Email Address",
        input_type="email",
        placeholder="your.email@example.com",
        help_text="We'll never share your email",
        icon="envelope"
    )

    phone: Optional[str] = FormField(
        None,
        title="Phone Number",
        input_type="tel",
        placeholder="+1 (555) 123-4567",
        help_text="Optional phone number",
        icon="telephone"
    )

    # Message Details
    subject: str = FormField(
        title="Subject",
        input_type="text",
        placeholder="Brief subject line",
        help_text="What is this message about?",
        icon="chat-left-text",
        min_length=5,
        max_length=200
    )

    message: str = FormField(
        title="Message",
        input_type="textarea",
        placeholder="Enter your detailed message here...",
        help_text="Please provide details about your inquiry",
        icon="chat-left-dots",
        min_length=10,
        max_length=2000
    )

    priority: Priority = FormField(
        Priority.MEDIUM,
        title="Priority Level",
        input_type="select",
        options=[p.value for p in Priority],
        help_text="How urgent is your request?",
        icon="exclamation-triangle"
    )

    # Preferences
    subscribe_newsletter: bool = FormField(
        False,
        title="Subscribe to Newsletter",
        input_type="checkbox",
        help_text="Receive updates and news",
        icon="newspaper"
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and len(v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        return v

class EmergencyContactModel(FormModel):
    """Emergency contact information model."""

    name: str = FormField(
        title="Contact Name",
        input_type="text",
        placeholder="John Doe",
        help_text="Full name of emergency contact",
        icon="person-badge",
        min_length=2,
        max_length=100
    )

    relationship: str = FormField(
        title="Relationship",
        input_type="select",
        options=[
            {"value": "spouse", "label": "💑 Spouse/Partner"},
            {"value": "parent", "label": "👨‍👩‍👧‍👦 Parent"},
            {"value": "child", "label": "👶 Child"},
            {"value": "sibling", "label": "👫 Sibling"},
            {"value": "friend", "label": "👥 Friend"},
            {"value": "colleague", "label": "💼 Colleague"},
            {"value": "other", "label": "🤝 Other"}
        ],
        help_text="Your relationship to this person",
        icon="people"
    )

    phone: str = FormField(
        title="Phone Number",
        input_type="tel",
        placeholder="+1 (555) 123-4567",
        help_text="Primary phone number for this contact",
        icon="telephone",
        min_length=10,
        max_length=20
    )

    email: Optional[EmailStr] = FormField(
        None,
        title="Email Address",
        input_type="email",
        placeholder="contact@example.com",
        help_text="Email address (optional)",
        icon="envelope"
    )

    available_24_7: bool = FormField(
        False,
        title="Available 24/7",
        input_type="checkbox",
        help_text="Can this person be contacted at any time?",
        icon="clock"
    )

class CompleteShowcaseForm(FormModel):
    """
    Complete showcase form demonstrating all Pydantic SchemaForms capabilities:
    - All input types (text, email, number, select, checkbox, date, color, etc.)
    - Collapsible list layouts with cards
    - Dynamic titles and field validation
    - Icons and help text
    - Multiple layout options
    """

    # ======== PERSONAL INFORMATION SECTION ========
    first_name: str = FormField(
        title="First Name",
        input_type="text",
        placeholder="Enter your first name",
        help_text="Your given name as it appears on official documents",
        icon="person",
        min_length=2,
        max_length=50
    )

    last_name: str = FormField(
        title="Last Name",
        input_type="text",
        placeholder="Enter your last name",
        help_text="Your family name or surname",
        icon="person",
        min_length=2,
        max_length=50
    )

    email: EmailStr = FormField(
        title="Email Address",
        input_type="email",
        placeholder="your.email@example.com",
        help_text="We'll use this to contact you about your registration",
        icon="envelope"
    )

    phone: Optional[str] = FormField(
        None,
        title="Phone Number",
        input_type="tel",
        placeholder="+1 (555) 123-4567",
        help_text="Include country code for international numbers",
        icon="telephone",
        pattern=r"^[\+]?[1-9][\d]{0,15}$"
    )

    birth_date: Optional[date] = FormField(
        None,
        title="Date of Birth",
        input_type="date",
        help_text="Used to verify age requirements (optional)",
        icon="calendar-date"
    )

    age: Optional[int] = FormField(
        None,
        title="Age",
        input_type="number",
        placeholder="25",
        help_text="Your current age in years",
        icon="hash",
        min_value=13,
        max_value=120
    )

    # ======== PREFERENCES SECTION ========
    favorite_color: Optional[str] = FormField(
        "#3498db",
        title="Favorite Color",
        input_type="color",
        help_text="Pick your favorite color",
        icon="palette"
    )

    experience_level: str = FormField(
        title="Experience Level",
        input_type="select",
        options=[
            {"value": "beginner", "label": "🌱 Beginner (0-1 years)"},
            {"value": "intermediate", "label": "🚀 Intermediate (2-5 years)"},
            {"value": "advanced", "label": "🎯 Advanced (5-10 years)"},
            {"value": "expert", "label": "🏆 Expert (10+ years)"}
        ],
        help_text="Select your experience level",
        icon="trophy"
    )

    newsletter_subscription: bool = FormField(
        True,
        title="Subscribe to Newsletter",
        input_type="checkbox",
        help_text="Receive updates and news about our services",
        icon="mailbox"
    )

    rating: Optional[int] = FormField(
        None,
        title="Rate Your Interest (1-10)",
        input_type="range",
        help_text="How interested are you in our services?",
        icon="star",
        min_value=1,
        max_value=10
    )

    # ======== ADDRESS INFORMATION ========
    address: Optional[str] = FormField(
        None,
        title="Street Address",
        input_type="textarea",
        placeholder="123 Main Street\nApt 4B",
        help_text="Your full mailing address (optional)",
        icon="house",
        max_length=500
    )

    country: Optional[Country] = FormField(
        None,
        title="Country",
        input_type="select",
        options=[
            {"value": "US", "label": "🇺🇸 United States"},
            {"value": "CA", "label": "🇨🇦 Canada"},
            {"value": "UK", "label": "🇬🇧 United Kingdom"},
            {"value": "DE", "label": "🇩🇪 Germany"},
            {"value": "FR", "label": "🇫🇷 France"},
            {"value": "AU", "label": "🇦🇺 Australia"},
            {"value": "OTHER", "label": "🌍 Other"}
        ],
        help_text="Select your country of residence",
        icon="globe"
    )

    # ======== PETS SECTION (ENHANCED LIST) ========
    pets: List[PetModel] = FormField(
        default_factory=list,
        title="Your Pets",
        input_type="model_list",
        help_text="Tell us about each of your beloved pets",
        icon="heart-fill",
        min_length=0,
        max_length=5,
        model_class=PetModel,
        add_button_text="🐾 Add Another Pet",
        remove_button_text="Remove Pet",
        collapsible_items=True,
        items_expanded=False,  # Start collapsed to showcase feature
        item_title_template="🐾 {name} the {species}",  # Dynamic titles with emojis
        section_design={
            "section_title": "Pet Registry",
            "section_description": "Register each of your pets with detailed information for our records",
            "icon": "bi bi-heart-fill",
            "collapsible": True,
            "collapsed": False
        }
    )

    # ======== EMERGENCY CONTACTS (ANOTHER LIST) ========
    emergency_contacts: List[EmergencyContactModel] = FormField(
        default_factory=list,
        title="Emergency Contacts",
        input_type="model_list",
        help_text="Add people we can contact in case of emergency",
        icon="person-exclamation",
        min_length=1,
        max_length=3,
        model_class=EmergencyContactModel,
        add_button_text="➕ Add Emergency Contact",
        remove_button_text="Remove Contact",
        collapsible_items=True,
        items_expanded=True,  # Start expanded for required items
        item_title_template="📞 {name} ({relationship})",
        section_design={
            "section_title": "Emergency Contacts",
            "section_description": "At least one emergency contact is required",
            "icon": "bi bi-shield-exclamation",
            "collapsible": False,  # Don't allow collapsing required section
            "collapsed": False
        }
    )

    # ======== ADDITIONAL PREFERENCES ========
    special_requests: Optional[str] = FormField(
        None,
        title="Special Requests or Comments",
        input_type="textarea",
        placeholder="Any special requests, dietary restrictions, accessibility needs, or additional comments...",
        help_text="Let us know about any special accommodations you need",
        icon="chat-dots",
        max_length=1000
    )

    terms_accepted: bool = FormField(
        False,
        title="I accept the Terms and Conditions",
        input_type="checkbox",
        help_text="You must accept the terms to proceed",
        icon="check-square"
    )

    @field_validator('terms_accepted')
    @classmethod
    def validate_terms(cls, v):
        if not v:
            raise ValueError('You must accept the terms and conditions')
        return v


# === ADDITIONAL MODELS ===

    email_field: EmailStr = FormField(
        title="Email Field",
        input_type="email",
        placeholder="user@example.com",
        help_text="Must be a valid email address",
        icon="at"
    )

    password_field: str = FormField(
        title="Password Field",
        input_type="password",
        placeholder="Enter secure password",
        help_text="At least 8 characters with mixed case",
        icon="shield-lock",
        min_length=8
    )

    search_field: str = FormField(
        title="Search Field",
        input_type="search",
        placeholder="Search for something...",
        help_text="Search input with special styling",
        icon="search"
    )

    url_field: str = FormField(
        title="URL Field",
        input_type="url",
        placeholder="https://example.com",
        help_text="Must be a valid URL",
        icon="link-45deg"
    )

    tel_field: str = FormField(
        title="Telephone Field",
        input_type="tel",
        placeholder="+1-555-123-4567",
        help_text="Phone number input",
        icon="telephone"
    )

    textarea_field: str = FormField(
        title="Text Area",
        input_type="textarea",
        placeholder="Enter multiple lines of text...",
        help_text="Multi-line text input",
        icon="textarea-resize",
        min_length=10,
        max_length=500
    )

    # === NUMERIC INPUTS ===
    number_field: int = FormField(
        title="Number Input",
        input_type="number",
        placeholder="42",
        help_text="Integer number input",
        icon="123",
        min_value=0,
        max_value=1000
    )

    float_field: float = FormField(
        title="Decimal Number",
        input_type="number",
        placeholder="3.14159",
        help_text="Decimal number input",
        icon="calculator",
        min_value=0.0,
        max_value=999.99
    )

    range_field: int = FormField(
        25,
        title="Range Slider",
        input_type="range",
        help_text="Slide to select value",
        icon="sliders",
        min_value=0,
        max_value=100
    )

    # === SELECTION INPUTS ===
    select_field: str = FormField(
        title="Select Dropdown",
        input_type="select",
        options=["Option 1", "Option 2", "Option 3", "Option 4"],
        help_text="Choose one option from dropdown",
        icon="list"
    )

    country_field: Country = FormField(
        Country.US,
        title="Country Selection",
        input_type="select",
        options=[c.value for c in Country],
        help_text="Select your country",
        icon="globe"
    )

    radio_field: str = FormField(
        "medium",
        title="Radio Button Group",
        input_type="radio",
        options=["small", "medium", "large", "extra-large"],
        help_text="Select one option",
        icon="ui-radios"
    )

    multiselect_field: List[str] = FormField(
        [],
        title="Multiple Selection",
        input_type="select",
        options=["JavaScript", "Python", "Java", "C++", "Go", "Rust"],
        help_text="Select multiple programming languages",
        icon="list-check"
    )

    # === BOOLEAN INPUTS ===
    checkbox_field: bool = FormField(
        False,
        title="Checkbox Input",
        input_type="checkbox",
        help_text="Check this box to agree",
        icon="check-square"
    )

    switch_field: bool = FormField(
        True,
        title="Switch Toggle",
        input_type="checkbox",
        help_text="Toggle this switch",
        icon="toggle-on"
    )

    # === DATE/TIME INPUTS ===
    date_field: date = FormField(
        title="Date Input",
        input_type="date",
        help_text="Select a date",
        icon="calendar-date"
    )

    time_field: str = FormField(
        title="Time Input",
        input_type="time",
        help_text="Select a time",
        icon="clock"
    )

    datetime_field: datetime = FormField(
        title="Date & Time",
        input_type="datetime-local",
        help_text="Select date and time",
        icon="calendar-event"
    )

    # === SPECIALIZED INPUTS ===
    color_field: str = FormField(
        "#3498db",
        title="Color Picker",
        input_type="color",
        help_text="Choose your favorite color",
        icon="palette"
    )

    file_field: str = FormField(
        title="File Upload",
        input_type="file",
        help_text="Upload a file (max 10MB)",
        icon="cloud-upload"
    )

    hidden_field: str = FormField(
        "hidden_value",
        title="Hidden Field",
        input_type="hidden",
        help_text="This field is hidden from users"
    )

    # === USER PROFILE SECTION ===
    role: UserRole = FormField(
        UserRole.USER,
        title="User Role",
        input_type="select",
        options=[r.value for r in UserRole],
        help_text="Select your role",
        icon="person-badge"
    )

    bio: Optional[str] = FormField(
        None,
        title="Biography",
        input_type="textarea",
        placeholder="Tell us about yourself...",
        help_text="Optional personal biography",
        icon="person-lines-fill",
        max_length=1000
    )

    newsletter: bool = FormField(
        False,
        title="Newsletter Subscription",
        input_type="checkbox",
        help_text="Receive our weekly newsletter",
        icon="envelope-heart"
    )

    notifications: bool = FormField(
        True,
        title="Push Notifications",
        input_type="checkbox",
        help_text="Receive push notifications",
        icon="bell"
    )

    @field_validator("password_field")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_nested_form_data(form_data):
    """
    Parse nested form data from flat keys to nested structure.

    Converts keys like 'pets[0].name' to nested dict structure:
    {'pets': [{'name': 'value'}]}

    Args:
        form_data: Dictionary with flat keys from HTML form submission

    Returns:
        Dictionary with proper nested structure
    """


    result = {}
    array_data = defaultdict(lambda: defaultdict(dict))

    for key, value in form_data.items():
        # Handle array notation like pets[0].name
        array_match = re.match(r'^(\w+)\[(\d+)\]\.(\w+)$', key)
        if array_match:
            array_name, index, field_name = array_match.groups()
            index = int(index)

            # Convert string values to appropriate types
            converted_value = convert_form_value(value)
            array_data[array_name][index][field_name] = converted_value
        else:
            # Regular field
            result[key] = convert_form_value(value)

    # Convert array data to proper list format
    for array_name, indexed_items in array_data.items():
        # Sort by index and create list
        items_list = []
        for i in sorted(indexed_items.keys()):
            items_list.append(indexed_items[i])
        result[array_name] = items_list

    return result


def convert_form_value(value):
    """
    Convert form string values to appropriate Python types.

    Args:
        value: String value from form

    Returns:
        Converted value (bool, int, float, or string)
    """
    if isinstance(value, str):
        # Handle boolean values
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        elif value.lower() in ('on', 'yes', '1'):
            return True
        elif value.lower() in ('off', 'no', '0'):
            return False

        # Don't convert numeric values automatically - let Pydantic handle type conversion
        # This prevents issues with password fields that contain only digits
        # and other string fields that should remain as strings

    # Return as-is for strings, empty values, etc.
    return value


def handle_form_submission(form_class, form_data, success_message="Form submitted successfully!"):
    """Handle form submission with validation and error handling."""
    try:


        # Parse nested form data (handles pets[0].name -> pets: [{name: ...}])
        parsed_data = parse_nested_form_data(form_data)

        # Validate the form data using Pydantic
        result = validate_form_data(form_class, parsed_data)

        if result.is_valid:
            # Return success response
            return {
                'success': True,
                'message': success_message,
                'data': result.data
            }
        else:
            # Return validation errors
            return {
                'success': False,
                'errors': result.errors
            }
    except Exception as e:
        # Return unexpected errors
        return {
            'success': False,
            'errors': {'form': str(e)}
        }

# Export all the models
__all__ = [
    # Enums
    'Priority', 'UserRole', 'Country',
    # Form Models
    'PetModel', 'EmergencyContactModel', 'MinimalLoginForm', 'UserRegistrationForm',
    'PetOwnerForm', 'PetRegistrationForm', 'MediumContactForm', 'CompleteShowcaseForm',
    # Layout Demonstration Forms
    'TaskItem', 'PersonalInfoForm', 'ContactInfoForm', 'PreferencesForm', 'TaskListForm',
    'LayoutDemonstrationForm',
    # Layout Classes
    'VerticalFormLayout', 'HorizontalFormLayout', 'TabbedFormLayout', 'ListFormLayout',
    # Helper Functions
    'handle_form_submission', 'parse_nested_form_data', 'convert_form_value'
]


# ============================================================================
# LAYOUT DEMONSTRATION FORMS
# ============================================================================

class TaskItem(FormModel):
    """Individual task item for list layout demonstration."""
    task_name: str = FormField(
        title="Task Description",
        input_type="text",
        placeholder="Enter task description...",
        help_text="What needs to be done?",
        icon="check-square",
        min_length=1,
        max_length=100
    )

    priority: str = FormField(
        "medium",
        title="Priority",
        input_type="select",
        options=[
            {"value": "low", "label": "🟢 Low"},
            {"value": "medium", "label": "🟡 Medium"},
            {"value": "high", "label": "🟠 High"},
            {"value": "urgent", "label": "🔴 Urgent"}
        ],
        help_text="How important is this task?",
        icon="exclamation-triangle"
    )

    due_date: Optional[date] = FormField(
        None,
        title="Due Date",
        input_type="date",
        help_text="When should this be completed? (optional)",
        icon="calendar-date"
    )

    completed: bool = FormField(
        False,
        title="Completed",
        input_type="checkbox",
        help_text="Is this task done?",
        icon="check"
    )


class PersonalInfoForm(FormModel):
    """Personal information form for vertical layout demonstration."""

    first_name: str = FormField(
        title="First Name",
        input_type="text",
        placeholder="Enter your first name",
        help_text="Your given name",
        icon="person",
        min_length=2,
        max_length=50
    )

    last_name: str = FormField(
        title="Last Name",
        input_type="text",
        placeholder="Enter your last name",
        help_text="Your family name",
        icon="person",
        min_length=2,
        max_length=50
    )

    email: EmailStr = FormField(
        title="Email Address",
        input_type="email",
        placeholder="your.email@example.com",
        help_text="Your email address",
        icon="envelope"
    )

    birth_date: Optional[date] = FormField(
        None,
        title="Date of Birth",
        input_type="date",
        help_text="Your birth date (optional)",
        icon="calendar-date"
    )


class ContactInfoForm(FormModel):
    """Contact information form for horizontal layout demonstration."""

    phone: Optional[str] = FormField(
        None,
        title="Phone Number",
        input_type="tel",
        placeholder="+1 (555) 123-4567",
        help_text="Your contact phone number",
        icon="telephone",
        max_length=20
    )

    address: str = FormField(
        title="Street Address",
        input_type="text",
        placeholder="123 Main Street",
        help_text="Your street address",
        icon="house",
        max_length=200
    )

    city: str = FormField(
        title="City",
        input_type="text",
        placeholder="Your city",
        help_text="City where you live",
        icon="building",
        max_length=100
    )

    postal_code: Optional[str] = FormField(
        None,
        title="Postal Code",
        input_type="text",
        placeholder="12345",
        help_text="ZIP or postal code",
        icon="mailbox",
        max_length=10
    )


class PreferencesForm(FormModel):
    """Preferences form for tabbed layout demonstration."""

    notification_email: bool = FormField(
        True,
        title="Email Notifications",
        input_type="checkbox",
        help_text="Receive notifications via email",
        icon="envelope"
    )

    notification_sms: bool = FormField(
        False,
        title="SMS Notifications",
        input_type="checkbox",
        help_text="Receive notifications via SMS",
        icon="phone"
    )

    theme: str = FormField(
        "light",
        title="UI Theme",
        input_type="select",
        options=[
            {"value": "light", "label": "☀️ Light Theme"},
            {"value": "dark", "label": "🌙 Dark Theme"},
            {"value": "auto", "label": "🔄 Auto (System)"}
        ],
        help_text="Choose your preferred theme",
        icon="palette"
    )

    language: str = FormField(
        "en",
        title="Language",
        input_type="select",
        options=[
            {"value": "en", "label": "🇺🇸 English"},
            {"value": "es", "label": "🇪🇸 Spanish"},
            {"value": "fr", "label": "🇫🇷 French"},
            {"value": "de", "label": "🇩🇪 German"}
        ],
        help_text="Select your preferred language",
        icon="globe"
    )


class TaskListForm(FormModel):
    """Task management form for list layout demonstration."""

    project_name: str = FormField(
        title="Project Name",
        input_type="text",
        placeholder="Enter project name",
        help_text="Name of the project or task collection",
        icon="folder",
        min_length=2,
        max_length=100,
    )

    tasks: List[TaskItem] = FormField(
        default_factory=list,
        title="Task List",
        input_type="model_list",
        help_text="Manage your tasks (dynamic list demonstration)",
        icon="list-task",
        min_length=1,
        max_length=10,
        model_class=TaskItem,
        add_button_text="Add Task",
        remove_button_text="Remove Task",
        collapsible_items=True,
        items_expanded_by_default=True
    )

    @field_validator('tasks')
    @classmethod
    def validate_tasks(cls, v):
        if len(v) < 1:
            raise ValueError('At least one task is required')
        if len(v) > 10:
            raise ValueError('Maximum 10 tasks allowed')
        return v




# ============================================================================
# LAYOUT CLASSES
# ============================================================================

class VerticalFormLayout(VerticalLayout):
    """Vertical layout - default stacked form layout."""
    form = PersonalInfoForm

class HorizontalFormLayout(HorizontalLayout):
    """Horizontal layout - side-by-side form arrangement."""
    form = ContactInfoForm

class TabbedFormLayout(TabbedLayout):
    """Tabbed layout - preferences organized in tabs."""
    # Split preferences form into logical tabs for demonstration
    notifications = PreferencesForm
    appearance = PreferencesForm

class ListFormLayout(VerticalLayout):
    """List layout - form with dynamic task list."""
    form = TaskListForm

class LayoutDemonstrationForm(FormModel):
    """
    Create a tabbed layout using VerticalLayout, HorizontalLayout, TabbedLayout, and ListLayout as the tabs.

    This demonstrates how to use layout classes as field types in a Pydantic form.
    Each field represents a different layout type that can be rendered as a tab.
    """
    vertical_tab: VerticalFormLayout = FormField(
        VerticalFormLayout(),
        title="Personal Info",
        input_type="layout",
        help_text="Vertical layout demonstration"
    )

    horizontal_tab: HorizontalFormLayout = FormField(
        HorizontalFormLayout(),
        title="Contact Info",
        input_type="layout",
        help_text="Horizontal layout demonstration"
    )

    tabbed_tab: TabbedFormLayout = FormField(
        TabbedFormLayout(),
        title="Preferences",
        input_type="layout",
        help_text="Tabbed layout demonstration"
    )

    list_tab: ListFormLayout = FormField(
        ListFormLayout(),
        title="Task List",
        input_type="layout",
        help_text="List layout demonstration"
    )
