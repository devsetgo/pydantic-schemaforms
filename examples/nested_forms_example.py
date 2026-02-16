#!/usr/bin/env python3
"""
Nested Forms Example - Comprehensive Tabbed Interface
======================================================

This example pushes the Pydantic SchemaForms library past normal use cases
by creating a comprehensive tabbed interface with:
- Multiple levels of nesting (5 levels deep)
- ALL input types demonstrated
- Complex hierarchical data structures
- Validation cascading through nested models
- Large nested lists with collapsible items

Tabbed Structure:
1. Organization Tab - 5-level nested company structure
2. Kitchen Sink Tab - ALL input types in one place
3. Contact Management Tab - Advanced contact forms with nested data
4. Scheduling Tab - Date/time management with recurring events
5. Media & Files Tab - File uploads, color schemes, and media preferences
6. Settings Tab - Application settings and preferences

This tests the library's ability to handle deep nesting, large lists,
complex form hierarchies, and every possible input type.
"""

import os
import sys
from datetime import date, datetime
from typing import List, Optional

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import EmailStr, field_validator
from pydantic_schemaforms.form_field import FormField
from pydantic_schemaforms.form_layouts import HorizontalLayout, TabbedLayout, VerticalLayout
from pydantic_schemaforms.schema_form import FormModel


# ============================================================================
# LEVEL 5 (DEEPEST) - Leaf Models
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


# ============================================================================
# LEVEL 4 - Containers for Level 5
# ============================================================================

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


# ============================================================================
# LEVEL 3 - Containers for Level 4
# ============================================================================

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


# ============================================================================
# LEVEL 2 - Containers for Level 3
# ============================================================================

# ============================================================================
# LAYOUT DEMO FORMS (PUSH LAYOUT ENGINE)
# ============================================================================

class DepartmentSummaryForm(FormModel):
    """Compact summary form used inside layout demos."""

    strategic_goal: str = FormField(
        title="Strategic Goal",
        input_type="text",
        placeholder="e.g., Reduce infra costs by 15%",
        help_text="Primary department goal for this year",
        icon="bullseye",
        max_length=200
    )

    hiring_plan: str = FormField(
        title="Hiring Plan",
        input_type="textarea",
        placeholder="Describe the hiring plan for the next 12 months",
        help_text="Key roles and timeline",
        max_length=1000
    )

    risk_level: str = FormField(
        "medium",
        title="Risk Level",
        input_type="select",
        options=[
            {"value": "low", "label": "🟢 Low"},
            {"value": "medium", "label": "🟡 Medium"},
            {"value": "high", "label": "🔴 High"}
        ],
        help_text="Overall operational risk assessment"
    )


class ProjectPortfolioForm(FormModel):
    """Portfolio-level details for layout demo."""

    portfolio_owner: str = FormField(
        title="Portfolio Owner",
        input_type="text",
        placeholder="Name of the portfolio owner",
        help_text="Who owns this portfolio?",
        icon="person-badge",
        max_length=100
    )

    quarterly_budget: float = FormField(
        0.0,
        title="Quarterly Budget ($)",
        input_type="number",
        help_text="Planned spend for this quarter",
        icon="cash-coin",
        min_value=0
    )

    portfolio_status: str = FormField(
        "on_track",
        title="Portfolio Status",
        input_type="select",
        options=[
            {"value": "on_track", "label": "✅ On Track"},
            {"value": "at_risk", "label": "⚠️ At Risk"},
            {"value": "off_track", "label": "🚨 Off Track"}
        ],
        help_text="Overall portfolio health"
    )


class DepartmentSummaryLayout(VerticalLayout):
    """Vertical layout for department summary."""
    form = DepartmentSummaryForm


class ProjectPortfolioLayout(HorizontalLayout):
    """Horizontal layout for project portfolio."""
    form = ProjectPortfolioForm


class DepartmentInsightsTabbed(TabbedLayout):
    """Tabbed layout combining multiple layout types."""
    summary = DepartmentSummaryLayout()
    portfolio = ProjectPortfolioLayout()

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


# ============================================================================
# LEVEL 1 (ROOT) - The Complete Organization
# ============================================================================

class CompanyOrganizationForm(FormModel):
    """
    Level 1 (Root): Complete company structure with 5 levels of nesting.

    This is the ultimate stress test for the Pydantic SchemaForms library.
    It creates a deeply nested organizational hierarchy:

    Company (Level 1)
    ├─ Department 1 (Level 2)
    │  ├─ Team A (Level 3)
    │  │  ├─ Member 1 (Level 4)
    │  │  │  └─ Certification 1 (Level 5)
    │  │  └─ Member 2 (Level 4)
    │  │     └─ Certification 2 (Level 5)
    │  └─ Project A (Level 3)
    │     ├─ Task 1 (Level 4)
    │     │  ├─ Subtask 1.1 (Level 5)
    │     │  └─ Subtask 1.2 (Level 5)
    │     └─ Task 2 (Level 4)
    │        └─ Subtask 2.1 (Level 5)
    └─ Department 2 (Level 2)
       └─ ...

    This demonstrates the library's ability to handle:
    - 5 levels of model nesting
    - Multiple lists at each level
    - Complex validation across levels
    - Large nested structures
    - Dynamic form rendering with collapsed/expanded states
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
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Company code can only contain letters, numbers, hyphens, and underscores")
        return v.upper()


# ============================================================================
# TAB 2: KITCHEN SINK - ALL INPUT TYPES
# ============================================================================

class KitchenSinkForm(FormModel):
    """Comprehensive form demonstrating EVERY input type available."""

    # === TEXT INPUTS ===
    text_input: str = FormField(
        title="Text Input",
        input_type="text",
        placeholder="Enter any text",
        help_text="Standard text input field",
        icon="fonts",
        max_length=100
    )

    email_input: EmailStr = FormField(
        title="Email Input",
        input_type="email",
        placeholder="user@example.com",
        help_text="Email address with validation",
        icon="envelope-at"
    )

    password_input: str = FormField(
        title="Password Input",
        input_type="password",
        placeholder="Enter password",
        help_text="Password field (masked input)",
        icon="key",
        min_length=8
    )

    search_input: str = FormField(
        title="Search Input",
        input_type="search",
        placeholder="Search...",
        help_text="Search field with special styling",
        icon="search"
    )

    url_input: str = FormField(
        title="URL Input",
        input_type="url",
        placeholder="https://example.com",
        help_text="URL field with validation",
        icon="link-45deg"
    )

    tel_input: str = FormField(
        title="Telephone Input",
        input_type="tel",
        placeholder="+1-555-123-4567",
        help_text="Telephone number input",
        icon="telephone"
    )

    textarea_input: str = FormField(
        title="Text Area",
        input_type="textarea",
        placeholder="Enter multiple lines of text...",
        help_text="Multi-line text input",
        icon="textarea-t",
        max_length=500
    )

    # === NUMERIC INPUTS ===
    number_input: int = FormField(
        42,
        title="Number Input (Integer)",
        input_type="number",
        help_text="Integer number input",
        icon="123",
        min_value=0,
        max_value=1000
    )

    decimal_input: float = FormField(
        3.14,
        title="Decimal Input (Float)",
        input_type="number",
        help_text="Floating-point number input",
        icon="calculator",
        min_value=0.0,
        max_value=999.99
    )

    range_input: int = FormField(
        50,
        title="Range Slider",
        input_type="range",
        help_text="Slider for selecting a value",
        icon="sliders",
        min_value=0,
        max_value=100
    )

    # === SELECTION INPUTS ===
    select_input: str = FormField(
        "option2",
        title="Select Dropdown",
        input_type="select",
        options=[
            {"value": "option1", "label": "Option 1"},
            {"value": "option2", "label": "Option 2"},
            {"value": "option3", "label": "Option 3"},
            {"value": "option4", "label": "Option 4"}
        ],
        help_text="Single select dropdown",
        icon="ui-checks"
    )

    radio_input: str = FormField(
        "medium",
        title="Radio Buttons",
        input_type="radio",
        options=[
            {"value": "small", "label": "Small"},
            {"value": "medium", "label": "Medium"},
            {"value": "large", "label": "Large"}
        ],
        help_text="Radio button group",
        icon="ui-radios"
    )

    multiselect_input: List[str] = FormField(
        ["python", "javascript"],
        title="Multiple Selection",
        input_type="select",
        options=[
            {"value": "python", "label": "🐍 Python"},
            {"value": "javascript", "label": "📜 JavaScript"},
            {"value": "typescript", "label": "📘 TypeScript"},
            {"value": "java", "label": "☕ Java"},
            {"value": "go", "label": "🐹 Go"},
            {"value": "rust", "label": "🦀 Rust"}
        ],
        help_text="Select multiple options",
        icon="list-check"
    )

    # === BOOLEAN INPUTS ===
    checkbox_input: bool = FormField(
        True,
        title="Checkbox Input",
        input_type="checkbox",
        help_text="Boolean checkbox",
        icon="check-square"
    )

    toggle_input: bool = FormField(
        False,
        title="Toggle Switch",
        input_type="checkbox",
        help_text="Boolean toggle switch",
        icon="toggle-on"
    )

    # === DATE/TIME INPUTS ===
    date_input: date = FormField(
        title="Date Input",
        input_type="date",
        help_text="Date picker",
        icon="calendar-date"
    )

    time_input: Optional[str] = FormField(
        None,
        title="Time Input",
        input_type="time",
        help_text="Time picker",
        icon="clock"
    )

    datetime_input: Optional[datetime] = FormField(
        None,
        title="DateTime Input",
        input_type="datetime-local",
        help_text="Date and time picker",
        icon="calendar-event"
    )

    # === SPECIALIZED INPUTS ===
    color_input: str = FormField(
        "#3498db",
        title="Color Picker",
        input_type="color",
        help_text="Color selection input",
        icon="palette"
    )

    hidden_input: str = FormField(
        "secret_value",
        title="Hidden Input",
        input_type="hidden",
        help_text="Hidden field (not visible to users)"
    )


# ============================================================================
# TAB 3: CONTACT MANAGEMENT
# ============================================================================

class PhoneNumber(FormModel):
    """Nested phone number model."""

    phone_type: str = FormField(
        title="Type",
        input_type="select",
        options=[
            {"value": "mobile", "label": "📱 Mobile"},
            {"value": "work", "label": "💼 Work"},
            {"value": "home", "label": "🏠 Home"},
            {"value": "fax", "label": "📠 Fax"}
        ],
        help_text="Type of phone number"
    )

    number: str = FormField(
        title="Phone Number",
        input_type="tel",
        placeholder="+1 (555) 123-4567",
        help_text="Contact phone number",
        icon="telephone",
        max_length=20
    )

    is_primary: bool = FormField(
        False,
        title="Primary Number",
        input_type="checkbox",
        help_text="Is this the primary contact number?"
    )


class Address(FormModel):
    """Nested address model."""

    address_type: str = FormField(
        title="Address Type",
        input_type="select",
        options=[
            {"value": "home", "label": "🏠 Home"},
            {"value": "work", "label": "💼 Work"},
            {"value": "billing", "label": "💳 Billing"},
            {"value": "shipping", "label": "📦 Shipping"}
        ],
        help_text="Type of address"
    )

    street_line1: str = FormField(
        title="Street Address Line 1",
        input_type="text",
        placeholder="123 Main Street",
        help_text="Primary street address",
        icon="house",
        max_length=200
    )

    street_line2: Optional[str] = FormField(
        None,
        title="Street Address Line 2",
        input_type="text",
        placeholder="Apt 4B",
        help_text="Apartment, suite, unit, etc.",
        max_length=200
    )

    city: str = FormField(
        title="City",
        input_type="text",
        placeholder="San Francisco",
        help_text="City name",
        icon="building",
        max_length=100
    )

    state: str = FormField(
        title="State/Province",
        input_type="text",
        placeholder="CA",
        help_text="State or province",
        max_length=50
    )

    postal_code: str = FormField(
        title="Postal Code",
        input_type="text",
        placeholder="94105",
        help_text="ZIP or postal code",
        icon="mailbox",
        max_length=20
    )

    country: str = FormField(
        "US",
        title="Country",
        input_type="select",
        options=[
            {"value": "US", "label": "🇺🇸 United States"},
            {"value": "CA", "label": "🇨🇦 Canada"},
            {"value": "UK", "label": "🇬🇧 United Kingdom"},
            {"value": "AU", "label": "🇦🇺 Australia"},
            {"value": "DE", "label": "🇩🇪 Germany"},
            {"value": "FR", "label": "🇫🇷 France"},
            {"value": "JP", "label": "🇯🇵 Japan"}
        ],
        help_text="Country",
        icon="globe"
    )


class ContactManagementForm(FormModel):
    """Advanced contact management with nested phone numbers and addresses."""

    first_name: str = FormField(
        title="First Name",
        input_type="text",
        placeholder="John",
        help_text="Contact's first name",
        icon="person",
        min_length=1,
        max_length=100
    )

    last_name: str = FormField(
        title="Last Name",
        input_type="text",
        placeholder="Doe",
        help_text="Contact's last name",
        icon="person",
        min_length=1,
        max_length=100
    )

    email: EmailStr = FormField(
        title="Primary Email",
        input_type="email",
        placeholder="john.doe@example.com",
        help_text="Primary email address",
        icon="envelope"
    )

    company: Optional[str] = FormField(
        None,
        title="Company",
        input_type="text",
        placeholder="Acme Corporation",
        help_text="Company or organization",
        icon="building",
        max_length=200
    )

    job_title: Optional[str] = FormField(
        None,
        title="Job Title",
        input_type="text",
        placeholder="Software Engineer",
        help_text="Position or role",
        icon="briefcase",
        max_length=100
    )

    birth_date: Optional[date] = FormField(
        None,
        title="Date of Birth",
        input_type="date",
        help_text="Birth date (optional)",
        icon="cake"
    )

    phone_numbers: List[PhoneNumber] = FormField(
        default_factory=list,
        title="Phone Numbers",
        input_type="model_list",
        help_text="Add multiple phone numbers",
        icon="telephone",
        min_length=0,
        max_length=10,
        model_class=PhoneNumber,
        add_button_text="➕ Add Phone Number",
        remove_button_text="Remove",
        collapsible_items=True,
        items_expanded=True,
        item_title_template="📞 {phone_type}: {number}",
        section_design={
            "section_title": "Contact Numbers",
            "section_description": "Manage multiple phone numbers",
            "icon": "bi bi-telephone",
            "collapsible": True,
            "collapsed": False
        }
    )

    addresses: List[Address] = FormField(
        default_factory=list,
        title="Addresses",
        input_type="model_list",
        help_text="Add multiple addresses",
        icon="house",
        min_length=0,
        max_length=5,
        model_class=Address,
        add_button_text="➕ Add Address",
        remove_button_text="Remove",
        collapsible_items=True,
        items_expanded=False,
        item_title_template="📍 {address_type}: {city}, {state}",
        section_design={
            "section_title": "Addresses",
            "section_description": "Manage multiple addresses",
            "icon": "bi bi-house",
            "collapsible": True,
            "collapsed": False
        }
    )

    notes: Optional[str] = FormField(
        None,
        title="Notes",
        input_type="textarea",
        placeholder="Additional notes about this contact...",
        help_text="Any additional information",
        icon="sticky",
        max_length=2000
    )


# ============================================================================
# TAB 4: SCHEDULING & EVENTS
# ============================================================================

class RecurringEvent(FormModel):
    """Nested recurring event model."""

    event_name: str = FormField(
        title="Event Name",
        input_type="text",
        placeholder="Weekly Team Meeting",
        help_text="Name of the recurring event",
        icon="calendar-event",
        max_length=200
    )

    event_type: str = FormField(
        title="Event Type",
        input_type="select",
        options=[
            {"value": "meeting", "label": "🤝 Meeting"},
            {"value": "reminder", "label": "⏰ Reminder"},
            {"value": "deadline", "label": "📅 Deadline"},
            {"value": "birthday", "label": "🎂 Birthday"},
            {"value": "anniversary", "label": "💍 Anniversary"},
            {"value": "other", "label": "📌 Other"}
        ],
        help_text="Type of event"
    )

    start_date: date = FormField(
        title="Start Date",
        input_type="date",
        help_text="When does this event start?",
        icon="calendar-check"
    )

    start_time: Optional[str] = FormField(
        None,
        title="Start Time",
        input_type="time",
        help_text="Event start time (optional)",
        icon="clock"
    )

    duration_minutes: int = FormField(
        60,
        title="Duration (minutes)",
        input_type="number",
        help_text="How long is the event?",
        icon="hourglass",
        min_value=15,
        max_value=1440
    )

    recurrence_pattern: str = FormField(
        "weekly",
        title="Recurrence Pattern",
        input_type="select",
        options=[
            {"value": "daily", "label": "📆 Daily"},
            {"value": "weekly", "label": "📅 Weekly"},
            {"value": "biweekly", "label": "📅📅 Bi-weekly"},
            {"value": "monthly", "label": "📆 Monthly"},
            {"value": "yearly", "label": "🗓️ Yearly"}
        ],
        help_text="How often does this repeat?"
    )

    end_date: Optional[date] = FormField(
        None,
        title="End Date",
        input_type="date",
        help_text="When should recurrence stop? (optional)"
    )

    location: Optional[str] = FormField(
        None,
        title="Location",
        input_type="text",
        placeholder="Conference Room A",
        help_text="Where will this event take place?",
        icon="geo-alt",
        max_length=200
    )

    send_reminder: bool = FormField(
        True,
        title="Send Reminder",
        input_type="checkbox",
        help_text="Send notification before event?",
        icon="bell"
    )


class SchedulingForm(FormModel):
    """Calendar and scheduling management."""

    calendar_name: str = FormField(
        title="Calendar Name",
        input_type="text",
        placeholder="Work Calendar",
        help_text="Name for this calendar",
        icon="calendar3",
        max_length=100
    )

    timezone: str = FormField(
        "America/Los_Angeles",
        title="Timezone",
        input_type="select",
        options=[
            {"value": "America/New_York", "label": "🌆 Eastern (ET)"},
            {"value": "America/Chicago", "label": "🌇 Central (CT)"},
            {"value": "America/Denver", "label": "🏔️ Mountain (MT)"},
            {"value": "America/Los_Angeles", "label": "🌴 Pacific (PT)"},
            {"value": "Europe/London", "label": "🇬🇧 London (GMT)"},
            {"value": "Europe/Paris", "label": "🇫🇷 Paris (CET)"},
            {"value": "Asia/Tokyo", "label": "🇯🇵 Tokyo (JST)"}
        ],
        help_text="Your timezone",
        icon="globe"
    )

    default_event_duration: int = FormField(
        60,
        title="Default Event Duration (minutes)",
        input_type="range",
        help_text="Default length for new events",
        icon="clock",
        min_value=15,
        max_value=480
    )

    work_start_time: Optional[str] = FormField(
        "09:00",
        title="Work Start Time",
        input_type="time",
        help_text="When does your workday start?",
        icon="sunrise"
    )

    work_end_time: Optional[str] = FormField(
        "17:00",
        title="Work End Time",
        input_type="time",
        help_text="When does your workday end?",
        icon="sunset"
    )

    weekend_days: List[str] = FormField(
        ["saturday", "sunday"],
        title="Weekend Days",
        input_type="select",
        options=[
            {"value": "sunday", "label": "Sunday"},
            {"value": "monday", "label": "Monday"},
            {"value": "tuesday", "label": "Tuesday"},
            {"value": "wednesday", "label": "Wednesday"},
            {"value": "thursday", "label": "Thursday"},
            {"value": "friday", "label": "Friday"},
            {"value": "saturday", "label": "Saturday"}
        ],
        help_text="Select your non-working days",
        icon="calendar-x"
    )

    recurring_events: List[RecurringEvent] = FormField(
        default_factory=list,
        title="Recurring Events",
        input_type="model_list",
        help_text="Set up recurring events and reminders",
        icon="arrow-repeat",
        min_length=0,
        max_length=50,
        model_class=RecurringEvent,
        add_button_text="➕ Add Recurring Event",
        remove_button_text="Remove",
        collapsible_items=True,
        items_expanded=False,
        item_title_template="🔄 {event_name} ({recurrence_pattern})",
        section_design={
            "section_title": "Recurring Events",
            "section_description": "Manage repeating events and reminders",
            "icon": "bi bi-arrow-repeat",
            "collapsible": True,
            "collapsed": False
        }
    )


# ============================================================================
# TAB 5: MEDIA & FILES
# ============================================================================

class ColorTheme(FormModel):
    """Nested color theme model."""

    theme_name: str = FormField(
        title="Theme Name",
        input_type="text",
        placeholder="Ocean Blue",
        help_text="Name for this color theme",
        icon="palette",
        max_length=50
    )

    primary_color: str = FormField(
        "#3498db",
        title="Primary Color",
        input_type="color",
        help_text="Main brand color",
        icon="palette"
    )

    secondary_color: str = FormField(
        "#2ecc71",
        title="Secondary Color",
        input_type="color",
        help_text="Secondary accent color",
        icon="palette"
    )

    accent_color: str = FormField(
        "#e74c3c",
        title="Accent Color",
        input_type="color",
        help_text="Highlight color",
        icon="palette"
    )

    background_color: str = FormField(
        "#ffffff",
        title="Background Color",
        input_type="color",
        help_text="Page background color",
        icon="palette"
    )

    text_color: str = FormField(
        "#333333",
        title="Text Color",
        input_type="color",
        help_text="Primary text color",
        icon="palette"
    )

    is_default: bool = FormField(
        False,
        title="Set as Default",
        input_type="checkbox",
        help_text="Use this as the default theme?"
    )


class MediaFilesForm(FormModel):
    """Media preferences and file management."""

    profile_picture_url: Optional[str] = FormField(
        None,
        title="Profile Picture URL",
        input_type="url",
        placeholder="https://example.com/avatar.jpg",
        help_text="URL to profile picture",
        icon="person-circle",
        max_length=500
    )

    background_image_url: Optional[str] = FormField(
        None,
        title="Background Image URL",
        input_type="url",
        placeholder="https://example.com/background.jpg",
        help_text="URL to background image",
        icon="image",
        max_length=500
    )

    favicon_color: str = FormField(
        "#3498db",
        title="Favicon Color",
        input_type="color",
        help_text="Color for browser favicon",
        icon="palette"
    )

    enable_animations: bool = FormField(
        True,
        title="Enable Animations",
        input_type="checkbox",
        help_text="Show animated transitions?",
        icon="play-circle"
    )

    enable_sound: bool = FormField(
        False,
        title="Enable Sound Effects",
        input_type="checkbox",
        help_text="Play sound effects?",
        icon="volume-up"
    )

    video_quality: str = FormField(
        "auto",
        title="Default Video Quality",
        input_type="select",
        options=[
            {"value": "auto", "label": "🔄 Auto"},
            {"value": "1080p", "label": "🎬 1080p (HD)"},
            {"value": "720p", "label": "📹 720p"},
            {"value": "480p", "label": "📺 480p"},
            {"value": "360p", "label": "📱 360p"}
        ],
        help_text="Preferred video playback quality",
        icon="film"
    )

    autoplay_videos: bool = FormField(
        False,
        title="Autoplay Videos",
        input_type="checkbox",
        help_text="Automatically play videos?",
        icon="play"
    )

    color_themes: List[ColorTheme] = FormField(
        default_factory=list,
        title="Color Themes",
        input_type="model_list",
        help_text="Create custom color themes",
        icon="palette2",
        min_length=0,
        max_length=10,
        model_class=ColorTheme,
        add_button_text="➕ Add Color Theme",
        remove_button_text="Remove",
        collapsible_items=True,
        items_expanded=True,
        item_title_template="🎨 {theme_name}",
        section_design={
            "section_title": "Custom Color Themes",
            "section_description": "Design your own color schemes",
            "icon": "bi bi-palette2",
            "collapsible": True,
            "collapsed": False
        }
    )

    max_upload_size_mb: int = FormField(
        10,
        title="Max Upload Size (MB)",
        input_type="range",
        help_text="Maximum file size for uploads",
        icon="cloud-upload",
        min_value=1,
        max_value=100
    )


# ============================================================================
# TAB 6: SETTINGS & PREFERENCES
# ============================================================================

class NotificationPreference(FormModel):
    """Nested notification preference model."""

    notification_type: str = FormField(
        title="Notification Type",
        input_type="select",
        options=[
            {"value": "email", "label": "📧 Email"},
            {"value": "sms", "label": "📱 SMS"},
            {"value": "push", "label": "🔔 Push Notification"},
            {"value": "in_app", "label": "💬 In-App"}
        ],
        help_text="Type of notification"
    )

    event_category: str = FormField(
        title="Event Category",
        input_type="select",
        options=[
            {"value": "security", "label": "🔒 Security Alerts"},
            {"value": "updates", "label": "📰 Product Updates"},
            {"value": "marketing", "label": "📣 Marketing"},
            {"value": "reminders", "label": "⏰ Reminders"},
            {"value": "social", "label": "👥 Social Activity"}
        ],
        help_text="What triggers this notification?"
    )

    enabled: bool = FormField(
        True,
        title="Enabled",
        input_type="checkbox",
        help_text="Receive these notifications?",
        icon="bell"
    )

    frequency: str = FormField(
        "realtime",
        title="Frequency",
        input_type="select",
        options=[
            {"value": "realtime", "label": "⚡ Real-time"},
            {"value": "hourly", "label": "🕐 Hourly Digest"},
            {"value": "daily", "label": "📅 Daily Digest"},
            {"value": "weekly", "label": "📆 Weekly Digest"}
        ],
        help_text="How often to receive notifications?"
    )


class SettingsForm(FormModel):
    """Application settings and user preferences."""

    username: str = FormField(
        title="Username",
        input_type="text",
        placeholder="johndoe",
        help_text="Your unique username",
        icon="person-badge",
        min_length=3,
        max_length=50
    )

    display_name: str = FormField(
        title="Display Name",
        input_type="text",
        placeholder="John Doe",
        help_text="Name shown to other users",
        icon="person",
        max_length=100
    )

    language: str = FormField(
        "en",
        title="Language",
        input_type="select",
        options=[
            {"value": "en", "label": "🇺🇸 English"},
            {"value": "es", "label": "🇪🇸 Español"},
            {"value": "fr", "label": "🇫🇷 Français"},
            {"value": "de", "label": "🇩🇪 Deutsch"},
            {"value": "ja", "label": "🇯🇵 日本語"},
            {"value": "zh", "label": "🇨🇳 中文"}
        ],
        help_text="Preferred language",
        icon="translate"
    )

    ui_theme: str = FormField(
        "auto",
        title="UI Theme",
        input_type="radio",
        options=[
            {"value": "light", "label": "☀️ Light"},
            {"value": "dark", "label": "🌙 Dark"},
            {"value": "auto", "label": "🔄 Auto"}
        ],
        help_text="Interface theme preference"
    )

    font_size: int = FormField(
        14,
        title="Font Size (px)",
        input_type="range",
        help_text="Adjust text size",
        icon="fonts",
        min_value=10,
        max_value=24
    )

    accessibility_mode: bool = FormField(
        False,
        title="Accessibility Mode",
        input_type="checkbox",
        help_text="Enable high-contrast and screen reader support",
        icon="universal-access"
    )

    compact_view: bool = FormField(
        False,
        title="Compact View",
        input_type="checkbox",
        help_text="Use denser layout to show more content",
        icon="layout-split"
    )

    show_tutorials: bool = FormField(
        True,
        title="Show Tutorial Tooltips",
        input_type="checkbox",
        help_text="Display helpful tips for new features",
        icon="question-circle"
    )

    auto_save: bool = FormField(
        True,
        title="Auto-Save",
        input_type="checkbox",
        help_text="Automatically save changes",
        icon="floppy"
    )

    auto_save_interval: int = FormField(
        5,
        title="Auto-Save Interval (minutes)",
        input_type="number",
        help_text="How often to auto-save",
        icon="clock",
        min_value=1,
        max_value=60
    )

    notification_preferences: List[NotificationPreference] = FormField(
        default_factory=list,
        title="Notification Preferences",
        input_type="model_list",
        help_text="Customize notification settings",
        icon="bell",
        min_length=0,
        max_length=20,
        model_class=NotificationPreference,
        add_button_text="➕ Add Notification Rule",
        remove_button_text="Remove",
        collapsible_items=True,
        items_expanded=False,
        item_title_template="🔔 {event_category} via {notification_type}",
        section_design={
            "section_title": "Notification Rules",
            "section_description": "Control how and when you receive notifications",
            "icon": "bi bi-bell",
            "collapsible": True,
            "collapsed": False
        }
    )

    two_factor_enabled: bool = FormField(
        False,
        title="Two-Factor Authentication",
        input_type="checkbox",
        help_text="Enable 2FA for enhanced security",
        icon="shield-check"
    )

    session_timeout: int = FormField(
        30,
        title="Session Timeout (minutes)",
        input_type="select",
        options=[
            {"value": 15, "label": "15 minutes"},
            {"value": 30, "label": "30 minutes"},
            {"value": 60, "label": "1 hour"},
            {"value": 120, "label": "2 hours"},
            {"value": 480, "label": "8 hours"},
            {"value": 1440, "label": "24 hours"}
        ],
        help_text="Auto-logout after inactivity",
        icon="stopwatch"
    )


# ============================================================================
# MAIN TABBED LAYOUT
# ============================================================================

class OrganizationLayout(VerticalLayout):
    """Wrapper layout for organization form."""
    form = CompanyOrganizationForm

class KitchenSinkLayout(VerticalLayout):
    """Wrapper layout for kitchen sink form."""
    form = KitchenSinkForm

class ContactsLayout(VerticalLayout):
    """Wrapper layout for contacts form."""
    form = ContactManagementForm

class SchedulingLayout(VerticalLayout):
    """Wrapper layout for scheduling form."""
    form = SchedulingForm

class MediaLayout(VerticalLayout):
    """Wrapper layout for media form."""
    form = MediaFilesForm

class SettingsLayout(VerticalLayout):
    """Wrapper layout for settings form."""
    form = SettingsForm

class ComprehensiveTabbed(TabbedLayout):
    """Main tabbed layout combining all forms."""
    organization = OrganizationLayout()
    kitchen_sink = KitchenSinkLayout()
    contacts = ContactsLayout()
    scheduling = SchedulingLayout()
    media = MediaLayout()
    settings = SettingsLayout()


class ComprehensiveTabbedForm(FormModel):
    """
    Wrapper form model containing the comprehensive tabbed layout.

    This form demonstrates:
    - 6 major tabs covering all form capabilities
    - Tab 1: Organization - 5 levels of nesting
    - Tab 2: Kitchen Sink - ALL input types
    - Tab 3: Contact Management - Nested contacts
    - Tab 4: Scheduling - Date/time management
    - Tab 5: Media & Files - Color themes and media
    - Tab 6: Settings - Preferences and notifications
    """

    comprehensive_tabs: ComprehensiveTabbed = FormField(
        default_factory=ComprehensiveTabbed,
        title="Complete Feature Showcase",
        input_type="layout",
        help_text="Explore all 6 tabs to see every feature of Pydantic SchemaForms"
    )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_sample_nested_data() -> dict:
    """Create sample data for testing deeply nested forms."""
    return {
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
                "name": "Engineering",
                "description": "Software development and infrastructure",
                "department_head": "John Doe",
                "head_email": "john.doe@techcorp.com",
                "established_date": "2010-06-01",
                "budget": 50000000.0,
                "teams": [
                    {
                        "name": "Backend Services",
                        "description": "API and database services",
                        "team_lead": "Alice Johnson",
                        "formed_date": "2015-03-01",
                        "members": [
                            {
                                "name": "Bob Wilson",
                                "email": "bob.wilson@techcorp.com",
                                "role": "Senior Backend Developer",
                                "hire_date": "2016-01-15",
                                "experience_years": 12,
                                "manager": "Alice Johnson",
                                "certifications": [
                                    {
                                        "name": "AWS Solutions Architect Professional",
                                        "issuer": "Amazon Web Services",
                                        "issue_date": "2022-05-01",
                                        "expiry_date": "2025-05-01",
                                        "credential_id": "AWS-12345",
                                        "credential_url": "https://aws.amazon.com/verification/12345"
                                    },
                                    {
                                        "name": "Certified Kubernetes Administrator",
                                        "issuer": "Cloud Native Computing Foundation",
                                        "issue_date": "2023-01-15",
                                        "expiry_date": "2026-01-15",
                                        "credential_id": "CKA-67890",
                                        "credential_url": "https://cncf.io/verify/67890"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "projects": [
                    {
                        "name": "Microservices Migration",
                        "description": "Migrate monolithic application to microservices architecture",
                        "status": "in_progress",
                        "start_date": "2024-01-01",
                        "target_end_date": "2024-12-31",
                        "budget": 2000000.0,
                        "project_manager": "Carol Lee",
                        "tasks": [
                            {
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


def create_comprehensive_sample_data() -> dict:
    """Create comprehensive sample data for all tabs."""
    from datetime import datetime

    return {
        # Tab 1: Organization (reuse existing nested data)
        "organization": create_sample_nested_data(),

        # Tab 2: Kitchen Sink (all input types with sample values)
        "kitchen_sink": {
            "text_input": "Sample text value",
            "email_input": "user@example.com",
            "password_input": "SecurePass123!",
            "search_input": "search query",
            "url_input": "https://example.com",
            "tel_input": "+1-555-987-6543",
            "textarea_input": "This is a multi-line\ntext area\nwith sample content.",
            "number_input": 42,
            "decimal_input": 3.14159,
            "range_input": 75,
            "select_input": "option3",
            "radio_input": "large",
            "multiselect_input": ["python", "typescript", "rust"],
            "checkbox_input": True,
            "toggle_input": False,
            "date_input": "2024-06-15",
            "time_input": "14:30",
            "datetime_input": datetime(2024, 6, 15, 14, 30).isoformat(),
            "color_input": "#e74c3c",
            "hidden_input": "hidden_secret_value"
        },

        # Tab 3: Contact Management
        "contacts": {
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "company": "Acme Corporation",
            "job_title": "Senior Software Engineer",
            "birth_date": "1985-04-12",
            "phone_numbers": [
                {
                    "phone_type": "mobile",
                    "number": "+1 (555) 123-4567",
                    "is_primary": True
                },
                {
                    "phone_type": "work",
                    "number": "+1 (555) 987-6543",
                    "is_primary": False
                }
            ],
            "addresses": [
                {
                    "address_type": "home",
                    "street_line1": "123 Main Street",
                    "street_line2": "Apt 4B",
                    "city": "San Francisco",
                    "state": "CA",
                    "postal_code": "94105",
                    "country": "US"
                },
                {
                    "address_type": "work",
                    "street_line1": "456 Corporate Blvd",
                    "street_line2": "Suite 200",
                    "city": "Palo Alto",
                    "state": "CA",
                    "postal_code": "94301",
                    "country": "US"
                }
            ],
            "notes": "Prefers email communication. Available Monday-Friday 9am-5pm PST."
        },

        # Tab 4: Scheduling
        "scheduling": {
            "calendar_name": "Work Calendar",
            "timezone": "America/Los_Angeles",
            "default_event_duration": 60,
            "work_start_time": "09:00",
            "work_end_time": "17:00",
            "weekend_days": ["saturday", "sunday"],
            "recurring_events": [
                {
                    "event_name": "Weekly Team Standup",
                    "event_type": "meeting",
                    "start_date": "2024-01-08",
                    "start_time": "10:00",
                    "duration_minutes": 30,
                    "recurrence_pattern": "weekly",
                    "end_date": "2024-12-31",
                    "location": "Conference Room A",
                    "send_reminder": True
                },
                {
                    "event_name": "Monthly All Hands",
                    "event_type": "meeting",
                    "start_date": "2024-01-15",
                    "start_time": "14:00",
                    "duration_minutes": 90,
                    "recurrence_pattern": "monthly",
                    "end_date": None,
                    "location": "Main Auditorium",
                    "send_reminder": True
                }
            ]
        },

        # Tab 5: Media & Files
        "media": {
            "profile_picture_url": "https://example.com/avatars/user123.jpg",
            "background_image_url": "https://example.com/backgrounds/abstract.jpg",
            "favicon_color": "#3498db",
            "enable_animations": True,
            "enable_sound": False,
            "video_quality": "1080p",
            "autoplay_videos": False,
            "color_themes": [
                {
                    "theme_name": "Ocean Blue",
                    "primary_color": "#3498db",
                    "secondary_color": "#2ecc71",
                    "accent_color": "#e74c3c",
                    "background_color": "#ffffff",
                    "text_color": "#2c3e50",
                    "is_default": True
                },
                {
                    "theme_name": "Dark Mode",
                    "primary_color": "#1a1a1a",
                    "secondary_color": "#34495e",
                    "accent_color": "#f39c12",
                    "background_color": "#0a0a0a",
                    "text_color": "#ecf0f1",
                    "is_default": False
                }
            ],
            "max_upload_size_mb": 25
        },

        # Tab 6: Settings
        "settings": {
            "username": "jsmith",
            "display_name": "John Smith",
            "language": "en",
            "ui_theme": "auto",
            "font_size": 16,
            "accessibility_mode": False,
            "compact_view": False,
            "show_tutorials": True,
            "auto_save": True,
            "auto_save_interval": 5,
            "notification_preferences": [
                {
                    "notification_type": "email",
                    "event_category": "security",
                    "enabled": True,
                    "frequency": "realtime"
                },
                {
                    "notification_type": "push",
                    "event_category": "updates",
                    "enabled": True,
                    "frequency": "daily"
                },
                {
                    "notification_type": "email",
                    "event_category": "marketing",
                    "enabled": False,
                    "frequency": "weekly"
                }
            ],
            "two_factor_enabled": True,
            "session_timeout": 60
        }
    }


if __name__ == "__main__":
    # Test the models
    print("Testing deeply nested form models...")

    try:
        # Create sample data
        sample_data = create_sample_nested_data()

        # Validate the data against the form model
        form = CompanyOrganizationForm(**sample_data)

        print("✅ Form validation successful!")
        print(f"Company: {form.company_name}")
        print(f"Departments: {len(form.departments)}")
        if form.departments:
            dept = form.departments[0]
            print(f"  First Department: {dept.name}")
            print(f"    Teams: {len(dept.teams)}")
            if dept.teams:
                team = dept.teams[0]
                print(f"      First Team: {team.name}")
                print(f"        Members: {len(team.members)}")
                if team.members:
                    member = team.members[0]
                    print(f"          First Member: {member.name}")
                    print(f"            Certifications: {len(member.certifications)}")
            print(f"    Projects: {len(dept.projects)}")
            if dept.projects:
                proj = dept.projects[0]
                print(f"      First Project: {proj.name}")
                print(f"        Tasks: {len(proj.tasks)}")
                if proj.tasks:
                    task = proj.tasks[0]
                    print(f"          First Task: {task.title}")
                    print(f"            Subtasks: {len(task.subtasks)}")

        print("\n📊 Nesting depth verification:")
        print("  Level 1: Company")
        print("  Level 2: Departments")
        print("  Level 3: Teams & Projects")
        print("  Level 4: Team Members & Tasks")
        print("  Level 5: Certifications & Subtasks")
        print("\n✨ This form successfully demonstrates 5 levels of nesting!")

    except Exception as e:
        print(f"❌ Validation error: {e}")
