#!/usr/bin/env python3
"""
Nested Forms Example - Stress Test
===================================

This example pushes the Pydantic SchemaForms library past normal use cases
by creating deeply nested forms (forms within forms within forms).

It demonstrates:
- Multiple levels of nesting
- Complex hierarchical data structures
- All input types across nested levels
- Validation cascading through nested models
- Large nested lists with collapsible items

Hierarchy:
1. Company Form (Level 1)
   └─ Departments (Level 2)
      ├─ Teams (Level 3)
      │  └─ Team Members (Level 4)
      │     └─ Certifications (Level 5)
      └─ Projects (Level 3)
         └─ Tasks (Level 4)
            └─ Subtasks (Level 5)

This tests the library's ability to handle deep nesting, large lists,
and complex form hierarchies that go beyond typical form use cases.
"""

import os
import sys
from datetime import date
from enum import Enum
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

    layout_demo: DepartmentInsightsTabbed = FormField(
        DepartmentInsightsTabbed(),
        title="Department Insights (Layout Demo)",
        input_type="layout",
        help_text="Tabbed layout demo embedded in the complex organization form"
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
                                        "expiry_date": None,
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
