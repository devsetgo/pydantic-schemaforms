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
# ORGANIZATION NESTED FORM MODELS (5 LEVELS)
# ============================================================================

class Certification(FormModel):
    """Level 5: Individual certification credential."""

    name: str = FormField(
        title="Certification Name",
        input_type="text",
        placeholder="e.g., AWS Solutions Architect",
        help_text="Name of the certification",
        icon="award",
        max_length=100
    )

    issuer: str = FormField(
        title="Issuing Organization",
        input_type="text",
        placeholder="e.g., Amazon Web Services",
        help_text="Organization that issued the certification",
        icon="building",
        max_length=100
    )

    issue_date: date = FormField(
        title="Issue Date",
        input_type="date",
        help_text="When was this certification issued?"
    )

    expiry_date: Optional[date] = FormField(
        None,
        title="Expiry Date",
        input_type="date",
        help_text="When does this certification expire? (Leave empty if no expiry)"
    )

    credential_id: Optional[str] = FormField(
        None,
        title="Credential ID",
        input_type="text",
        placeholder="Optional credential identifier",
        help_text="Unique ID for credential verification",
        max_length=100
    )

    credential_url: Optional[str] = FormField(
        None,
        title="Credential URL",
        input_type="text",
        placeholder="https://...",
        help_text="Link to verify the credential",
        max_length=500
    )


class Subtask(FormModel):
    """Level 5: Individual subtask within a task."""

    title: str = FormField(
        title="Subtask Title",
        input_type="text",
        placeholder="Brief description of the subtask",
        help_text="What is this subtask about?",
        icon="list-check",
        max_length=200
    )

    description: Optional[str] = FormField(
        None,
        title="Description",
        input_type="textarea",
        placeholder="Detailed description of the subtask",
        help_text="Additional details about this subtask",
        max_length=1000
    )

    assigned_to: str = FormField(
        title="Assigned To",
        input_type="text",
        placeholder="Team member name",
        help_text="Who is responsible for this subtask?",
        icon="person",
        max_length=100
    )

    estimated_hours: float = FormField(
        1.0,
        title="Estimated Hours",
        input_type="number",
        help_text="Estimated time to complete",
        icon="clock",
        min_value=0.5,
        max_value=100
    )

    status: str = FormField(
        "pending",
        title="Status",
        input_type="select",
        options=[
            {"value": "pending", "label": "⏳ Pending"},
            {"value": "in_progress", "label": "🔄 In Progress"},
            {"value": "completed", "label": "✅ Completed"},
            {"value": "blocked", "label": "🚫 Blocked"}
        ],
        help_text="Current status of the subtask"
    )


class TeamMember(FormModel):
    """Level 4: Team member with certifications (Level 5)."""

    name: str = FormField(
        title="Member Name",
        input_type="text",
        placeholder="Enter full name",
        help_text="Full name of the team member",
        icon="person",
        min_length=2,
        max_length=100
    )

    email: EmailStr = FormField(
        title="Email Address",
        input_type="email",
        placeholder="member@company.com",
        help_text="Contact email address"
    )

    role: str = FormField(
        title="Role",
        input_type="text",
        placeholder="e.g., Senior Developer",
        help_text="Job title or role",
        icon="briefcase",
        max_length=100
    )

    hire_date: date = FormField(
        title="Hire Date",
        input_type="date",
        help_text="When did this person join?"
    )

    experience_years: int = FormField(
        0,
        title="Years of Experience",
        input_type="number",
        help_text="Total professional experience in years",
        icon="hourglass-split",
        min_value=0,
        max_value=70
    )

    manager: Optional[str] = FormField(
        None,
        title="Manager Name",
        input_type="text",
        placeholder="Direct manager name",
        help_text="Who supervises this team member?",
        max_length=100
    )

    certifications: List[Certification] = FormField(
        default_factory=list,
        title="Certifications",
        input_type="model_list",
        help_text="Professional certifications and credentials",
        icon="award",
        min_length=0,
        max_length=20,
        model_class=Certification,
        add_button_text="➕ Add Certification",
        remove_button_text="Remove",
        collapsible_items=True,
        items_expanded=False,
        item_title_template="{name} - {issuer}",
        section_design={
            "section_title": "Professional Certifications",
            "section_description": "Add credentials and certifications",
            "icon": "bi bi-award",
            "collapsible": True,
            "collapsed": False
        }
    )


class Task(FormModel):
    """Level 4: Project task with subtasks (Level 5)."""

    title: str = FormField(
        title="Task Title",
        input_type="text",
        placeholder="Brief task name",
        help_text="What is this task?",
        icon="bookmark",
        min_length=3,
        max_length=200
    )

    description: str = FormField(
        title="Task Description",
        input_type="textarea",
        placeholder="Detailed description of the task",
        help_text="Full description of what needs to be done",
        max_length=2000
    )

    priority: str = FormField(
        "medium",
        title="Priority Level",
        input_type="select",
        options=[
            {"value": "low", "label": "🟢 Low"},
            {"value": "medium", "label": "🟡 Medium"},
            {"value": "high", "label": "🔴 High"},
            {"value": "critical", "label": "⛔ Critical"}
        ],
        help_text="Task priority level",
        icon="exclamation-circle"
    )

    status: str = FormField(
        "planning",
        title="Task Status",
        input_type="select",
        options=[
            {"value": "planning", "label": "📋 Planning"},
            {"value": "in_progress", "label": "🔄 In Progress"},
            {"value": "in_review", "label": "👀 In Review"},
            {"value": "completed", "label": "✅ Completed"},
            {"value": "cancelled", "label": "❌ Cancelled"}
        ],
        help_text="Current task status"
    )

    start_date: date = FormField(
        title="Start Date",
        input_type="date",
        help_text="When should this task start?"
    )

    due_date: date = FormField(
        title="Due Date",
        input_type="date",
        help_text="When is this task due?"
    )

    assigned_to: Optional[str] = FormField(
        None,
        title="Assigned To",
        input_type="text",
        placeholder="Team member name",
        help_text="Who is responsible for this task?",
        max_length=100
    )

    estimated_hours: float = FormField(
        8.0,
        title="Estimated Hours",
        input_type="number",
        help_text="Estimated time to complete (in hours)",
        icon="clock",
        min_value=0.5,
        max_value=1000
    )

    subtasks: List[Subtask] = FormField(
        default_factory=list,
        title="Subtasks",
        input_type="model_list",
        help_text="Break down this task into smaller subtasks",
        icon="list-check",
        min_length=0,
        max_length=50,
        model_class=Subtask,
        add_button_text="➕ Add Subtask",
        remove_button_text="Remove Subtask",
        collapsible_items=True,
        items_expanded=False,
        item_title_template="🔹 {title}",
        section_design={
            "section_title": "Task Breakdown",
            "section_description": "Organize this task into smaller, manageable subtasks",
            "icon": "bi bi-list-check",
            "collapsible": True,
            "collapsed": False
        }
    )


class Team(FormModel):
    """Level 3: Team with members (Level 4) who have certifications (Level 5)."""

    name: str = FormField(
        title="Team Name",
        input_type="text",
        placeholder="e.g., Backend Team",
        help_text="Name of the team",
        icon="people",
        min_length=2,
        max_length=100
    )

    description: Optional[str] = FormField(
        None,
        title="Team Description",
        input_type="textarea",
        placeholder="What does this team do?",
        help_text="Brief description of the team's responsibilities",
        max_length=500
    )

    team_lead: str = FormField(
        title="Team Lead Name",
        input_type="text",
        placeholder="Name of the team lead",
        help_text="Who leads this team?",
        icon="star",
        max_length=100
    )

    formed_date: date = FormField(
        title="Formation Date",
        input_type="date",
        help_text="When was this team formed?"
    )

    members: List[TeamMember] = FormField(
        default_factory=list,
        title="Team Members",
        input_type="model_list",
        help_text="Add team members and their certifications",
        icon="people",
        min_length=1,
        max_length=100,
        model_class=TeamMember,
        add_button_text="👤 Add Team Member",
        remove_button_text="Remove Member",
        collapsible_items=True,
        items_expanded=False,
        item_title_template="👤 {name} - {role}",
        section_design={
            "section_title": "Team Members",
            "section_description": "Members of this team with their certifications and experience",
            "icon": "bi bi-people",
            "collapsible": True,
            "collapsed": False
        }
    )


class Project(FormModel):
    """Level 3: Project with tasks (Level 4) that have subtasks (Level 5)."""

    name: str = FormField(
        title="Project Name",
        input_type="text",
        placeholder="e.g., Mobile App Redesign",
        help_text="Name of the project",
        icon="kanban",
        min_length=3,
        max_length=200
    )

    description: str = FormField(
        title="Project Description",
        input_type="textarea",
        placeholder="Detailed description of the project",
        help_text="What is this project about?",
        max_length=2000
    )

    status: str = FormField(
        "planning",
        title="Project Status",
        input_type="select",
        options=[
            {"value": "planning", "label": "📋 Planning"},
            {"value": "in_progress", "label": "🚀 In Progress"},
            {"value": "on_hold", "label": "⏸️ On Hold"},
            {"value": "completed", "label": "✅ Completed"},
            {"value": "archived", "label": "📦 Archived"}
        ],
        help_text="Current project status",
        icon="flag"
    )

    start_date: date = FormField(
        title="Project Start Date",
        input_type="date",
        help_text="When does this project start?"
    )

    target_end_date: date = FormField(
        title="Target End Date",
        input_type="date",
        help_text="When should this project be completed?"
    )

    budget: float = FormField(
        0.0,
        title="Budget ($)",
        input_type="number",
        help_text="Project budget in USD",
        icon="cash-coin",
        min_value=0
    )

    project_manager: str = FormField(
        title="Project Manager",
        input_type="text",
        placeholder="PM name",
        help_text="Who is managing this project?",
        icon="person-badge",
        max_length=100
    )

    tasks: List[Task] = FormField(
        default_factory=list,
        title="Project Tasks",
        input_type="model_list",
        help_text="Add tasks with subtasks to organize project work",
        icon="list-check",
        min_length=1,
        max_length=200,
        model_class=Task,
        add_button_text="📝 Add Task",
        remove_button_text="Remove Task",
        collapsible_items=True,
        items_expanded=False,
        item_title_template="📋 {title}",
        section_design={
            "section_title": "Project Tasks",
            "section_description": "Organize project work into tasks and subtasks",
            "icon": "bi bi-list-task",
            "collapsible": True,
            "collapsed": False
        }
    )


class Department(FormModel):
    """Level 2: Department with teams (Level 3) and projects (Level 3)."""

    name: str = FormField(
        title="Department Name",
        input_type="text",
        placeholder="e.g., Engineering, Sales",
        help_text="Name of the department",
        icon="building",
        min_length=2,
        max_length=100
    )

    description: Optional[str] = FormField(
        None,
        title="Department Description",
        input_type="textarea",
        placeholder="What does this department do?",
        help_text="Description of department responsibilities",
        max_length=1000
    )

    department_head: str = FormField(
        title="Department Head",
        input_type="text",
        placeholder="Head of department name",
        help_text="Who leads this department?",
        icon="crown",
        max_length=100
    )

    head_email: EmailStr = FormField(
        title="Department Head Email",
        input_type="email",
        placeholder="head@company.com",
        help_text="Contact email for the department head"
    )

    established_date: date = FormField(
        title="Established Date",
        input_type="date",
        help_text="When was this department established?"
    )

    budget: float = FormField(
        0.0,
        title="Annual Budget ($)",
        input_type="number",
        help_text="Department annual budget in USD",
        icon="cash-coin",
        min_value=0
    )

    teams: List[Team] = FormField(
        default_factory=list,
        title="Teams",
        input_type="model_list",
        help_text="Teams within this department and their members",
        icon="people",
        min_length=1,
        max_length=50,
        model_class=Team,
        add_button_text="👥 Add Team",
        remove_button_text="Remove Team",
        collapsible_items=True,
        items_expanded=False,
        item_title_template="👥 {name} (Lead: {team_lead})",
        section_design={
            "section_title": "Department Teams",
            "section_description": "Organize teams with members and their certifications",
            "icon": "bi bi-diagram-2",
            "collapsible": True,
            "collapsed": False
        }
    )

    projects: List[Project] = FormField(
        default_factory=list,
        title="Active Projects",
        input_type="model_list",
        help_text="Projects managed by this department",
        icon="kanban",
        min_length=0,
        max_length=100,
        model_class=Project,
        add_button_text="🚀 Add Project",
        remove_button_text="Remove Project",
        collapsible_items=True,
        items_expanded=False,
        item_title_template="🚀 {name}",
        section_design={
            "section_title": "Department Projects",
            "section_description": "Projects in progress with tasks and subtasks",
            "icon": "bi bi-kanban",
            "collapsible": True,
            "collapsed": False
        }
    )


class CompanyOrganizationForm(FormModel):
    """
    Root company structure with 5 levels of nesting.

    This model demonstrates how SchemaForms can render deeply nested data by
    composing `model_list` fields across multiple `FormModel` classes:

    Company -> Department -> Team -> TeamMember -> Certification
                        -> Project -> Task -> Subtask
    """

    company_name: str = FormField(
        title="Company Name",
        input_type="text",
        placeholder="Enter company name",
        help_text="Legal name of the company",
        icon="building",
        min_length=2,
        max_length=200
    )

    company_code: str = FormField(
        title="Company Code",
        input_type="text",
        placeholder="e.g., ACME-2024",
        help_text="Unique identifier for this company",
        icon="code",
        min_length=2,
        max_length=50
    )

    headquarters_address: str = FormField(
        title="Headquarters Address",
        input_type="textarea",
        placeholder="Full address of headquarters",
        help_text="Main office address",
        icon="map-marker",
        max_length=500
    )

    ceo_name: str = FormField(
        title="CEO Name",
        input_type="text",
        placeholder="Name of the CEO",
        help_text="Chief Executive Officer",
        icon="star",
        max_length=100
    )

    ceo_email: EmailStr = FormField(
        title="CEO Email",
        input_type="email",
        placeholder="ceo@company.com",
        help_text="Email address of the CEO"
    )

    founded_date: date = FormField(
        title="Founded Date",
        input_type="date",
        help_text="When was the company founded?"
    )

    employee_count: int = FormField(
        0,
        title="Total Employees",
        input_type="number",
        help_text="Total number of employees",
        icon="people",
        min_value=1,
        max_value=1000000
    )

    annual_revenue: float = FormField(
        0.0,
        title="Annual Revenue ($)",
        input_type="number",
        help_text="Company annual revenue in USD",
        icon="cash-coin",
        min_value=0
    )

    website: Optional[str] = FormField(
        None,
        title="Company Website",
        input_type="text",
        placeholder="https://www.example.com",
        help_text="Company website URL",
        icon="globe",
        max_length=500
    )

    departments: List[Department] = FormField(
        default_factory=list,
        title="Company Departments",
        input_type="model_list",
        help_text="Organize departments with teams, members, and projects",
        icon="diagram-2",
        min_length=1,
        max_length=500,
        model_class=Department,
        add_button_text="🏢 Add Department",
        remove_button_text="Remove Department",
        collapsible_items=True,
        items_expanded=False,
        item_title_template="🏢 {name} (Head: {department_head})",
        section_design={
            "section_title": "Organizational Structure",
            "section_description": "Complete company hierarchy with departments, teams, members, and projects",
            "icon": "bi bi-diagram-2",
            "collapsible": True,
            "collapsed": False
        }
    )

    @field_validator('company_code')
    @classmethod
    def validate_code(cls, v):
        """Normalize and validate company code input for demonstration purposes."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Company code can only contain letters, numbers, hyphens, and underscores")
        return v.upper()


def create_sample_nested_data() -> dict:
    """
    Create realistic seed data for the organization hierarchy example.

    The returned payload mirrors the exact shape expected by
    `CompanyOrganizationForm`, so it can be used to:
    - pre-fill example pages,
    - test nested rendering,
    - validate nested parsing/serialization behavior.
    """
    return {
        # Level 1: company root
        "company_name": "TechCorp International",
        "company_code": "TECH-2024",
        "headquarters_address": "123 Innovation Drive, San Francisco, CA 94105",
        "ceo_name": "Jane Smith",
        "ceo_email": "jane.smith@techcorp.com",
        "founded_date": "2010-01-15",
        "employee_count": 5000,
        "annual_revenue": 500000000.0,
        "website": "https://www.techcorp.com",
        "departments": [
            {
                # Level 2: departments
                "name": "Engineering",
                "description": "Software development and infrastructure",
                "department_head": "John Doe",
                "head_email": "john.doe@techcorp.com",
                "established_date": "2010-06-01",
                "budget": 50000000.0,
                "teams": [
                    {
                        # Level 3: teams
                        "name": "Backend Services",
                        "description": "API and database services",
                        "team_lead": "Alice Johnson",
                        "formed_date": "2015-03-01",
                        "members": [
                            {
                                # Level 4: team members
                                "name": "Bob Wilson",
                                "email": "bob.wilson@techcorp.com",
                                "role": "Senior Backend Developer",
                                "hire_date": "2016-01-15",
                                "experience_years": 12,
                                "manager": "Alice Johnson",
                                "certifications": [
                                    {
                                        # Level 5: leaf credentials
                                        "name": "AWS Solutions Architect Professional",
                                        "issuer": "Amazon Web Services",
                                        "issue_date": "2022-05-01",
                                        "expiry_date": "2025-05-01",
                                        "credential_id": "AWS-12345",
                                        "credential_url": "https://aws.amazon.com/verification/12345"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "projects": [
                    {
                        # Level 3 (parallel branch): projects with tasks/subtasks
                        "name": "Microservices Migration",
                        "description": "Migrate monolithic application to microservices architecture",
                        "status": "in_progress",
                        "start_date": "2024-01-01",
                        "target_end_date": "2024-12-31",
                        "budget": 2000000.0,
                        "project_manager": "Carol Lee",
                        "tasks": [
                            {
                                # Level 4: tasks
                                "title": "Refactor Auth Service",
                                "description": "Extract authentication into standalone microservice",
                                "priority": "high",
                                "status": "in_progress",
                                "start_date": "2024-02-01",
                                "due_date": "2024-03-31",
                                "assigned_to": "Bob Wilson",
                                "estimated_hours": 120.0,
                                "subtasks": [
                                    {
                                        # Level 5: subtasks
                                        "title": "Create service skeleton",
                                        "description": "Set up FastAPI project structure",
                                        "assigned_to": "Bob Wilson",
                                        "estimated_hours": 16.0,
                                        "status": "completed"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

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

    def tokenize_path(path: str):
        tokens = []
        for name_token, index_token in re.findall(r'([^.\[\]]+)|\[(\d+)\]', path):
            if name_token:
                tokens.append(name_token)
            elif index_token:
                tokens.append(int(index_token))
        return tokens

    def assign_nested(container, tokens, value):
        current = container
        for idx, token in enumerate(tokens):
            is_last = idx == len(tokens) - 1
            next_token = tokens[idx + 1] if not is_last else None

            if isinstance(token, str):
                if is_last:
                    current[token] = value
                    return

                if token not in current or current[token] is None:
                    current[token] = [] if isinstance(next_token, int) else {}
                current = current[token]
                continue

            # token is a list index
            while len(current) <= token:
                current.append(None)

            if is_last:
                current[token] = value
                return

            if current[token] is None:
                current[token] = [] if isinstance(next_token, int) else {}
            current = current[token]

    for key, value in form_data.items():
        converted_value = convert_form_value(value)
        tokens = tokenize_path(key)

        if not tokens:
            result[key] = converted_value
            continue

        if len(tokens) == 1 and isinstance(tokens[0], str):
            result[tokens[0]] = converted_value
            continue

        assign_nested(result, tokens, converted_value)

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
    'Certification', 'Subtask', 'TeamMember', 'Task', 'Team', 'Project', 'Department', 'CompanyOrganizationForm',
    # Layout Demonstration Forms
    'TaskItem', 'PersonalInfoForm', 'ContactInfoForm', 'PreferencesForm', 'TaskListForm',
    'LayoutDemonstrationForm',
    # Layout Classes
    'VerticalFormLayout', 'HorizontalFormLayout', 'TabbedFormLayout', 'ListFormLayout',
    # Helper Functions
    'handle_form_submission', 'parse_nested_form_data', 'convert_form_value', 'create_sample_nested_data'
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


class PreferencesTabLayout(VerticalLayout):
    """Vertical layout wrapper used inside the preferences TabbedLayout."""

    form = PreferencesForm


class TabbedFormLayout(TabbedLayout):
    """Tabbed layout - preferences organized in tabs."""

    def __init__(self, form_config=None):
        super().__init__(form_config=form_config)
        # Each tab must be a layout instance (BaseLayout/FormLayoutBase), not a FormModel class.
        self.notifications = PreferencesTabLayout()
        self.appearance = PreferencesTabLayout()

    def _get_layouts(self):
        # Keep ordering stable (and avoid scanning dir(self)).
        return [
            ("notifications", self.notifications),
            ("appearance", self.appearance),
        ]

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
        default_factory=VerticalFormLayout,
        title="Personal Info",
        input_type="layout",
        help_text="Vertical layout demonstration"
    )

    horizontal_tab: HorizontalFormLayout = FormField(
        default_factory=HorizontalFormLayout,
        title="Contact Info",
        input_type="layout",
        help_text="Horizontal layout demonstration"
    )

    tabbed_tab: TabbedFormLayout = FormField(
        default_factory=TabbedFormLayout,
        title="Preferences",
        input_type="layout",
        help_text="Tabbed layout demonstration"
    )

    list_tab: ListFormLayout = FormField(
        default_factory=ListFormLayout,
        title="Task List",
        input_type="layout",
        help_text="List layout demonstration"
    )
