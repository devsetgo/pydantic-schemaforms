"""
Shared form models for Pydantic SchemaForms examples.

This module contains all the form models used across different framework examples
(Flask, FastAPI, etc.) to demonstrate Pydantic SchemaForms capabilities.
"""

import os
import sys
from datetime import date, datetime, time
from enum import Enum
from typing import List, Literal, Optional

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import EmailStr, field_validator, model_validator

from pydantic_schemaforms import (
    CustomRule,
    DateRangeRule,
    EmailDeliverabilityRule,
    EmailRule,
    Field,
    FormField,
    FormModel,
    FormValidator,
    MaxLengthRule,
    MinLengthRule,
    NumericRangeRule,
    PhoneRule,
    RegexRule,
    RequiredRule,
)

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

# Demo-only secret for the CompleteShowcaseForm CAPTCHA field. A real app must
# use a properly generated, environment-supplied secret -- never hardcode one.
SHOWCASE_CAPTCHA_SECRET = 'demo-only-showcase-captcha-secret-do-not-use-in-production'


class Priority(str, Enum):
    """Priority levels for forms."""

    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'


class UserRole(str, Enum):
    """User roles."""

    USER = 'user'
    ADMIN = 'admin'
    MODERATOR = 'moderator'


class Country(str, Enum):
    """Countries for selection."""

    US = 'United States'
    CA = 'Canada'
    UK = 'United Kingdom'
    AU = 'Australia'
    DE = 'Germany'
    FR = 'France'
    JP = 'Japan'


# ============================================================================
# BASIC FORM MODELS
# ============================================================================


class PetModel(FormModel):
    """Enhanced pet information model showcasing various input types."""

    name: str = FormField(
        title="Pet's Name",
        input_type='text',
        placeholder="Enter your pet's name",
        help_text='The name of your pet',
        icon='heart',
        min_length=1,
        max_length=50,
    )

    species: str = FormField(
        title='Species',
        input_type='select',
        options=[
            {'value': 'dog', 'label': 'Dog 🐕'},
            {'value': 'cat', 'label': 'Cat 🐱'},
            {'value': 'bird', 'label': 'Bird 🐦'},
            {'value': 'fish', 'label': 'Fish 🐠'},
            {'value': 'rabbit', 'label': 'Rabbit 🐰'},
            {'value': 'hamster', 'label': 'Hamster 🐹'},
            {'value': 'reptile', 'label': 'Reptile 🦎'},
            {'value': 'other', 'label': 'Other 🐾'},
        ],
        help_text='What type of animal is your pet?',
        icon='collection',
    )

    age: Optional[int] = FormField(
        None,
        title='Age',
        input_type='number',
        placeholder="Pet's age in years",
        help_text='How old is your pet? (optional)',
        icon='calendar',
        min_value=0,
        max_value=50,
    )

    weight: Optional[float] = FormField(
        None,
        title='Weight (lbs)',
        input_type='number',
        placeholder="Pet's weight",
        help_text='Weight in pounds (optional - enter 0.01 for tiny pets like birds)',
        icon='speedometer2',
        min_value=0.01,
        max_value=500.0,
    )

    is_vaccinated: bool = FormField(
        False,
        title='Vaccinated',
        input_type='checkbox',
        help_text='Is your pet up to date with vaccinations?',
        icon='shield-check',
    )

    microchipped: bool = FormField(
        False,
        title='Microchipped',
        input_type='checkbox',
        help_text='Does your pet have a microchip?',
        icon='cpu',
    )

    breed: Optional[str] = FormField(
        None,
        title='Breed',
        input_type='text',
        placeholder='e.g., Golden Retriever, Persian Cat',
        help_text='Specific breed of your pet (optional)',
        icon='award',
        max_length=100,
    )

    color: Optional[str] = FormField(
        None,
        title='Primary Color',
        input_type='color',
        help_text='Primary color of your pet (optional)',
        icon='palette',
    )

    last_vet_visit: Optional[date] = FormField(
        None,
        title='Last Vet Visit',
        input_type='date',
        help_text='When was the last veterinary checkup? (optional)',
        icon='calendar-date',
    )

    special_needs: Optional[str] = FormField(
        None,
        title='Special Needs',
        input_type='textarea',
        placeholder='Any special care requirements, medications, allergies, etc.',
        help_text='Describe any special care requirements (optional)',
        icon='heart-pulse',
        max_length=500,
    )


class MinimalLoginForm(FormModel):
    """Minimal form example - Simple login form."""

    username: str = FormField(
        title='Username',
        input_type='text',
        placeholder='Enter your username',
        help_text='Your username or email address',
        icon='person',
        min_length=3,
        max_length=50,
    )

    password: str = FormField(
        title='Password',
        input_type='password',
        placeholder='Enter your password',
        help_text='Your account password',
        icon='lock',
        min_length=6,
    )

    remember_me: bool = FormField(
        False,
        title='Remember me',
        input_type='checkbox',
        help_text='Keep me logged in on this device',
        icon='check2-square',
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()


class UserRegistrationForm(FormModel):
    """User registration form with username, email, and password."""

    username: str = FormField(
        title='Username',
        input_type='text',
        placeholder='Choose a username',
        help_text='Your unique username (3-50 characters)',
        icon='person',
        min_length=3,
        max_length=50,
    )

    email: EmailStr = FormField(
        title='Email Address',
        input_type='email',
        placeholder='your.email@example.com',
        help_text='Your email address for account verification',
        icon='email',
    )

    password: str = FormField(
        title='Password',
        input_type='password',
        placeholder='Create a strong password',
        help_text='Password must be at least 8 characters',
        icon='lock',
        min_length=8,
    )

    confirm_password: str = FormField(
        title='Confirm Password',
        input_type='password',
        placeholder='Confirm your password',
        help_text='Re-enter your password to confirm',
        icon='lock',
    )

    age: Optional[int] = FormField(
        None,
        title='Age',
        input_type='number',
        placeholder='Your age (optional)',
        help_text='Your age in years',
        icon='calendar',
        min_value=13,
        max_value=120,
    )

    role: UserRole = FormField(
        UserRole.USER,
        title='Account Type',
        input_type='select',
        options=[
            {'value': 'user', 'label': '👤 User'},
            {'value': 'admin', 'label': '🔑 Admin'},
            {'value': 'moderator', 'label': '🛡️ Moderator'},
        ],
        help_text='Select your account type',
        icon='shield',
    )

    # validate_default=True is required here: an unchecked HTML checkbox/toggle
    # is simply omitted from submitted form data, so Pydantic falls back to the
    # `False` default -- and by default (validate_default=False) it does NOT
    # run field validators against a defaulted value, which would otherwise
    # let an unaccepted submission silently pass.
    accept_terms: bool = FormField(
        False,
        title='Accept Terms of Service',
        input_type='toggle',
        help_text='You must accept the Terms of Service to register',
        icon='file-earmark-check',
        validate_default=True,
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.strip()

    @field_validator('confirm_password')
    @classmethod
    def validate_passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('accept_terms')
    @classmethod
    def validate_accept_terms(cls, v):
        if not v:
            raise ValueError('You must accept the Terms of Service to register')
        return v


class PetOwnerForm(FormModel):
    """Form that demonstrates a repeating pet sub-form (a list[PetModel] field)."""

    owner_name: str = FormField(
        title='Owner Name',
        input_type='text',
        placeholder='Enter your full name',
        help_text='Your full name as the pet owner',
        icon='person',
        min_length=2,
        max_length=100,
    )

    email: EmailStr = FormField(
        title='Email Address',
        input_type='email',
        placeholder='your.email@example.com',
        help_text='Your contact email address',
        icon='envelope',
    )

    address: Optional[str] = FormField(
        None,
        title='Address',
        input_type='textarea',
        placeholder='Enter your full address...',
        help_text='Your home address (optional)',
        icon='house',
        max_length=500,
    )

    emergency_contact: Optional[str] = FormField(
        None,
        title='Emergency Contact',
        input_type='text',
        placeholder='Emergency contact name and phone',
        help_text='Someone to contact in case of emergency',
        icon='person-exclamation',
        max_length=100,
    )


class PetRegistrationForm(FormModel):
    """Complete pet registration form with owner information and pets list."""

    # Owner Information Section
    owner_name: str = FormField(
        title='Owner Name',
        input_type='text',
        placeholder='Enter your full name',
        help_text='Your full name as the pet owner',
        icon='person',
        min_length=2,
        max_length=100,
    )

    email: EmailStr = FormField(
        title='Email Address',
        input_type='email',
        placeholder='your.email@example.com',
        help_text='Your contact email address',
        icon='envelope',
    )

    address: Optional[str] = FormField(
        None,
        title='Address',
        input_type='textarea',
        placeholder='Enter your full address...',
        help_text='Your home address (optional)',
        icon='house',
        max_length=500,
    )

    emergency_contact: Optional[str] = FormField(
        None,
        title='Emergency Contact',
        input_type='text',
        placeholder='Emergency contact name and phone',
        help_text='Someone to contact in case of emergency',
        icon='person-exclamation',
        max_length=100,
    )

    # Pets List Section - using model_list with collapsible cards
    pets: List[PetModel] = FormField(
        default_factory=list,
        title='Your Pets',
        input_type='model_list',
        help_text='Add information about each of your pets',
        icon='heart',
        min_length=1,
        max_length=10,
        add_button_label='Add Another Pet',
        collapsible_items=True,
        items_expanded=False,  # Start collapsed to show the feature
        item_title_template='Pet #{index}: {name}',  # Dynamic titles
    )


class MediumContactForm(FormModel):
    """Medium complexity form - Contact form with validation."""

    # Personal Information
    first_name: str = FormField(
        title='First Name',
        input_type='text',
        placeholder='Enter your first name',
        help_text='Your given name',
        icon='person',
        min_length=2,
        max_length=50,
    )

    last_name: str = FormField(
        title='Last Name',
        input_type='text',
        placeholder='Enter your last name',
        help_text='Your family name',
        icon='person',
        min_length=2,
        max_length=50,
    )

    email: EmailStr = FormField(
        title='Email Address',
        input_type='email',
        placeholder='your.email@example.com',
        help_text="We'll never share your email",
        icon='envelope',
    )

    phone: Optional[str] = FormField(
        None,
        title='Phone Number',
        input_type='tel',
        placeholder='+1 (555) 123-4567',
        help_text='Optional phone number',
        icon='telephone',
    )

    # Message Details
    subject: str = FormField(
        title='Subject',
        input_type='text',
        placeholder='Brief subject line',
        help_text='What is this message about?',
        icon='chat-left-text',
        min_length=5,
        max_length=200,
    )

    message: str = FormField(
        title='Message',
        input_type='textarea',
        placeholder='Enter your detailed message here...',
        help_text='Please provide details about your inquiry',
        icon='chat-left-dots',
        min_length=10,
        max_length=2000,
    )

    priority: Priority = FormField(
        Priority.MEDIUM,
        title='Priority Level',
        input_type='select',
        options=[p.value for p in Priority],
        help_text='How urgent is your request?',
        icon='exclamation-triangle',
    )

    # Preferences
    subscribe_newsletter: bool = FormField(
        False,
        title='Subscribe to Newsletter',
        input_type='checkbox',
        help_text='Receive updates and news',
        icon='newspaper',
    )

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v and len(v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v


class EmergencyContactModel(FormModel):
    """Emergency contact information model."""

    name: str = FormField(
        title='Contact Name',
        input_type='text',
        placeholder='John Doe',
        help_text='Full name of emergency contact',
        icon='person-badge',
        min_length=2,
        max_length=100,
    )

    relationship: str = FormField(
        title='Relationship',
        input_type='select',
        options=[
            {'value': 'spouse', 'label': '💑 Spouse/Partner'},
            {'value': 'parent', 'label': '👨‍👩‍👧‍👦 Parent'},
            {'value': 'child', 'label': '👶 Child'},
            {'value': 'sibling', 'label': '👫 Sibling'},
            {'value': 'friend', 'label': '👥 Friend'},
            {'value': 'colleague', 'label': '💼 Colleague'},
            {'value': 'other', 'label': '🤝 Other'},
        ],
        help_text='Your relationship to this person',
        icon='people',
    )

    phone: str = FormField(
        title='Phone Number',
        input_type='tel',
        placeholder='+1 (555) 123-4567',
        help_text='Primary phone number for this contact',
        icon='telephone',
        min_length=10,
        max_length=20,
    )

    email: Optional[EmailStr] = FormField(
        None,
        title='Email Address',
        input_type='email',
        placeholder='contact@example.com',
        help_text='Email address (optional)',
        icon='envelope',
    )

    available_24_7: bool = FormField(
        False,
        title='Available 24/7',
        input_type='checkbox',
        help_text='Can this person be contacted at any time?',
        icon='clock',
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
        title='First Name',
        input_type='text',
        placeholder='Enter your first name',
        help_text='Your given name as it appears on official documents',
        icon='person',
        min_length=2,
        max_length=50,
    )

    last_name: str = FormField(
        title='Last Name',
        input_type='text',
        placeholder='Enter your last name',
        help_text='Your family name or surname',
        icon='person',
        min_length=2,
        max_length=50,
    )

    email: EmailStr = FormField(
        title='Email Address',
        input_type='email',
        placeholder='your.email@example.com',
        help_text="We'll use this to contact you about your registration",
        icon='envelope',
    )

    # Uses the modern Field(ui_element=..., ui_options=...) API instead of the
    # legacy FormField(input_type=...) used elsewhere in this model, because
    # phone_format is a widget-specific kwarg -- legacy FormField's **kwargs
    # land flat in json_schema_extra and never reach the ui_options merge path,
    # so widget-specific config like this only works through modern Field().
    phone: Optional[str] = Field(
        None,
        title='Phone Number',
        ui_element='phone',
        ui_help_text='Live-formats as you type using the (###) ###-#### mask',
        ui_options={'phone_format': '(###) ###-####'},
        json_schema_extra={'icon': 'telephone'},
    )

    birth_date: Optional[date] = FormField(
        None,
        title='Date of Birth',
        input_type='birthdate',
        help_text='Used to verify age requirements (optional) -- shows a computed age display',
        icon='calendar-date',
    )

    age: Optional[int] = FormField(
        None,
        title='Age',
        input_type='age',
        placeholder='25',
        help_text='Your current age in years',
        icon='hash',
        min_value=13,
        max_value=120,
    )

    # ======== PREFERENCES SECTION ========
    favorite_color: Optional[str] = FormField(
        '#3498db',
        title='Favorite Color',
        input_type='color',
        help_text='Pick your favorite color',
        icon='palette',
    )

    experience_level: str = FormField(
        title='Experience Level',
        input_type='select',
        options=[
            {'value': 'beginner', 'label': '🌱 Beginner (0-1 years)'},
            {'value': 'intermediate', 'label': '🚀 Intermediate (2-5 years)'},
            {'value': 'advanced', 'label': '🎯 Advanced (5-10 years)'},
            {'value': 'expert', 'label': '🏆 Expert (10+ years)'},
        ],
        help_text='Select your experience level',
        icon='trophy',
    )

    newsletter_subscription: bool = FormField(
        True,
        title='Subscribe to Newsletter',
        input_type='checkbox',
        help_text='Receive updates and news about our services',
        icon='mailbox',
    )

    # max_rating is a widget-specific kwarg (RatingInput hardcodes min/max/step
    # from it, overriding any Pydantic ge/le), so this needs modern Field()
    # rather than legacy FormField() -- same reason as `phone` above.
    rating: Optional[int] = Field(
        None,
        title='Rate Your Interest (1-10)',
        ui_element='rating',
        ui_help_text='How interested are you in our services? (range-slider based; contrast with star_rating below)',
        ui_options={'max_rating': 10},
        json_schema_extra={'icon': 'star'},
    )

    # ======== ADDRESS INFORMATION ========
    address: Optional[str] = FormField(
        None,
        title='Street Address',
        input_type='textarea',
        placeholder='123 Main Street\nApt 4B',
        help_text='Your full mailing address (optional)',
        icon='house',
        max_length=500,
    )

    country: Optional[Country] = FormField(
        None,
        title='Country',
        input_type='select',
        options=[
            {'value': Country.US.value, 'label': '🇺🇸 United States'},
            {'value': Country.CA.value, 'label': '🇨🇦 Canada'},
            {'value': Country.UK.value, 'label': '🇬🇧 United Kingdom'},
            {'value': Country.DE.value, 'label': '🇩🇪 Germany'},
            {'value': Country.FR.value, 'label': '🇫🇷 France'},
            {'value': Country.AU.value, 'label': '🇦🇺 Australia'},
            {'value': Country.JP.value, 'label': '🇯🇵 Japan'},
        ],
        help_text='Select your country of residence',
        icon='globe',
    )

    # ======== PETS SECTION (ENHANCED LIST) ========
    pets: List[PetModel] = FormField(
        default_factory=list,
        title='Your Pets',
        input_type='model_list',
        help_text='Tell us about each of your beloved pets',
        icon='heart-fill',
        min_length=0,
        max_length=5,
        add_button_label='🐾 Add Another Pet',
        collapsible_items=True,
        items_expanded=False,  # Start collapsed to showcase feature
        item_title_template='🐾 {name} the {species}',  # Dynamic titles with emojis
    )

    # ======== EMERGENCY CONTACTS (ANOTHER LIST) ========
    emergency_contacts: List[EmergencyContactModel] = FormField(
        default_factory=list,
        title='Emergency Contacts',
        input_type='model_list',
        help_text='Add people we can contact in case of emergency',
        icon='person-exclamation',
        min_length=1,
        max_length=3,
        add_button_label='➕ Add Emergency Contact',
        collapsible_items=True,
        items_expanded=True,  # Start expanded for required items
        item_title_template='📞 {name} ({relationship})',
    )

    # ======== ADDITIONAL PREFERENCES ========
    special_requests: Optional[str] = FormField(
        None,
        title='Special Requests or Comments',
        input_type='textarea',
        placeholder='Any special requests, dietary restrictions, accessibility needs, or additional comments...',
        help_text='Let us know about any special accommodations you need',
        icon='chat-dots',
        max_length=1000,
    )

    # validate_default=True: an unchecked checkbox is omitted from submitted
    # form data entirely, so without this the field_validator below never
    # runs against the `False` default and an unaccepted submission would
    # silently pass (see accept_terms on UserRegistrationForm for the same fix).
    terms_accepted: bool = FormField(
        False,
        title='I accept the Terms and Conditions',
        input_type='checkbox',
        help_text='You must accept the terms to proceed',
        icon='check-square',
        validate_default=True,
    )

    @field_validator('terms_accepted')
    @classmethod
    def validate_terms(cls, v):
        if not v:
            raise ValueError('You must accept the terms and conditions')
        return v

    # === ADDITIONAL MODELS ===

    email_field: EmailStr = FormField(
        title='Email Field',
        input_type='email',
        placeholder='user@example.com',
        help_text='Must be a valid email address',
        icon='at',
    )

    password_field: str = FormField(
        title='Password Field',
        input_type='password',
        placeholder='Enter secure password',
        help_text='At least 8 characters with mixed case',
        icon='shield-lock',
        min_length=8,
    )

    search_field: str = FormField(
        title='Search Field',
        input_type='search',
        placeholder='Search for something...',
        help_text='Search input with special styling',
        icon='search',
    )

    url_field: str = FormField(
        title='URL Field',
        input_type='url',
        placeholder='https://example.com',
        help_text='Must be a valid URL',
        icon='link-45deg',
    )

    tel_field: str = FormField(
        title='Telephone Field',
        input_type='tel',
        placeholder='+1-555-123-4567',
        help_text='Phone number input',
        icon='telephone',
    )

    textarea_field: str = FormField(
        title='Text Area',
        input_type='textarea',
        placeholder='Enter multiple lines of text...',
        help_text='Multi-line text input',
        icon='textarea-resize',
        min_length=10,
        max_length=500,
    )

    # === NUMERIC INPUTS ===
    number_field: int = FormField(
        title='Number Input',
        input_type='number',
        placeholder='42',
        help_text='Integer number input',
        icon='123',
        min_value=0,
        max_value=1000,
    )

    float_field: float = FormField(
        title='Decimal Number',
        input_type='number',
        placeholder='3.14159',
        help_text='Decimal number input',
        icon='calculator',
        min_value=0.0,
        max_value=999.99,
    )

    range_field: int = FormField(
        25,
        title='Range Slider',
        input_type='range',
        help_text='Slide to select value',
        icon='sliders',
        min_value=0,
        max_value=100,
    )

    # === SELECTION INPUTS ===
    select_field: str = FormField(
        title='Select Dropdown',
        input_type='select',
        options=['Option 1', 'Option 2', 'Option 3', 'Option 4'],
        help_text='Choose one option from dropdown',
        icon='list',
    )

    country_field: Country = FormField(
        Country.US,
        title='Country Selection',
        input_type='select',
        options=[c.value for c in Country],
        help_text='Select your country',
        icon='globe',
    )

    radio_field: str = FormField(
        'medium',
        title='Radio Button Group',
        input_type='radio',
        options=['small', 'medium', 'large', 'extra-large'],
        help_text='Select one option',
        icon='ui-radios',
    )

    multiselect_field: List[str] = FormField(
        [],
        title='Multiple Selection',
        input_type='multiselect',
        options=['JavaScript', 'Python', 'Java', 'C++', 'Go', 'Rust'],
        help_text='Select multiple programming languages (chips + search UI layered over a real <select multiple>)',
        icon='list-check',
    )

    # === BOOLEAN INPUTS ===
    checkbox_field: bool = FormField(
        False,
        title='Checkbox Input',
        input_type='checkbox',
        help_text='Check this box to agree',
        icon='check-square',
    )

    switch_field: bool = FormField(
        True,
        title='Switch Toggle',
        input_type='toggle',
        help_text='A styled on/off switch (functionally a checkbox)',
        icon='toggle-on',
    )

    # === DATE/TIME INPUTS ===
    date_field: date = FormField(
        title='Date Input', input_type='date', help_text='Select a date', icon='calendar-date'
    )

    time_field: str = FormField(
        title='Time Input', input_type='time', help_text='Select a time', icon='clock'
    )

    datetime_field: datetime = FormField(
        title='Date & Time',
        input_type='datetime-local',
        help_text='Select date and time',
        icon='calendar-event',
    )

    # === SPECIALIZED INPUTS ===
    color_field: str = FormField(
        '#3498db',
        title='Color Picker',
        input_type='color',
        help_text='Choose your favorite color',
        icon='palette',
    )

    file_field: str = FormField(
        title='File Upload',
        input_type='file',
        help_text='Upload a file (max 10MB)',
        icon='cloud-upload',
    )

    hidden_field: str = FormField(
        'hidden_value',
        title='Hidden Field',
        input_type='hidden',
        help_text='This field is hidden from users',
    )

    honeypot_field: str = FormField(
        '',
        title='Website',
        input_type='honeypot',
        help_text='Spam-trap field: always renders empty/hidden. Real users never fill it '
        'in; a bot that does gets rejected server-side (see showcase_post()).',
    )

    # === MODERNIZED / TIER-2 INPUT TYPES ===
    ssn_field: Optional[str] = FormField(
        None,
        title='Social Security Number',
        input_type='ssn',
        help_text='Formatted and masked as ###-##-####',
        icon='shield-lock',
    )

    credit_card_field: Optional[str] = FormField(
        None,
        title='Credit Card Number',
        input_type='credit_card',
        help_text='Formatted in groups of 4 digits',
        icon='credit-card',
    )

    currency_field: Optional[str] = FormField(
        None,
        title='Price',
        input_type='currency',
        help_text='Live thousands-separator formatting as you type',
        icon='cash-coin',
    )

    tags_field: str = FormField(
        'python,fastapi,pydantic',
        title='Tags',
        input_type='tags',
        help_text='Type a value and press Enter (or comma) to add a chip; Backspace removes the last one',
        icon='tags',
    )

    percentage_field: Optional[float] = FormField(
        None,
        title='Completion Percentage',
        input_type='percentage',
        help_text='0-100 with a % placeholder',
        icon='percent',
    )

    decimal_field: Optional[float] = FormField(
        None,
        title='Precise Measurement',
        input_type='decimal',
        help_text='Decimal number input with configurable precision',
        icon='calculator',
    )

    integer_only_field: Optional[int] = FormField(
        None,
        title='Whole Number',
        input_type='integer',
        help_text='Integer-only input (step forced to 1)',
        icon='123',
    )

    quantity_field: int = FormField(
        1,
        title='Quantity',
        input_type='quantity',
        help_text='Ships with +/- stepper buttons by default',
        icon='basket',
        min_value=1,
    )

    score_field: Optional[float] = FormField(
        None,
        title='Score',
        input_type='score',
        help_text='Configurable min/max numeric score',
        icon='award',
    )

    # max_stars is a widget-specific kwarg, same reason `phone`/`rating` above use modern Field().
    star_rating_field: int = Field(
        3,
        title='Star Rating',
        ui_element='star_rating',
        ui_help_text='Individually clickable stars -- a distinct widget from the range-slider `rating` field above',
        ui_options={'max_stars': 5},
        json_schema_extra={'icon': 'star-fill'},
    )

    slider_field: int = FormField(
        50,
        title='Enhanced Slider',
        input_type='slider',
        help_text='A RangeInput variant with min/max labels shown below the track',
        icon='sliders2',
        min_value=0,
        max_value=100,
    )

    temperature_field: Optional[float] = FormField(
        None,
        title='Temperature',
        input_type='temperature',
        help_text='Unit-aware placeholder/bounds (defaults to Celsius)',
        icon='thermometer-half',
    )

    combobox_field: Optional[str] = FormField(
        None,
        title='City (type to search)',
        input_type='combobox',
        options=['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
        help_text='Native datalist fallback plus JS-filtered dropdown with arrow-key navigation',
        icon='geo-alt',
    )

    # variant is a widget-specific kwarg (see radio_field/checkbox_field above for the
    # plain stacked versions of these two widgets) -- needs modern Field().
    shipping_speed: str = Field(
        'standard',
        title='Shipping Speed',
        ui_element='radio',
        ui_help_text='Segmented-control presentation of a plain radio group -- same exclusive-choice semantics',
        ui_options={'choices': ['standard', 'express', 'overnight'], 'variant': 'segmented'},
        json_schema_extra={'icon': 'truck'},
    )

    checkbox_group_field: List[str] = Field(
        default_factory=list,
        title='Notification Channels',
        ui_element='checkbox_group',
        ui_help_text='Button-group presentation of a plain checkbox group -- same independent-selection semantics',
        ui_options={'choices': ['email', 'sms', 'push', 'slack'], 'variant': 'button_group'},
        json_schema_extra={'icon': 'bell-fill'},
    )

    month_field: Optional[str] = FormField(
        None,
        title='Billing Month',
        input_type='month',
        help_text='Native month picker (e.g. for credit cards, billing periods)',
        icon='calendar3',
    )

    week_field: Optional[str] = FormField(
        None,
        title='Target Week',
        input_type='week',
        help_text='Native week picker',
        icon='calendar-week',
    )

    # secret_key is a widget-specific kwarg, so this needs modern Field(). See
    # CaptchaInput's docstring (pydantic_schemaforms/inputs/specialized_inputs.py)
    # for why verification happens at the route level in showcase_post(),
    # not via a @model_validator here.
    captcha_answer: str = Field(
        '',
        title='Verify you are human',
        ui_element='captcha',
        ui_help_text='Self-hosted arithmetic challenge -- the answer is signed and verified '
        'server-side; the sum itself is never sent to the browser',
        ui_options={'secret_key': SHOWCASE_CAPTCHA_SECRET},
    )

    # === USER PROFILE SECTION ===
    role: UserRole = FormField(
        UserRole.USER,
        title='User Role',
        input_type='select',
        options=[r.value for r in UserRole],
        help_text='Select your role',
        icon='person-badge',
    )

    bio: Optional[str] = FormField(
        None,
        title='Biography',
        input_type='textarea',
        placeholder='Tell us about yourself...',
        help_text='Optional personal biography',
        icon='person-lines-fill',
        max_length=1000,
    )

    newsletter: bool = FormField(
        False,
        title='Newsletter Subscription',
        input_type='checkbox',
        help_text='Receive our weekly newsletter',
        icon='envelope-heart',
    )

    notifications: bool = FormField(
        True,
        title='Push Notifications',
        input_type='checkbox',
        help_text='Receive push notifications',
        icon='bell',
    )

    @field_validator('password_field')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v


# ============================================================================
# ORGANIZATION NESTED FORM MODELS (5 LEVELS)
# ============================================================================


class Certification(FormModel):
    """Level 5: Individual certification credential."""

    name: str = FormField(
        title='Certification Name',
        input_type='text',
        placeholder='e.g., AWS Solutions Architect',
        help_text='Name of the certification',
        icon='award',
        max_length=100,
    )

    issuer: str = FormField(
        title='Issuing Organization',
        input_type='text',
        placeholder='e.g., Amazon Web Services',
        help_text='Organization that issued the certification',
        icon='building',
        max_length=100,
    )

    issue_date: date = FormField(
        title='Issue Date', input_type='date', help_text='When was this certification issued?'
    )

    expiry_date: Optional[date] = FormField(
        None,
        title='Expiry Date',
        input_type='date',
        help_text='When does this certification expire? (Leave empty if no expiry)',
    )

    credential_id: Optional[str] = FormField(
        None,
        title='Credential ID',
        input_type='text',
        placeholder='Optional credential identifier',
        help_text='Unique ID for credential verification',
        max_length=100,
    )

    credential_url: Optional[str] = FormField(
        None,
        title='Credential URL',
        input_type='text',
        placeholder='https://...',
        help_text='Link to verify the credential',
        max_length=500,
    )


class Subtask(FormModel):
    """Level 5: Individual subtask within a task."""

    title: str = FormField(
        title='Subtask Title',
        input_type='text',
        placeholder='Brief description of the subtask',
        help_text='What is this subtask about?',
        icon='list-check',
        max_length=200,
    )

    description: Optional[str] = FormField(
        None,
        title='Description',
        input_type='textarea',
        placeholder='Detailed description of the subtask',
        help_text='Additional details about this subtask',
        max_length=1000,
    )

    assigned_to: str = FormField(
        title='Assigned To',
        input_type='text',
        placeholder='Team member name',
        help_text='Who is responsible for this subtask?',
        icon='person',
        max_length=100,
    )

    estimated_hours: float = FormField(
        1.0,
        title='Estimated Hours',
        input_type='number',
        help_text='Estimated time to complete',
        icon='clock',
        min_value=0.5,
        max_value=100,
    )

    status: str = FormField(
        'pending',
        title='Status',
        input_type='select',
        options=[
            {'value': 'pending', 'label': '⏳ Pending'},
            {'value': 'in_progress', 'label': '🔄 In Progress'},
            {'value': 'completed', 'label': '✅ Completed'},
            {'value': 'blocked', 'label': '🚫 Blocked'},
        ],
        help_text='Current status of the subtask',
    )


class TeamMember(FormModel):
    """Level 4: Team member with certifications (Level 5)."""

    name: str = FormField(
        title='Member Name',
        input_type='text',
        placeholder='Enter full name',
        help_text='Full name of the team member',
        icon='person',
        min_length=2,
        max_length=100,
    )

    email: EmailStr = FormField(
        title='Email Address',
        input_type='email',
        placeholder='member@company.com',
        help_text='Contact email address',
    )

    role: str = FormField(
        title='Role',
        input_type='text',
        placeholder='e.g., Senior Developer',
        help_text='Job title or role',
        icon='briefcase',
        max_length=100,
    )

    hire_date: date = FormField(
        title='Hire Date', input_type='date', help_text='When did this person join?'
    )

    experience_years: int = FormField(
        0,
        title='Years of Experience',
        input_type='number',
        help_text='Total professional experience in years',
        icon='hourglass-split',
        min_value=0,
        max_value=70,
    )

    manager: Optional[str] = FormField(
        None,
        title='Manager Name',
        input_type='text',
        placeholder='Direct manager name',
        help_text='Who supervises this team member?',
        max_length=100,
    )

    certifications: List[Certification] = FormField(
        default_factory=list,
        title='Certifications',
        input_type='model_list',
        help_text='Professional certifications and credentials',
        icon='award',
        min_length=0,
        max_length=20,
        add_button_label='➕ Add Certification',
        collapsible_items=True,
        items_expanded=False,
        item_title_template='{name} - {issuer}',
    )


class Task(FormModel):
    """Level 4: Project task with subtasks (Level 5)."""

    title: str = FormField(
        title='Task Title',
        input_type='text',
        placeholder='Brief task name',
        help_text='What is this task?',
        icon='bookmark',
        min_length=3,
        max_length=200,
    )

    description: str = FormField(
        title='Task Description',
        input_type='textarea',
        placeholder='Detailed description of the task',
        help_text='Full description of what needs to be done',
        max_length=2000,
    )

    priority: str = FormField(
        'medium',
        title='Priority Level',
        input_type='select',
        options=[
            {'value': 'low', 'label': '🟢 Low'},
            {'value': 'medium', 'label': '🟡 Medium'},
            {'value': 'high', 'label': '🔴 High'},
            {'value': 'critical', 'label': '⛔ Critical'},
        ],
        help_text='Task priority level',
        icon='exclamation-circle',
    )

    status: str = FormField(
        'planning',
        title='Task Status',
        input_type='select',
        options=[
            {'value': 'planning', 'label': '📋 Planning'},
            {'value': 'in_progress', 'label': '🔄 In Progress'},
            {'value': 'in_review', 'label': '👀 In Review'},
            {'value': 'completed', 'label': '✅ Completed'},
            {'value': 'cancelled', 'label': '❌ Cancelled'},
        ],
        help_text='Current task status',
    )

    start_date: date = FormField(
        title='Start Date', input_type='date', help_text='When should this task start?'
    )

    due_date: date = FormField(
        title='Due Date', input_type='date', help_text='When is this task due?'
    )

    assigned_to: Optional[str] = FormField(
        None,
        title='Assigned To',
        input_type='text',
        placeholder='Team member name',
        help_text='Who is responsible for this task?',
        max_length=100,
    )

    estimated_hours: float = FormField(
        8.0,
        title='Estimated Hours',
        input_type='number',
        help_text='Estimated time to complete (in hours)',
        icon='clock',
        min_value=0.5,
        max_value=1000,
    )

    subtasks: List[Subtask] = FormField(
        default_factory=list,
        title='Subtasks',
        input_type='model_list',
        help_text='Break down this task into smaller subtasks',
        icon='list-check',
        min_length=0,
        max_length=50,
        add_button_label='➕ Add Subtask',
        collapsible_items=True,
        items_expanded=False,
        item_title_template='🔹 {title}',
    )


class Team(FormModel):
    """Level 3: Team with members (Level 4) who have certifications (Level 5)."""

    name: str = FormField(
        title='Team Name',
        input_type='text',
        placeholder='e.g., Backend Team',
        help_text='Name of the team',
        icon='people',
        min_length=2,
        max_length=100,
    )

    description: Optional[str] = FormField(
        None,
        title='Team Description',
        input_type='textarea',
        placeholder='What does this team do?',
        help_text="Brief description of the team's responsibilities",
        max_length=500,
    )

    team_lead: str = FormField(
        title='Team Lead Name',
        input_type='text',
        placeholder='Name of the team lead',
        help_text='Who leads this team?',
        icon='star',
        max_length=100,
    )

    formed_date: date = FormField(
        title='Formation Date', input_type='date', help_text='When was this team formed?'
    )

    members: List[TeamMember] = FormField(
        default_factory=list,
        title='Team Members',
        input_type='model_list',
        help_text='Add team members and their certifications',
        icon='people',
        min_length=1,
        max_length=100,
        add_button_label='👤 Add Team Member',
        collapsible_items=True,
        items_expanded=False,
        item_title_template='👤 {name} - {role}',
    )


class Project(FormModel):
    """Level 3: Project with tasks (Level 4) that have subtasks (Level 5)."""

    name: str = FormField(
        title='Project Name',
        input_type='text',
        placeholder='e.g., Mobile App Redesign',
        help_text='Name of the project',
        icon='kanban',
        min_length=3,
        max_length=200,
    )

    description: str = FormField(
        title='Project Description',
        input_type='textarea',
        placeholder='Detailed description of the project',
        help_text='What is this project about?',
        max_length=2000,
    )

    status: str = FormField(
        'planning',
        title='Project Status',
        input_type='select',
        options=[
            {'value': 'planning', 'label': '📋 Planning'},
            {'value': 'in_progress', 'label': '🚀 In Progress'},
            {'value': 'on_hold', 'label': '⏸️ On Hold'},
            {'value': 'completed', 'label': '✅ Completed'},
            {'value': 'archived', 'label': '📦 Archived'},
        ],
        help_text='Current project status',
        icon='flag',
    )

    start_date: date = FormField(
        title='Project Start Date', input_type='date', help_text='When does this project start?'
    )

    target_end_date: date = FormField(
        title='Target End Date',
        input_type='date',
        help_text='When should this project be completed?',
    )

    budget: float = FormField(
        0.0,
        title='Budget ($)',
        input_type='number',
        help_text='Project budget in USD',
        icon='cash-coin',
        min_value=0,
    )

    project_manager: str = FormField(
        title='Project Manager',
        input_type='text',
        placeholder='PM name',
        help_text='Who is managing this project?',
        icon='person-badge',
        max_length=100,
    )

    tasks: List[Task] = FormField(
        default_factory=list,
        title='Project Tasks',
        input_type='model_list',
        help_text='Add tasks with subtasks to organize project work',
        icon='list-check',
        min_length=1,
        max_length=200,
        add_button_label='📝 Add Task',
        collapsible_items=True,
        items_expanded=False,
        item_title_template='📋 {title}',
    )


class Department(FormModel):
    """Level 2: Department with teams (Level 3) and projects (Level 3)."""

    name: str = FormField(
        title='Department Name',
        input_type='text',
        placeholder='e.g., Engineering, Sales',
        help_text='Name of the department',
        icon='building',
        min_length=2,
        max_length=100,
    )

    description: Optional[str] = FormField(
        None,
        title='Department Description',
        input_type='textarea',
        placeholder='What does this department do?',
        help_text='Description of department responsibilities',
        max_length=1000,
    )

    department_head: str = FormField(
        title='Department Head',
        input_type='text',
        placeholder='Head of department name',
        help_text='Who leads this department?',
        icon='crown',
        max_length=100,
    )

    head_email: EmailStr = FormField(
        title='Department Head Email',
        input_type='email',
        placeholder='head@company.com',
        help_text='Contact email for the department head',
    )

    established_date: date = FormField(
        title='Established Date',
        input_type='date',
        help_text='When was this department established?',
    )

    budget: float = FormField(
        0.0,
        title='Annual Budget ($)',
        input_type='number',
        help_text='Department annual budget in USD',
        icon='cash-coin',
        min_value=0,
    )

    teams: List[Team] = FormField(
        default_factory=list,
        title='Teams',
        input_type='model_list',
        help_text='Teams within this department and their members',
        icon='people',
        min_length=1,
        max_length=50,
        add_button_label='👥 Add Team',
        collapsible_items=True,
        items_expanded=False,
        item_title_template='👥 {name} (Lead: {team_lead})',
    )

    projects: List[Project] = FormField(
        default_factory=list,
        title='Active Projects',
        input_type='model_list',
        help_text='Projects managed by this department',
        icon='kanban',
        min_length=0,
        max_length=100,
        add_button_label='🚀 Add Project',
        collapsible_items=True,
        items_expanded=False,
        item_title_template='🚀 {name}',
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
        title='Company Name',
        input_type='text',
        placeholder='Enter company name',
        help_text='Legal name of the company',
        icon='building',
        min_length=2,
        max_length=200,
    )

    company_code: str = FormField(
        title='Company Code',
        input_type='text',
        placeholder='e.g., ACME-2024',
        help_text='Unique identifier for this company',
        icon='code',
        min_length=2,
        max_length=50,
    )

    headquarters_address: str = FormField(
        title='Headquarters Address',
        input_type='textarea',
        placeholder='Full address of headquarters',
        help_text='Main office address',
        icon='geo-alt',
        max_length=500,
    )

    ceo_name: str = FormField(
        title='CEO Name',
        input_type='text',
        placeholder='Name of the CEO',
        help_text='Chief Executive Officer',
        icon='star',
        max_length=100,
    )

    ceo_email: EmailStr = FormField(
        title='CEO Email',
        input_type='email',
        placeholder='ceo@company.com',
        help_text='Email address of the CEO',
    )

    founded_date: date = FormField(
        title='Founded Date', input_type='date', help_text='When was the company founded?'
    )

    employee_count: int = FormField(
        0,
        title='Total Employees',
        input_type='number',
        help_text='Total number of employees',
        icon='people',
        min_value=1,
        max_value=1000000,
    )

    annual_revenue: float = FormField(
        0.0,
        title='Annual Revenue ($)',
        input_type='number',
        help_text='Company annual revenue in USD',
        icon='cash-coin',
        min_value=0,
    )

    website: Optional[str] = FormField(
        None,
        title='Company Website',
        input_type='text',
        placeholder='https://www.example.com',
        help_text='Company website URL',
        icon='globe',
        max_length=500,
    )

    departments: List[Department] = FormField(
        default_factory=list,
        title='Company Departments',
        input_type='model_list',
        help_text='Organize departments with teams, members, and projects',
        icon='diagram-2',
        min_length=1,
        max_length=500,
        add_button_label='🏢 Add Department',
        collapsible_items=True,
        items_expanded=False,
        item_title_template='🏢 {name} (Head: {department_head})',
    )

    @field_validator('company_code')
    @classmethod
    def validate_code(cls, v):
        """Normalize and validate company code input for demonstration purposes."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError(
                'Company code can only contain letters, numbers, hyphens, and underscores'
            )
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
        'company_name': 'TechCorp International',
        'company_code': 'TECH-2024',
        'headquarters_address': '123 Innovation Drive, San Francisco, CA 94105',
        'ceo_name': 'Jane Smith',
        'ceo_email': 'jane.smith@techcorp.com',
        'founded_date': '2010-01-15',
        'employee_count': 5000,
        'annual_revenue': 500000000.0,
        'website': 'https://www.techcorp.com',
        'departments': [
            {
                # Level 2: departments
                'name': 'Engineering',
                'description': 'Software development and infrastructure',
                'department_head': 'John Doe',
                'head_email': 'john.doe@techcorp.com',
                'established_date': '2010-06-01',
                'budget': 50000000.0,
                'teams': [
                    {
                        # Level 3: teams
                        'name': 'Backend Services',
                        'description': 'API and database services',
                        'team_lead': 'Alice Johnson',
                        'formed_date': '2015-03-01',
                        'members': [
                            {
                                # Level 4: team members
                                'name': 'Bob Wilson',
                                'email': 'bob.wilson@techcorp.com',
                                'role': 'Senior Backend Developer',
                                'hire_date': '2016-01-15',
                                'experience_years': 12,
                                'manager': 'Alice Johnson',
                                'certifications': [
                                    {
                                        # Level 5: leaf credentials
                                        'name': 'AWS Solutions Architect Professional',
                                        'issuer': 'Amazon Web Services',
                                        'issue_date': '2022-05-01',
                                        'expiry_date': '2025-05-01',
                                        'credential_id': 'AWS-12345',
                                        'credential_url': 'https://aws.amazon.com/verification/12345',
                                    },
                                    {
                                        'name': 'Certified Kubernetes Administrator',
                                        'issuer': 'Cloud Native Computing Foundation',
                                        'issue_date': '2023-01-15',
                                        'expiry_date': '2026-01-15',
                                        'credential_id': 'CKA-67890',
                                        'credential_url': 'https://cncf.io/verify/67890',
                                    },
                                    {
                                        'name': 'Google Cloud Professional Data Engineer',
                                        'issuer': 'Google Cloud',
                                        'issue_date': '2023-06-10',
                                        'expiry_date': '2025-06-10',
                                        'credential_id': 'GCP-DE-11223',
                                        'credential_url': 'https://cloud.google.com/verify/11223',
                                    },
                                ],
                            },
                            {
                                'name': 'Maria Chen',
                                'email': 'maria.chen@techcorp.com',
                                'role': 'Backend Developer',
                                'hire_date': '2019-03-10',
                                'experience_years': 7,
                                'manager': 'Alice Johnson',
                                'certifications': [
                                    {
                                        'name': 'AWS Developer Associate',
                                        'issuer': 'Amazon Web Services',
                                        'issue_date': '2021-09-20',
                                        'expiry_date': '2024-09-20',
                                        'credential_id': 'AWS-DEV-44556',
                                        'credential_url': 'https://aws.amazon.com/verification/44556',
                                    },
                                    {
                                        'name': 'MongoDB Certified Developer',
                                        'issuer': 'MongoDB Inc.',
                                        'issue_date': '2022-11-05',
                                        'expiry_date': None,
                                        'credential_id': 'MONGO-77889',
                                        'credential_url': 'https://university.mongodb.com/verify/77889',
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'name': 'Frontend & UX',
                        'description': 'Web interfaces and user experience design',
                        'team_lead': 'Carlos Rivera',
                        'formed_date': '2017-08-15',
                        'members': [
                            {
                                'name': 'Priya Patel',
                                'email': 'priya.patel@techcorp.com',
                                'role': 'Senior Frontend Engineer',
                                'hire_date': '2018-05-01',
                                'experience_years': 9,
                                'manager': 'Carlos Rivera',
                                'certifications': [
                                    {
                                        'name': 'Google UX Design Certificate',
                                        'issuer': 'Google',
                                        'issue_date': '2021-04-15',
                                        'expiry_date': None,
                                        'credential_id': 'GUX-33445',
                                        'credential_url': 'https://grow.google/verify/33445',
                                    },
                                    {
                                        'name': 'Meta React Developer Certificate',
                                        'issuer': 'Meta',
                                        'issue_date': '2022-07-20',
                                        'expiry_date': None,
                                        'credential_id': 'META-REACT-55667',
                                        'credential_url': 'https://coursera.org/verify/55667',
                                    },
                                ],
                            },
                            {
                                'name': 'David Kim',
                                'email': 'david.kim@techcorp.com',
                                'role': 'UX Designer',
                                'hire_date': '2020-11-20',
                                'experience_years': 5,
                                'manager': 'Carlos Rivera',
                                'certifications': [
                                    {
                                        'name': 'Certified UX Professional',
                                        'issuer': 'Nielsen Norman Group',
                                        'issue_date': '2022-03-12',
                                        'expiry_date': '2025-03-12',
                                        'credential_id': 'NNG-UXP-99001',
                                        'credential_url': 'https://nngroup.com/verify/99001',
                                    },
                                ],
                            },
                        ],
                    },
                ],
                'projects': [
                    {
                        # Level 3 (parallel branch): projects with tasks/subtasks
                        'name': 'Microservices Migration',
                        'description': 'Migrate monolithic application to microservices architecture',
                        'status': 'in_progress',
                        'start_date': '2024-01-01',
                        'target_end_date': '2024-12-31',
                        'budget': 2000000.0,
                        'project_manager': 'Carol Lee',
                        'tasks': [
                            {
                                # Level 4: tasks
                                'title': 'Refactor Auth Service',
                                'description': 'Extract authentication into standalone microservice',
                                'priority': 'high',
                                'status': 'in_progress',
                                'start_date': '2024-02-01',
                                'due_date': '2024-03-31',
                                'assigned_to': 'Bob Wilson',
                                'estimated_hours': 120.0,
                                'subtasks': [
                                    {
                                        # Level 5: subtasks
                                        'title': 'Create service skeleton',
                                        'description': 'Set up FastAPI project structure',
                                        'assigned_to': 'Bob Wilson',
                                        'estimated_hours': 16.0,
                                        'status': 'completed',
                                    },
                                    {
                                        'title': 'Implement JWT token handling',
                                        'description': 'Add token generation, validation, and refresh logic',
                                        'assigned_to': 'Maria Chen',
                                        'estimated_hours': 24.0,
                                        'status': 'in_progress',
                                    },
                                    {
                                        'title': 'Write integration tests',
                                        'description': 'Cover all auth endpoints with pytest',
                                        'assigned_to': 'Bob Wilson',
                                        'estimated_hours': 20.0,
                                        'status': 'pending',
                                    },
                                ],
                            },
                            {
                                'title': 'Build API Gateway',
                                'description': 'Central entry point routing requests to microservices',
                                'priority': 'high',
                                'status': 'planning',
                                'start_date': '2024-04-01',
                                'due_date': '2024-05-31',
                                'assigned_to': 'Maria Chen',
                                'estimated_hours': 80.0,
                                'subtasks': [
                                    {
                                        'title': 'Evaluate gateway options',
                                        'description': 'Compare Kong, NGINX, and AWS API Gateway',
                                        'assigned_to': 'Bob Wilson',
                                        'estimated_hours': 8.0,
                                        'status': 'completed',
                                    },
                                    {
                                        'title': 'Configure rate limiting',
                                        'description': 'Set per-client rate limits and burst handling',
                                        'assigned_to': 'Maria Chen',
                                        'estimated_hours': 16.0,
                                        'status': 'pending',
                                    },
                                ],
                            },
                            {
                                'title': 'Database Sharding Strategy',
                                'description': 'Design and implement horizontal database sharding',
                                'priority': 'medium',
                                'status': 'planning',
                                'start_date': '2024-06-01',
                                'due_date': '2024-08-31',
                                'assigned_to': 'Bob Wilson',
                                'estimated_hours': 160.0,
                                'subtasks': [
                                    {
                                        'title': 'Analyze current query patterns',
                                        'description': 'Profile slow queries and identify hot tables',
                                        'assigned_to': 'Bob Wilson',
                                        'estimated_hours': 24.0,
                                        'status': 'pending',
                                    },
                                    {
                                        'title': 'Design shard key schema',
                                        'description': 'Choose optimal shard keys to minimize cross-shard queries',
                                        'assigned_to': 'Maria Chen',
                                        'estimated_hours': 16.0,
                                        'status': 'pending',
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'name': 'Developer Portal Redesign',
                        'description': 'Modernize the developer documentation and API explorer',
                        'status': 'in_progress',
                        'start_date': '2024-03-01',
                        'target_end_date': '2024-09-30',
                        'budget': 500000.0,
                        'project_manager': 'Priya Patel',
                        'tasks': [
                            {
                                'title': 'Redesign navigation & IA',
                                'description': 'Restructure information architecture and top-level nav',
                                'priority': 'high',
                                'status': 'completed',
                                'start_date': '2024-03-01',
                                'due_date': '2024-04-15',
                                'assigned_to': 'David Kim',
                                'estimated_hours': 60.0,
                                'subtasks': [
                                    {
                                        'title': 'User interviews',
                                        'description': 'Interview 10 external developers about pain points',
                                        'assigned_to': 'David Kim',
                                        'estimated_hours': 12.0,
                                        'status': 'completed',
                                    },
                                    {
                                        'title': 'Prototype new nav structure',
                                        'description': 'Figma prototype for usability testing',
                                        'assigned_to': 'David Kim',
                                        'estimated_hours': 20.0,
                                        'status': 'completed',
                                    },
                                ],
                            },
                            {
                                'title': 'Implement interactive API playground',
                                'description': 'Build in-browser API explorer powered by OpenAPI spec',
                                'priority': 'medium',
                                'status': 'in_progress',
                                'start_date': '2024-05-01',
                                'due_date': '2024-07-31',
                                'assigned_to': 'Priya Patel',
                                'estimated_hours': 120.0,
                                'subtasks': [
                                    {
                                        'title': 'Integrate Swagger UI',
                                        'description': 'Embed and theme Swagger UI component',
                                        'assigned_to': 'Priya Patel',
                                        'estimated_hours': 16.0,
                                        'status': 'completed',
                                    },
                                    {
                                        'title': 'Add auth token management',
                                        'description': 'Let users paste/store API keys in the playground',
                                        'assigned_to': 'Priya Patel',
                                        'estimated_hours': 12.0,
                                        'status': 'in_progress',
                                    },
                                    {
                                        'title': 'Write end-to-end tests',
                                        'description': 'Playwright tests for the playground UI',
                                        'assigned_to': 'David Kim',
                                        'estimated_hours': 20.0,
                                        'status': 'pending',
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'name': 'Product',
                'description': 'Product management, roadmap, and analytics',
                'department_head': 'Linda Park',
                'head_email': 'linda.park@techcorp.com',
                'established_date': '2012-04-01',
                'budget': 15000000.0,
                'teams': [
                    {
                        'name': 'Product Strategy',
                        'description': 'Roadmap planning and market research',
                        'team_lead': 'Marcus Thompson',
                        'formed_date': '2012-04-01',
                        'members': [
                            {
                                'name': 'Sarah Nguyen',
                                'email': 'sarah.nguyen@techcorp.com',
                                'role': 'Senior Product Manager',
                                'hire_date': '2017-07-10',
                                'experience_years': 10,
                                'manager': 'Marcus Thompson',
                                'certifications': [
                                    {
                                        'name': 'Certified Scrum Product Owner',
                                        'issuer': 'Scrum Alliance',
                                        'issue_date': '2020-02-14',
                                        'expiry_date': '2026-02-14',
                                        'credential_id': 'CSPO-22334',
                                        'credential_url': 'https://scrumalliance.org/verify/22334',
                                    },
                                    {
                                        'name': 'Professional Scrum Master II',
                                        'issuer': 'Scrum.org',
                                        'issue_date': '2021-08-30',
                                        'expiry_date': None,
                                        'credential_id': 'PSM-II-55678',
                                        'credential_url': 'https://scrum.org/verify/55678',
                                    },
                                ],
                            },
                            {
                                'name': "James O'Brien",
                                'email': 'james.obrien@techcorp.com',
                                'role': 'Product Analyst',
                                'hire_date': '2021-01-18',
                                'experience_years': 4,
                                'manager': 'Marcus Thompson',
                                'certifications': [
                                    {
                                        'name': 'Google Analytics Individual Qualification',
                                        'issuer': 'Google',
                                        'issue_date': '2022-05-20',
                                        'expiry_date': '2023-05-20',
                                        'credential_id': 'GA-IQ-88990',
                                        'credential_url': 'https://skillshop.google.com/verify/88990',
                                    },
                                ],
                            },
                        ],
                    },
                ],
                'projects': [
                    {
                        'name': 'Q3 Analytics Dashboard',
                        'description': 'Self-serve analytics for enterprise customers',
                        'status': 'planning',
                        'start_date': '2024-07-01',
                        'target_end_date': '2024-09-30',
                        'budget': 300000.0,
                        'project_manager': 'Sarah Nguyen',
                        'tasks': [
                            {
                                'title': 'Define KPI requirements',
                                'description': 'Gather requirements from top 20 enterprise customers',
                                'priority': 'high',
                                'status': 'in_progress',
                                'start_date': '2024-07-01',
                                'due_date': '2024-07-15',
                                'assigned_to': "James O'Brien",
                                'estimated_hours': 40.0,
                                'subtasks': [
                                    {
                                        'title': 'Send requirements survey',
                                        'description': 'Draft and send survey via Typeform to enterprise contacts',
                                        'assigned_to': "James O'Brien",
                                        'estimated_hours': 4.0,
                                        'status': 'completed',
                                    },
                                    {
                                        'title': 'Synthesize survey results',
                                        'description': 'Analyze responses and produce a ranked KPI list',
                                        'assigned_to': "James O'Brien",
                                        'estimated_hours': 8.0,
                                        'status': 'in_progress',
                                    },
                                ],
                            },
                            {
                                'title': 'Design data model',
                                'description': 'Schema design for analytics event store',
                                'priority': 'medium',
                                'status': 'pending',
                                'start_date': '2024-07-16',
                                'due_date': '2024-08-05',
                                'assigned_to': 'Sarah Nguyen',
                                'estimated_hours': 60.0,
                                'subtasks': [
                                    {
                                        'title': 'Evaluate time-series DB options',
                                        'description': 'Compare TimescaleDB, ClickHouse, and BigQuery',
                                        'assigned_to': "James O'Brien",
                                        'estimated_hours': 12.0,
                                        'status': 'pending',
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }


# Export all the models
__all__ = [
    # Enums
    'Priority',
    'UserRole',
    'Country',
    # Form Models
    'PetModel',
    'EmergencyContactModel',
    'MinimalLoginForm',
    'UserRegistrationForm',
    'PetOwnerForm',
    'PetRegistrationForm',
    'MediumContactForm',
    'CompleteShowcaseForm',
    'Certification',
    'Subtask',
    'TeamMember',
    'Task',
    'Team',
    'Project',
    'Department',
    'CompanyOrganizationForm',
    # Layout Demonstration Forms
    'TaskItem',
    'PersonalInfoForm',
    'ContactInfoForm',
    'NotificationsForm',
    'AppearanceForm',
    'TaskListForm',
    'LayoutDemonstrationForm',
    'AccountSettingsForm',
    # Widget Gallery (tabbed showcase by input-type category)
    'TextInputsGalleryForm',
    'CheckboxTogglesGalleryForm',
    'NumericGalleryForm',
    'SelectionGalleryForm',
    'DateTimeGalleryForm',
    'SpecializedGalleryForm',
    'WidgetGalleryForm',
    # Helper Functions
    'create_sample_nested_data',
]


# ============================================================================
# LAYOUT DEMONSTRATION FORMS
# ============================================================================


class TaskItem(FormModel):
    """Individual task item for list layout demonstration."""

    task_name: str = FormField(
        title='Task Description',
        input_type='text',
        placeholder='Enter task description...',
        help_text='What needs to be done?',
        icon='check-square',
        min_length=1,
        max_length=100,
    )

    priority: str = FormField(
        'medium',
        title='Priority',
        input_type='select',
        options=[
            {'value': 'low', 'label': '🟢 Low'},
            {'value': 'medium', 'label': '🟡 Medium'},
            {'value': 'high', 'label': '🟠 High'},
            {'value': 'urgent', 'label': '🔴 Urgent'},
        ],
        help_text='How important is this task?',
        icon='exclamation-triangle',
    )

    due_date: Optional[date] = FormField(
        None,
        title='Due Date',
        input_type='date',
        help_text='When should this be completed? (optional)',
        icon='calendar-date',
    )

    completed: bool = FormField(
        False,
        title='Completed',
        input_type='checkbox',
        help_text='Is this task done?',
        icon='check',
    )


class PersonalInfoForm(FormModel):
    """Personal information form for vertical layout demonstration."""

    first_name: str = FormField(
        title='First Name',
        input_type='text',
        placeholder='Enter your first name',
        help_text='Your given name',
        icon='person',
        min_length=2,
        max_length=50,
    )

    last_name: str = FormField(
        title='Last Name',
        input_type='text',
        placeholder='Enter your last name',
        help_text='Your family name',
        icon='person',
        min_length=2,
        max_length=50,
    )

    email: EmailStr = FormField(
        title='Email Address',
        input_type='email',
        placeholder='your.email@example.com',
        help_text='Your email address',
        icon='envelope',
    )

    birth_date: Optional[date] = FormField(
        None,
        title='Date of Birth',
        input_type='date',
        help_text='Your birth date (optional)',
        icon='calendar-date',
    )


class ContactInfoForm(FormModel):
    """Contact information form for horizontal layout demonstration."""

    phone: Optional[str] = FormField(
        None,
        title='Phone Number',
        input_type='tel',
        placeholder='+1 (555) 123-4567',
        help_text='Your contact phone number',
        icon='telephone',
        max_length=20,
    )

    address: str = FormField(
        title='Street Address',
        input_type='text',
        placeholder='123 Main Street',
        help_text='Your street address',
        icon='house',
        max_length=200,
    )

    city: str = FormField(
        title='City',
        input_type='text',
        placeholder='Your city',
        help_text='City where you live',
        icon='building',
        max_length=100,
    )

    postal_code: Optional[str] = FormField(
        None,
        title='Postal Code',
        input_type='text',
        placeholder='12345',
        help_text='ZIP or postal code',
        icon='mailbox',
        max_length=10,
    )


class NotificationsForm(FormModel):
    """Notification preferences for the Notifications tab."""

    notification_email: bool = FormField(
        True,
        title='Email Notifications',
        input_type='checkbox',
        help_text='Receive notifications via email',
        icon='envelope',
    )

    notification_sms: bool = FormField(
        False,
        title='SMS Notifications',
        input_type='checkbox',
        help_text='Receive notifications via SMS',
        icon='phone',
    )

    notification_push: bool = FormField(
        False,
        title='Push Notifications',
        input_type='checkbox',
        help_text='Receive browser push notifications',
        icon='bell',
    )

    digest_frequency: str = FormField(
        'daily',
        title='Digest Frequency',
        input_type='select',
        options=[
            {'value': 'realtime', 'label': '⚡ Real-time'},
            {'value': 'hourly', 'label': '🕐 Hourly'},
            {'value': 'daily', 'label': '📅 Daily Digest'},
            {'value': 'weekly', 'label': '📆 Weekly Summary'},
        ],
        help_text='How often to receive notification digests',
        icon='clock',
    )


class AppearanceForm(FormModel):
    """Appearance preferences for the Appearance tab."""

    theme: str = FormField(
        'light',
        title='UI Theme',
        input_type='select',
        options=[
            {'value': 'light', 'label': '☀️ Light Theme'},
            {'value': 'dark', 'label': '🌙 Dark Theme'},
            {'value': 'auto', 'label': '🔄 Auto (System)'},
            {'value': 'high_contrast', 'label': '🔲 High Contrast'},
        ],
        help_text='Choose your preferred colour theme',
        icon='palette',
    )

    language: str = FormField(
        'en',
        title='Language',
        input_type='select',
        options=[
            {'value': 'en', 'label': '🇺🇸 English'},
            {'value': 'es', 'label': '🇪🇸 Spanish'},
            {'value': 'fr', 'label': '🇫🇷 French'},
            {'value': 'de', 'label': '🇩🇪 German'},
        ],
        help_text='Select your preferred language',
        icon='globe',
    )

    font_size: str = FormField(
        'medium',
        title='Font Size',
        input_type='select',
        options=[
            {'value': 'small', 'label': 'Small'},
            {'value': 'medium', 'label': 'Medium'},
            {'value': 'large', 'label': 'Large'},
        ],
        help_text='Adjust the base font size across the UI',
        icon='type',
    )

    compact_mode: bool = FormField(
        False,
        title='Compact Mode',
        input_type='checkbox',
        help_text='Reduce spacing for a denser layout',
        icon='layout-three-columns',
    )


class TaskListForm(FormModel):
    """Task management form for list layout demonstration."""

    project_name: str = FormField(
        title='Project Name',
        input_type='text',
        placeholder='Enter project name',
        help_text='Name of the project or task collection',
        icon='folder',
        min_length=2,
        max_length=100,
    )

    tasks: List[TaskItem] = FormField(
        default_factory=list,
        title='Task List',
        input_type='model_list',
        help_text='Manage your tasks (dynamic list demonstration)',
        icon='list-task',
        min_length=1,
        max_length=10,
        add_button_label='Add Task',
        item_title_template='{task_name}',
        collapsible_items=True,
        items_expanded=False,  # /menu-order shows the expanded variant
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
# LAYOUT DEMONSTRATION -- composing a form from several FormModels
# ============================================================================


class LayoutDemonstrationForm(FormModel):
    """Four independent FormModels composed into one form by nesting them as fields.

    Render it with any layout to see the same structure presented differently:
    ``layout="vertical"`` (stacked sections), ``"tabbed"``, ``"side-by-side"``,
    ``"accordion"`` or ``"wizard"``. Groups follow field declaration order. Inputs
    are named ``personal_info.first_name``, ``task_list.tasks[0].title``, ...,
    and ``validate()`` returns nested data and errors in the same shape.
    """

    personal_info: PersonalInfoForm = Field(
        title='Personal Info',
        ui_help_text='A plain nested sub-form',
        ui_step_title='About you',  # wizard step label only; tabs/panels use title
    )
    contact_info: ContactInfoForm = Field(
        title='Contact Info',
        ui_help_text='Collapsible section that starts closed (vertical layout)',
        ui_collapsible=True,
        ui_collapsed=True,
    )
    preferences: NotificationsForm = Field(
        title='Preferences', ui_help_text='Collapsible section', ui_collapsible=True
    )
    task_list: TaskListForm = Field(
        title='Task List', ui_help_text='A sub-form containing a repeating list'
    )


class AccountSettingsForm(FormModel):
    """A second grouped form for /layouts/two-forms: rendered on the same page as
    LayoutDemonstrationForm, its tabs and sections must work independently."""

    notifications: NotificationsForm = Field(title='Notifications')
    appearance: AppearanceForm = Field(title='Appearance')


# ============================================================================
# WIDGET GALLERY — every ui_element (and alias) with every one of its options
# ============================================================================
#
# Each category is its own FormModel, nested as a field of WidgetGalleryForm
# and rendered with layout="tabbed", one tab per category in declaration
# order. Every field has a default, and those defaults are the page's demo
# values (a fresh render starts from them), so a field and its demo value can
# never drift apart. CLAUDE.md requires every registered ui_element and each
# of its options to appear here; tests/test_examples_coverage.py checks it.

_SIZES = ['small', 'medium', 'large']
_CHANNELS = ['email', 'sms', 'push']
_CITIES = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
_LANGUAGES = [
    {'value': 'python', 'label': 'Python'},
    {'value': 'javascript', 'label': 'JavaScript'},
    {'value': 'go', 'label': 'Go'},
    {'value': 'rust', 'label': 'Rust'},
]


class TextInputsGalleryForm(FormModel):
    """Text-family widgets: plain, multi-line/code, masked, and formatted."""

    text_input: str = Field(
        'Hello, world!', title='Text', ui_element='text', ui_placeholder='Plain text input'
    )
    textarea_input: str = Field(
        'This textarea supports\nmultiple lines of text.',
        title='Textarea (rows=3)',
        ui_element='textarea',
        ui_options={'rows': 3},
    )
    textarea_no_resize: str = Field(
        'Fixed size: the drag handle is hidden.',
        title='Textarea (resize="none")',
        ui_element='textarea',
        ui_options={'rows': 2, 'resize': 'none'},
    )
    code_json_input: str = Field(
        '{\n  "name": "demo",\n  "enabled": true\n}',
        title='Code: JSON (Format button + syntax highlighting)',
        ui_element='textarea',
        ui_options={'language': 'json', 'rows': 6},
    )
    code_yaml_input: str = Field(
        'name: demo\nenabled: true\n',
        title='Code: YAML',
        ui_element='textarea',
        ui_options={'language': 'yaml', 'rows': 4},
    )
    code_toml_input: str = Field(
        'name = "demo"\nenabled = true\n',
        title='Code: TOML',
        ui_element='textarea',
        ui_options={'language': 'toml', 'rows': 4},
    )
    code_bash_input: str = Field(
        '#!/usr/bin/env bash\necho "hello, demo"\n',
        title='Code: Bash (whitespace cleanup + highlighting)',
        ui_element='textarea',
        ui_options={'language': 'bash', 'rows': 4},
    )
    code_python_input: str = Field(
        'def hello():\n    print("hello, demo")\n',
        title='Code: Python, 4-space indent (indent_size=4)',
        ui_element='textarea',
        ui_options={'language': 'python', 'rows': 4, 'indent_size': 4},
    )
    code_no_highlight_input: str = Field(
        '{\n  "highlighting": "off"\n}',
        title='Code: JSON, no highlighting (code_highlight=False)',
        ui_element='textarea',
        ui_options={'language': 'json', 'rows': 4, 'code_highlight': False},
    )
    code_no_format_input: str = Field(
        '{"format_button": "hidden"}',
        title='Code: JSON, no Format button (code_format=False)',
        ui_element='textarea',
        ui_options={'language': 'json', 'rows': 2, 'code_format': False},
    )
    code_no_tab_input: str = Field(
        '{"tab_key": "moves focus"}',
        title='Code: JSON, Tab moves focus (code_tab_indent=False)',
        ui_element='textarea',
        ui_options={'language': 'json', 'rows': 2, 'code_tab_indent': False},
    )
    password_input: str = Field('demo-password', title='Password', ui_element='password')
    email_input: str = Field(
        'demo@example.com', title='Email', ui_element='email', ui_placeholder='you@example.com'
    )
    search_input: str = Field(
        'pydantic schemaforms', title='Search', ui_element='search', ui_placeholder='Search...'
    )
    url_input: str = Field(
        'https://example.com', title='URL', ui_element='url', ui_placeholder='https://example.com'
    )
    tel_input: str = Field('5551234567', title='Telephone (plain)', ui_element='tel')
    phone_input: str = Field(
        '(555) 123-4567',
        title='Phone (phone_format mask as you type)',
        ui_element='phone',
        ui_options={'phone_format': '(###) ###-####'},
    )
    phone_country_code: str = Field(
        '',
        title='Phone with country code (alias "phone_number", country_code="+44")',
        ui_element='phone_number',
        ui_placeholder='20 7946 0958',
        ui_options={'country_code': '+44'},
    )
    phone_no_live_format: str = Field(
        '5551234567',
        title='Phone, formatted on blur only (live_format=False)',
        ui_element='phone',
        ui_options={'phone_format': '(###) ###-####', 'live_format': False},
    )
    ssn_input: str = Field('123-45-6789', title='Social Security Number', ui_element='ssn')
    ssn_alias: str = Field(
        '', title='SSN (alias "social_security_number")', ui_element='social_security_number'
    )
    credit_card_input: str = Field(
        '4111 1111 1111 1111', title='Credit Card Number', ui_element='credit_card'
    )
    card_alias: str = Field('', title='Credit Card (alias "card")', ui_element='card')
    cc_number_alias: str = Field(
        '', title='Credit Card (alias "cc_number")', ui_element='cc_number'
    )
    currency_input: str = Field('$1,234.56', title='Currency', ui_element='currency')
    currency_euro: str = Field(
        '€99.00',
        title='Currency in euros (alias "money", currency_symbol="€")',
        ui_element='money',
        ui_options={'currency_symbol': '€'},
    )
    currency_no_live_format: str = Field(
        '1234.5',
        title='Currency, no live formatting (live_format=False)',
        ui_element='currency',
        ui_options={'live_format': False},
    )
    tags_input: str = Field(
        'python,fastapi,pydantic',
        title='Tags',
        ui_element='tags',
        ui_help_text='Press Enter or comma to add a chip; Backspace removes the last one',
    )
    tags_semicolon: str = Field(
        'red;green;blue',
        title='Tags joined with ";" (separator=";")',
        ui_element='tags',
        ui_options={'separator': ';'},
    )


class CheckboxTogglesGalleryForm(FormModel):
    """Boolean and multi-boolean widgets: checkbox, switch, and grouped variants."""

    checkbox_unchecked: bool = Field(False, title='Checkbox (unchecked)', ui_element='checkbox')
    checkbox_checked: bool = Field(True, title='Checkbox (checked)', ui_element='checkbox')
    toggle_off: bool = Field(False, title='Toggle Switch (off)', ui_element='toggle')
    toggle_on: bool = Field(True, title='Toggle Switch (on)', ui_element='toggle')
    toggle_switch_alias: bool = Field(
        True, title='Toggle (alias "toggle_switch")', ui_element='toggle_switch'
    )
    checkbox_toggle_alias: bool = Field(
        False, title='Toggle (alias "checkbox_toggle")', ui_element='checkbox_toggle'
    )
    checkbox_group_stacked: List[str] = Field(
        default_factory=lambda: ['email', 'push'],
        title='Checkbox Group (stacked)',
        ui_element='checkbox_group',
        ui_options={'choices': _CHANNELS},
    )
    checkbox_group_buttons: List[str] = Field(
        default_factory=lambda: ['sms'],
        title='Checkbox Group (variant="button_group")',
        ui_element='checkbox_group',
        ui_options={'choices': _CHANNELS, 'variant': 'button_group'},
    )
    checkbox_group_collapsible: List[str] = Field(
        default_factory=lambda: ['email'],
        title='Checkbox Group (collapsible=True: click the legend)',
        ui_element='checkbox_group',
        ui_options={'choices': _CHANNELS, 'collapsible': True},
    )
    checkbox_group_collapsed: List[str] = Field(
        default_factory=list,
        title='Checkbox Group (collapsible, starts collapsed=True)',
        ui_element='checkbox_group',
        ui_options={'choices': _CHANNELS, 'collapsible': True, 'collapsed': True},
    )


class NumericGalleryForm(FormModel):
    """Numeric widgets, from a plain number box to specialized presentations."""

    number_input: int = Field(42, title='Number', ui_element='number')
    number_stepper: int = Field(
        5,
        title='Number with +/- buttons (show_stepper=True)',
        ui_element='number',
        ui_options={'show_stepper': True},
    )
    integer_input: int = Field(7, title='Integer', ui_element='integer')
    decimal_input: float = Field(3.14, title='Decimal (2 places by default)', ui_element='decimal')
    decimal_four_places: float = Field(
        2.7183,
        title='Decimal with 4 places (decimal_places=4)',
        ui_element='decimal',
        ui_options={'decimal_places': 4},
    )
    percentage_input: float = Field(82.5, title='Percentage', ui_element='percentage')
    age_input: int = Field(34, title='Age', ui_element='age')
    quantity_input: int = Field(3, title='Quantity (ships a +/- stepper)', ui_element='quantity')
    quantity_no_stepper: int = Field(
        1,
        title='Quantity without the stepper (show_stepper=False)',
        ui_element='quantity',
        ui_options={'show_stepper': False},
    )
    score_input: float = Field(91.0, title='Score (0-100 by default)', ui_element='score')
    score_out_of_ten: float = Field(
        7.5,
        title='Score out of 10 (min_score=0, max_score=10)',
        ui_element='score',
        ui_options={'min_score': 0, 'max_score': 10},
    )
    range_input: int = Field(65, title='Range', ui_element='range', ge=0, le=100)
    range_no_value: int = Field(
        30,
        title='Range without the value readout (show_value=False)',
        ui_element='range',
        ge=0,
        le=100,
        ui_options={'show_value': False},
    )
    slider_input: int = Field(
        55, title='Slider (with min/max labels)', ui_element='slider', ge=0, le=100
    )
    slider_no_labels: int = Field(
        20,
        title='Slider without labels (show_labels=False)',
        ui_element='slider',
        ge=0,
        le=100,
        ui_options={'show_labels': False},
    )
    rating_input: int = Field(
        8,
        title='Rating out of 10 (range-slider based, max_rating=10)',
        ui_element='rating',
        ui_options={'max_rating': 10},
    )
    rating_stars_alias: int = Field(
        4, title='Rating (alias "rating_stars", default max 5)', ui_element='rating_stars'
    )
    star_rating_input: int = Field(
        4, title='Star Rating (clickable stars)', ui_element='star_rating'
    )
    star_rating_ten: int = Field(
        7,
        title='Star Rating out of 10 (max_stars=10)',
        ui_element='star_rating',
        ui_options={'max_stars': 10},
    )
    temperature_input: float = Field(
        21.5, title='Temperature (celsius by default)', ui_element='temperature'
    )
    # unit sets the placeholder and the absolute-zero minimum, so these two
    # start empty to show the unit's placeholder.
    temperature_fahrenheit: Optional[float] = Field(
        None,
        title='Temperature, empty to show its placeholder (unit="fahrenheit")',
        ui_element='temperature',
        ui_options={'unit': 'fahrenheit'},
    )
    temperature_kelvin: Optional[float] = Field(
        None,
        title='Temperature, empty to show its placeholder (unit="kelvin")',
        ui_element='temperature',
        ui_options={'unit': 'kelvin'},
    )


class SelectionGalleryForm(FormModel):
    """Choose-from-options widgets, including every presentation variant."""

    select_input: str = Field(
        'medium',
        title='Select (dropdown)',
        ui_element='select',
        ui_options={'choices': _SIZES},
    )
    select_placeholder: str = Field(
        '',
        title='Select forcing a real choice (placeholder="Choose a size...")',
        ui_element='select',
        ui_options={'choices': _SIZES, 'placeholder': 'Choose a size...'},
    )
    select_labelled: str = Field(
        'rust',
        title='Select with value/label pairs',
        ui_element='select',
        ui_options={'choices': _LANGUAGES},
    )
    multiselect_input: List[str] = Field(
        default_factory=lambda: ['python', 'rust'],
        title='Multi-Select (chips + search)',
        ui_element='multiselect',
        ui_options={'choices': _LANGUAGES, 'search_placeholder': 'Find a language...'},
    )
    multiselect_no_search: List[str] = Field(
        default_factory=lambda: ['go'],
        title='Multi-Select, chips without search (searchable=False)',
        ui_element='multiselect',
        ui_options={'choices': _LANGUAGES, 'searchable': False},
    )
    multiselect_native: List[str] = Field(
        default_factory=lambda: ['javascript'],
        title='Multi-Select, native <select multiple> (enhanced=False)',
        ui_element='multiselect',
        ui_options={'choices': _LANGUAGES, 'enhanced': False},
    )
    radio_stacked: str = Field(
        'large',
        title='Radio (stacked)',
        ui_element='radio',
        ui_options={'choices': _SIZES},
    )
    radio_segmented: str = Field(
        'express',
        title='Radio (variant="segmented")',
        ui_element='radio',
        ui_options={'choices': ['standard', 'express', 'overnight'], 'variant': 'segmented'},
    )
    radio_collapsible: str = Field(
        'small',
        title='Radio (collapsible=True: click the legend)',
        ui_element='radio',
        ui_options={'choices': _SIZES, 'collapsible': True},
    )
    radio_collapsed: str = Field(
        'medium',
        title='Radio (collapsible, starts collapsed=True)',
        ui_element='radio',
        ui_options={'choices': _SIZES, 'collapsible': True, 'collapsed': True},
    )
    combobox_input: str = Field(
        'New York',
        title='Combobox (type to filter, matches anywhere)',
        ui_element='combobox',
        ui_options={'choices': _CITIES},
    )
    combobox_startswith: str = Field(
        '',
        title='Combobox matching from the start, after 2 characters '
        '(filter_mode="startswith", min_chars=2)',
        ui_element='combobox',
        ui_options={'choices': _CITIES, 'filter_mode': 'startswith', 'min_chars': 2},
    )


class DateTimeGalleryForm(FormModel):
    """Temporal widgets. /date-time-formats shows many more custom formats."""

    date_input: date = Field(date(2024, 6, 15), title='Date (native picker)', ui_element='date')
    date_custom_format: date = Field(
        date(2024, 6, 15),
        title='Date typed as MM/DD/YYYY (date_format="%m/%d/%Y")',
        ui_element='date',
        ui_options={'date_format': '%m/%d/%Y'},
    )
    date_no_live_format: date = Field(
        date(2024, 6, 15),
        title='Date as DD.MM.YYYY, no mask while typing (live_format=False)',
        ui_element='date',
        ui_options={'date_format': '%d.%m.%Y', 'live_format': False},
    )
    time_input: time = Field(time(14, 30), title='Time (native picker)', ui_element='time')
    time_custom_format: time = Field(
        time(14, 30),
        title='Time typed as 12-hour (time_format="%I:%M %p")',
        ui_element='time',
        ui_options={'time_format': '%I:%M %p'},
    )
    time_no_live_format: time = Field(
        time(9, 15),
        title='Time as 12-hour, no mask while typing (live_format=False)',
        ui_element='time',
        ui_options={'time_format': '%I:%M %p', 'live_format': False},
    )
    datetime_input: datetime = Field(
        datetime(2024, 6, 15, 14, 30), title='Date & Time', ui_element='datetime'
    )
    datetime_no_live_format: datetime = Field(
        datetime(2024, 6, 15, 18, 0),
        title='Date & Time as DD.MM.YYYY HH:MM, no mask while typing (live_format=False)',
        ui_element='datetime',
        ui_options={'datetime_format': '%d.%m.%Y %H:%M', 'live_format': False},
    )
    datetime_local_alias: datetime = Field(
        datetime(2024, 6, 15, 9, 0),
        title='Date & Time (alias "datetime-local")',
        ui_element='datetime-local',
    )
    datetime_custom_format: datetime = Field(
        datetime(2024, 6, 15, 14, 30),
        title='Date & Time typed as MM/DD/YYYY HH:MM (datetime_format=...)',
        ui_element='datetime',
        ui_options={'datetime_format': '%m/%d/%Y %H:%M'},
    )
    datetime_now_button: Optional[datetime] = Field(
        None,
        title='Date & Time with a "Now" button (with_set_now_button=True)',
        ui_element='datetime',
        ui_options={'with_set_now_button': True},
    )
    datetime_auto_now: Optional[datetime] = Field(
        None,
        title='Date & Time filled with the current time on load (auto_set_current=True)',
        ui_element='datetime',
        ui_options={'auto_set_current': True},
    )
    month_input: str = Field('2024-06', title='Month', ui_element='month')
    week_input: str = Field('2024-W24', title='Week', ui_element='week')
    birthdate_input: date = Field(
        date(1990, 1, 1), title='Birthdate (shows a computed age)', ui_element='birthdate'
    )
    birthdate_no_age: date = Field(
        date(1985, 5, 20),
        title='Birthdate without the age readout (show_age=False)',
        ui_element='birthdate',
        ui_options={'show_age': False},
    )


class SpecializedGalleryForm(FormModel):
    """Files and other specialized widgets."""

    file_input: str = Field(
        '', title='File Upload (drag-and-drop + preview by default)', ui_element='file'
    )
    file_documents: str = Field(
        '',
        title='Several documents (accept=".pdf,.docx", multiple=True)',
        ui_element='file',
        ui_options={'accept': '.pdf,.docx', 'multiple': True},
    )
    file_camera: str = Field(
        '',
        title='Photo from the rear camera on mobile (accept="image/*", capture="environment")',
        ui_element='file',
        ui_options={'accept': 'image/*', 'capture': 'environment'},
    )
    file_plain: str = Field(
        '',
        title='Plain file input (show_preview=False, enable_drag_drop=False)',
        ui_element='file',
        ui_options={'show_preview': False, 'enable_drag_drop': False},
    )
    color_input: str = Field('#3498db', title='Color Picker', ui_element='color')
    color_no_value: str = Field(
        '#e74c3c',
        title='Color Picker without the hex readout (show_value=False)',
        ui_element='color',
        ui_options={'show_value': False},
    )
    hidden_input: str = Field('hidden-demo-value', title='Hidden Field', ui_element='hidden')


class FieldOptionsGalleryForm(FormModel):
    """Field-level options that work on any widget, shown on plain inputs."""

    with_help: str = Field(
        'Help text sits under the input',
        title='ui_help_text',
        ui_help_text='Explain what the user should enter here.',
    )
    with_icon: str = Field('ada@example.com', title='icon="envelope"', icon='envelope')
    with_placeholder: str = Field('', title='ui_placeholder', ui_placeholder='Shown while empty')
    disabled_field: str = Field(
        'Not editable, not submitted', title='ui_disabled=True', ui_disabled=True
    )
    readonly_field: str = Field(
        'Not editable, but submitted', title='ui_readonly=True', ui_readonly=True
    )
    autofocus_field: str = Field('', title='ui_autofocus=True (focused on load)', ui_autofocus=True)
    styled_field: str = Field(
        'Custom class and inline style',
        title='ui_class="border-primary", ui_style="font-weight: 600"',
        ui_class='border-primary',
        ui_style='font-weight: 600',
    )
    ordered_first: str = Field(
        'Declared last, shown first', title='ui_order=0 (moved to the top)', ui_order=0
    )
    data_attributes: str = Field(
        '',
        title='Extra HTML attributes via ui_options (autocomplete, data-*)',
        ui_options={'autocomplete': 'off', 'data-analytics-id': 'gallery-demo'},
    )


class WidgetGalleryForm(FormModel):
    """Tabbed gallery of every registered ui_element and alias, with all its options.

    CSRF/honeypot/CAPTCHA are deliberately not included here -- they're
    route-level/security-flow concerns demonstrated end-to-end on
    CompleteShowcaseForm's /showcase route, not "just another input type".
    model_list (/pets, /menu-order) and DataTableLayout (/employees/import) are
    composition mechanisms rather than discrete widgets.
    """

    text_inputs: TextInputsGalleryForm = Field(title='Text Inputs')
    checkboxes_toggles: CheckboxTogglesGalleryForm = Field(title='Checkboxes & Toggles')
    numeric_inputs: NumericGalleryForm = Field(title='Numeric Inputs')
    selection_inputs: SelectionGalleryForm = Field(title='Selection Inputs')
    date_time: DateTimeGalleryForm = Field(title='Date & Time')
    files_specialized: SpecializedGalleryForm = Field(title='Files & Specialized')
    field_options: FieldOptionsGalleryForm = Field(title='Field Options')


# ============================================================================
# VALIDATION SHOWCASE — every kind of validation, failing and re-rendering
# ============================================================================
#
# One form, two validation layers, one error tree: Pydantic validates the
# model (Field constraints, validators, sub-forms, lists) and a rule-based
# FormValidator checks the rest; /validation merges both into the nested
# error tree render_form_html() takes. INVALID_VALIDATION_DEMO pre-fills a
# value that breaks every rule, so a single Submit shows them all.
# Live (as-you-type) HTMX validation is its own page: /live-validation.


class ValidationAddress(FormModel):
    city: str = Field(..., title='City (min_length=2)', min_length=2)
    postcode: str = Field(..., title='Postcode (pattern: 5 digits)', pattern=r'^\d{5}$')


class ValidationItem(FormModel):
    name: str = Field(..., title='Item name (min_length=1)', min_length=1)
    quantity: int = Field(1, title='Quantity (ge=1)', ge=1)


class ValidationShowcaseForm(FormModel):
    """Every kind of validation the library supports, on one form."""

    # Pydantic Field constraints. Pydantic reports only the first failing
    # constraint of a field, so each constraint gets its own field here.
    username: str = Field(..., title='Username (min_length=3)', min_length=3)
    bio: str = Field('', title='Bio (max_length=40)', max_length=40, ui_element='textarea')
    handle: str = Field(..., title='Handle (pattern=^[a-z0-9_]+$)', pattern=r'^[a-z0-9_]+$')
    age: int = Field(..., title='Age (ge=13)', ge=13)
    rating: int = Field(..., title='Rating (le=5)', le=5)
    discount: float = Field(..., title='Discount % (gt=0)', gt=0)
    tip_percent: float = Field(..., title='Tip % (lt=50)', lt=50)
    pack_size: int = Field(..., title='Pack size (multiple_of=6)', multiple_of=6)
    email: EmailStr = Field(..., title='Email (EmailStr)', ui_element='email')

    # A required checkbox, with its own message when it is left unticked
    accept_terms: Literal[True] = Field(
        title='I accept the terms (Literal[True] + unchecked_message)',
        unchecked_message='You must accept the terms to continue',
    )

    # Validators
    password: str = Field(
        ..., title='Password (@field_validator: needs a digit)', ui_element='password'
    )
    confirm_password: str = Field(
        ..., title='Confirm password (@model_validator: must match)', ui_element='password'
    )

    # Errors inside a sub-form and inside list items
    address: ValidationAddress = Field(title='Address (errors inside a sub-form)')
    items: List[ValidationItem] = Field(
        default_factory=list,
        title='Items (min_length=1 on the list, errors on each item)',
        min_length=1,
    )

    # Checked by the rule-based FormValidator in validation_showcase_rules()
    phone: str = Field('', title='Phone (RequiredRule + PhoneRule)')
    nickname: str = Field('', title='Nickname (MinLengthRule(2) + MaxLengthRule(10))')
    backup_email: str = Field('', title='Backup email (EmailRule)')
    work_email: str = Field('', title='Work email (EmailDeliverabilityRule: domain accepts mail)')
    budget: str = Field('', title='Budget (NumericRangeRule 100-10000)')
    website: str = Field('', title='Website (RegexRule: starts with http(s)://)')
    coupon: str = Field('', title='Coupon (CustomRule: starts with SAVE)')
    start_date: str = Field(
        '', title='Start date (DateRangeRule: 2025 or later)', ui_element='date'
    )
    end_date: str = Field('', title='End date (cross-field rule: after start)', ui_element='date')

    @field_validator('password')
    @classmethod
    def _password_has_digit(cls, value: str) -> str:
        if not any(ch.isdigit() for ch in value):
            raise ValueError('Password must contain at least one digit')
        return value

    @model_validator(mode='after')
    def _passwords_match(self) -> 'ValidationShowcaseForm':
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


def _end_after_start(data: dict) -> tuple[bool, dict[str, str]]:
    start, end = data.get('start_date'), data.get('end_date')
    if start and end and end <= start:
        return False, {'end_date': 'End date must be after the start date'}
    return True, {}


def validation_showcase_rules() -> FormValidator:
    """The rule-based half of /validation: rule classes plus a cross-field rule."""

    rules = FormValidator()
    rules.field('phone').add_rule(RequiredRule('Phone is required')).add_rule(PhoneRule())
    rules.field('nickname').add_rule(MinLengthRule(2)).add_rule(MaxLengthRule(10))
    rules.field('backup_email').add_rule(EmailRule())
    # Looks the domain up in DNS; reserved names like .invalid fail without a lookup.
    rules.field('work_email').add_rule(EmailDeliverabilityRule())
    rules.field('budget').add_rule(NumericRangeRule(min_value=100, max_value=10000))
    rules.field('website').add_rule(RegexRule(r'^https?://', 'Must start with http:// or https://'))
    rules.field('coupon').add_rule(
        CustomRule(lambda value: str(value).startswith('SAVE'), 'Coupons start with SAVE')
    )
    rules.field('start_date').add_rule(DateRangeRule(min_date=date(2025, 1, 1)))
    rules.add_cross_field_rule(_end_after_start)
    return rules


VALID_VALIDATION_DEMO = {
    'username': 'ada',
    'bio': 'Mathematician and writer.',
    'handle': 'ada_l',
    'age': 36,
    'rating': 5,
    'discount': 10,
    'tip_percent': 15,
    'pack_size': 12,
    'email': 'ada@example.com',
    'accept_terms': True,
    'password': 'engine1843',
    'confirm_password': 'engine1843',
    'address': {'city': 'London', 'postcode': '10001'},
    'items': [{'name': 'Widget', 'quantity': 2}],
    'phone': '(555) 123-4567',
    'nickname': 'ada',
    'backup_email': 'ada.backup@example.com',
    'work_email': '',
    'budget': '2500',
    'website': 'https://example.com',
    'coupon': 'SAVE10',
    'start_date': '2025-03-01',
    'end_date': '2025-04-01',
}

# Everything valid except the passwords: Pydantic only runs
# @model_validator(mode='after') once every field is valid, so the form-wide
# "_errors" message needs its own scenario.
PASSWORD_MISMATCH_DEMO = VALID_VALIDATION_DEMO | {'confirm_password': 'engine1844'}

INVALID_VALIDATION_DEMO = {
    'username': 'ab',
    'bio': 'This bio is far longer than the forty characters allowed.',
    'handle': 'Bad Handle!',
    'age': 9,
    'rating': 9,
    'discount': 0,
    'tip_percent': 75,
    'pack_size': 10,
    'email': 'not-an-email',
    'password': 'nodigits',
    'confirm_password': 'different',
    'address': {'city': 'X', 'postcode': 'ABC'},
    'items': [{'name': 'Widget', 'quantity': 2}, {'name': '', 'quantity': 0}],
    'phone': '123',
    'nickname': 'x',
    'backup_email': 'backup-at-example',
    'work_email': 'someone@no-such-domain.invalid',
    'budget': '50',
    'website': 'ftp://example.com',
    'coupon': 'FREE10',
    'start_date': '2024-03-01',
    'end_date': '2024-02-01',
}
