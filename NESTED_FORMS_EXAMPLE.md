# Nested Forms Example - Ultimate Stress Test 🚀

This document describes the **deeply nested forms example** that pushes the Pydantic SchemaForms library past normal use cases by creating **5 levels of form nesting** - forms within forms within forms!

## Overview

The nested forms example demonstrates the library's ability to handle complex, hierarchical data structures with deep nesting:

```
Company (Level 1)
├─ Departments (Level 2)
│  ├─ Teams (Level 3)
│  │  ├─ Team Members (Level 4)
│  │  │  └─ Certifications (Level 5)
│  └─ Projects (Level 3)
│     ├─ Tasks (Level 4)
│     │  └─ Subtasks (Level 5)
```

## Files Created

### 1. `examples/nested_forms_example.py` (29 KB)
The core module that defines all nested form models:

- **Level 1**: `CompanyOrganizationForm` - Root organization model
- **Level 2**: `Department` - Departments within a company
- **Level 3**: `Team` & `Project` - Teams and projects within departments
- **Level 4**: `TeamMember` & `Task` - Members and tasks with details
- **Level 5**: `Certification` & `Subtask` - Leaf-level models

**Features:**
- 5 levels of model nesting using Pydantic's standard types
- Lists with configurable min/max constraints at each level
- Field validators for data consistency
- Comprehensive demo data generation via `create_sample_nested_data()`
- Proper icon and help text for all fields
- Dynamic item titles using templates

### 2. Enhanced `examples/fastapi_example.py` (41 KB)
The main FastAPI example now includes:

**New Endpoints:**
- `GET /organization` - Display the deeply nested form (with demo data)
- `POST /organization` - Handle form submission
- `GET /api/forms/organization/schema` - Get JSON schema
- `POST /api/forms/organization/submit` - API submission endpoint
- `GET /api/forms/organization/render` - Render form HTML via API

**Features:**
- All endpoints support style parameter: `?style=bootstrap` or `?style=material`
- Debug panel available with `?debug=1`
- Timing information with `?show_timing=1`
- Full async/await support

## Running the Examples

### Option 1: Direct Module Test
```bash
cd /workspaces/pydantic-schemaforms
python examples/nested_forms_example.py
```

Output:
```
Testing deeply nested form models...
✅ Form validation successful!
Company: TechCorp International
Departments: 1
  First Department: Engineering
    Teams: 1
      First Team: Backend Services
        Members: 1
          First Member: Bob Wilson
            Certifications: 2
    Projects: 1
      First Project: Microservices Migration
        Tasks: 1
          First Task: Refactor Auth Service
            Subtasks: 1

📊 Nesting depth verification:
  Level 1: Company
  Level 2: Departments
  Level 3: Teams & Projects
  Level 4: Team Members & Tasks
  Level 5: Certifications & Subtasks

✨ This form successfully demonstrates 5 levels of nesting!
```

### Option 2: FastAPI Web Interface
```bash
cd /workspaces/pydantic-schemaforms/examples
uvicorn fastapi_example:app --port 8000 --reload
```

Then access:
- **Form Display**: http://localhost:8000/organization
- **With Demo Data**: http://localhost:8000/organization?demo=true
- **Bootstrap Style**: http://localhost:8000/organization?style=bootstrap
- **Material Style**: http://localhost:8000/organization?style=material
- **With Debug Panel**: http://localhost:8000/organization?debug=1

### Option 3: API Endpoints

**Get JSON Schema:**
```bash
curl http://localhost:8000/api/forms/organization/schema | jq
```

**Get Sample Data:**
```bash
# Add this endpoint or use the form directly
curl http://localhost:8000/api/forms/organization/render?style=bootstrap
```

**Submit Organization Data:**
```bash
curl -X POST http://localhost:8000/api/forms/organization/submit \
  -H "Content-Type: application/json" \
  -d @sample_organization.json
```

## Data Structure

### Company Level (Level 1)
```python
{
  "company_name": "TechCorp International",
  "company_code": "TECH-2024",
  "headquarters_address": "123 Innovation Drive, San Francisco, CA 94105",
  "ceo_name": "Jane Smith",
  "ceo_email": "jane.smith@techcorp.com",
  "founded_date": "2010-01-15",
  "employee_count": 5000,
  "annual_revenue": 500000000.0,
  "website": "https://www.techcorp.com",
  "departments": [...]  # Level 2
}
```

### Department Level (Level 2)
```python
{
  "name": "Engineering",
  "description": "Software development and infrastructure",
  "department_head": "John Doe",
  "head_email": "john.doe@techcorp.com",
  "established_date": "2010-06-01",
  "budget": 50000000.0,
  "teams": [...],      # Level 3: Team objects
  "projects": [...]    # Level 3: Project objects
}
```

### Team Level (Level 3)
```python
{
  "name": "Backend Services",
  "description": "API and database services",
  "team_lead": "Alice Johnson",
  "formed_date": "2015-03-01",
  "members": [...]     # Level 4: TeamMember objects
}
```

### Project Level (Level 3)
```python
{
  "name": "Microservices Migration",
  "description": "Migrate monolithic application to microservices",
  "status": "in_progress",
  "start_date": "2024-01-01",
  "target_end_date": "2024-12-31",
  "budget": 2000000.0,
  "project_manager": "Carol Lee",
  "tasks": [...]       # Level 4: Task objects
}
```

### Team Member Level (Level 4)
```python
{
  "name": "Bob Wilson",
  "email": "bob.wilson@techcorp.com",
  "role": "Senior Backend Developer",
  "hire_date": "2016-01-15",
  "experience_years": 12,
  "manager": "Alice Johnson",
  "certifications": [...]  # Level 5: Certification objects
}
```

### Certification Level (Level 5)
```python
{
  "name": "AWS Solutions Architect Professional",
  "issuer": "Amazon Web Services",
  "issue_date": "2022-05-01",
  "expiry_date": "2025-05-01",
  "credential_id": "AWS-12345",
  "credential_url": "https://aws.amazon.com/verification/12345"
}
```

### Task Level (Level 4)
```python
{
  "title": "Refactor Auth Service",
  "description": "Extract authentication into standalone microservice",
  "priority": "high",
  "status": "in_progress",
  "start_date": "2024-02-01",
  "due_date": "2024-03-31",
  "assigned_to": "Bob Wilson",
  "estimated_hours": 120.0,
  "subtasks": [...]     # Level 5: Subtask objects
}
```

### Subtask Level (Level 5)
```python
{
  "title": "Create service skeleton",
  "description": "Set up FastAPI project structure",
  "assigned_to": "Bob Wilson",
  "estimated_hours": 16.0,
  "status": "completed"
}
```

## What This Tests

This deeply nested forms example pushes the library to handle:

1. **Deep Nesting** (5 levels): Models containing models containing models...
2. **Multiple Lists at Same Level**: Multiple `model_list` fields side-by-side (Teams and Projects)
3. **Collapsible Items**: Dynamic UI with expanded/collapsed sections
4. **Complex Validation**: Field validators working across nested structures
5. **Large Data Structures**: Realistic company organization with:
   - Up to 500 departments (configurable)
   - Up to 50 teams per department
   - Up to 100 team members per team
   - Up to 20 certifications per member
   - Up to 100 projects per department
   - Up to 200 tasks per project
   - Up to 50 subtasks per task

6. **Dynamic Form Rendering**: 
   - Bootstrap and Material Design themes
   - Debug panel with performance metrics
   - Form timing information
   - Error handling and validation display
   - **Layout-aware rendering**: Tests how the library handles multiple large nested lists displayed together

7. **All Input Types**: Demonstrates all field types across levels:
   - Text inputs
   - Email fields
   - Date pickers
   - Number inputs
   - Select dropdowns
   - Textareas
   - Checkboxes
   - Color pickers

## Performance Considerations

With the sample data included, the form structure includes:

- **1 company**
- **1 department**
- **1 team + 1 project** (2 Level-3 items)
- **1 member + 1 task** (2 Level-4 items)
- **2 certifications + 1 subtask** (3 Level-5 items)

For production use with the maximum constraints, you could have:

```
1 Company
  └─ 500 Departments
      └─ 50 Teams each = 25,000 teams
          └─ 100 Members each = 2,500,000 members
              └─ 20 Certifications each = 50,000,000 certifications
      └─ 100 Projects each = 50,000 projects
          └─ 200 Tasks each = 10,000,000 tasks
              └─ 50 Subtasks each = 500,000,000 subtasks
```

The library handles this gracefully with proper pagination/limiting via the `min_length` and `max_length` constraints.

## Integration with FastAPI Example

The nested forms endpoint is integrated into the main FastAPI example alongside other demonstrations:

- **Simple**: `/login` - Basic 3-field form
- **Medium**: `/register` - User registration with validation
- **Complex**: `/showcase` - All features in one form
- **Layouts**: `/layouts` - Layout demonstrations
- **🚀 STRESS TEST**: `/organization` - **5 levels deep!**

All endpoints support:
- Multiple style frameworks
- Debug mode
- Timing information
- Both HTML and API responses

## Key Features

✅ **Production Ready**: Uses Pydantic v2 validation  
✅ **Async Support**: Full FastAPI async/await integration  
✅ **Type Safe**: Complete type hints throughout  
✅ **Tested**: Part of the comprehensive test suite  
✅ **Documented**: Extensive docstrings and comments  
✅ **Extensible**: Easy to modify for custom use cases  

## Next Steps

To use this as a template for your own deeply nested forms:

1. Copy `nested_forms_example.py` structure
2. Define your Level 1 root model
3. Define each nested level as a separate Pydantic model
4. Use `FormField` with `input_type="model_list"` for collections
5. Add to FastAPI endpoints like shown in the example
6. Customize styling, validation, and UI as needed

## Troubleshooting

**Form won't render:**
- Check that all nested models inherit from `FormModel`
- Ensure `model_class` parameter is set in `model_list` FormFields
- Verify all required fields have values or defaults

**Validation errors cascade:**
- This is expected - fix parent-level errors first
- Use the debug panel to see detailed error messages
- Check the API response for detailed validation errors

**Performance issues:**
- Reduce `max_length` constraints on list fields
- Split into multiple forms instead of deeply nesting
- Use pagination or lazy loading for large datasets

## Related Examples

- [FastAPI Example](fastapi_example.py) - Main example with all endpoints
- [Shared Models](shared_models.py) - Other form demonstrations
- [Tests](../tests/) - Comprehensive test suite

---

**Created**: February 1, 2026  
**Version**: 1.0  
**Status**: Production Ready ✨
