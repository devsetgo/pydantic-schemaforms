#!/usr/bin/env python3
"""
Test model list functionality
"""

from typing import List
from pydantic_forms import FormModel, FormField
from pydantic_forms.render_form import render_form_html

class PetModel(FormModel):
    """Pet information."""
    name: str = FormField(
        title="Pet Name",
        input_type="text",
        placeholder="Enter pet name"
    )
    species: str = FormField(
        title="Species", 
        input_type="text",
        placeholder="dog, cat, fish, etc."
    )

class TestForm(FormModel):
    """Test form with model list."""
    pets: List[PetModel] = FormField(
        default_factory=list,
        title="Your Pets",
        input_type="model_list",
        model_class=PetModel,
        help_text="Add your pets",
        min_items=0,
        max_items=5
    )

if __name__ == "__main__":
    # First, let's check the schema structure
    schema = TestForm.model_json_schema()
    print("Schema structure:")
    print("=" * 50)
    import json
    print(json.dumps(schema, indent=2))
    print("=" * 50)
    
    form_html = render_form_html(TestForm, framework="bootstrap")
    
    print("Generated HTML:")
    print("=" * 50)
    print(form_html)
    print("=" * 50)
    
    # Save to file for viewing
    with open("/workspaces/pydantic-forms/test_model_list.html", "w") as f:
        f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Model List Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>Model List Test</h1>
        {form_html}
    </div>
</body>
</html>
        """)
    
    print("Test HTML saved to: /workspaces/pydantic-forms/test_model_list.html")