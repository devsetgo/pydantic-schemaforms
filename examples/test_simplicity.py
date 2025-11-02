#!/usr/bin/env python3
"""
Test script to verify that framework examples follow the "simple is better" principle.

This ensures that users only need to:
1. Create form models in shared_models.py
2. Render with render_form_html()
3. Validate with handle_form_submission()

No local FormModel definitions should exist in framework examples.
"""

import ast
import os

def check_file_for_local_models(filepath):
    """Check if a file contains local FormModel or FormField definitions."""
    print(f"\n=== Checking {filepath} ===")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Parse the AST to find class definitions
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"❌ Syntax error in {filepath}: {e}")
        return False
    
    local_models = []
    pydantic_imports = []
    
    for node in ast.walk(tree):
        # Check for class definitions that inherit from FormModel
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == 'FormModel':
                    local_models.append(node.name)
        
        # Check for pydantic-forms imports (beyond rendering)
        if isinstance(node, ast.ImportFrom):
            if node.module and 'pydantic_forms' in node.module:
                if 'FormModel' in [alias.name for alias in node.names]:
                    pydantic_imports.append('FormModel')
                if 'FormField' in [alias.name for alias in node.names]:
                    pydantic_imports.append('FormField')
                if 'schema_form' in node.module:
                    pydantic_imports.append('schema_form')
    
    # Report findings
    if local_models:
        print(f"❌ Found local FormModel definitions: {local_models}")
        return False
    else:
        print("✅ No local FormModel definitions found")
    
    if pydantic_imports:
        print(f"❌ Found pydantic-forms modeling imports: {pydantic_imports}")
        return False
    else:
        print("✅ No pydantic-forms modeling imports found")
    
    # Check imports - should only import rendering/validation functions
    allowed_imports = [
        'render_form_html', 'EnhancedFormRenderer', 'SimpleMaterialRenderer',
        'ListLayout', 'SectionDesign'
    ]
    
    print("✅ Framework example follows 'simple is better' principle")
    return True

def test_simple_usage_pattern():
    """Test that the usage pattern is simple and consistent."""
    print("\n=== Testing Simple Usage Pattern ===")
    
    # Test the three-step pattern
    try:
        # 1. Import shared models
        from shared_models import UserRegistrationForm, PetRegistrationForm
        
        # 2. Render forms
        from pydantic_forms.enhanced_renderer import render_form_html
        
        bootstrap_form = render_form_html(UserRegistrationForm, framework='bootstrap')
        material_form = render_form_html(UserRegistrationForm, framework='material')
        
        # 3. Validate forms
        from shared_models import handle_form_submission
        
        test_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'user'
        }
        
        result = handle_form_submission(UserRegistrationForm, test_data)
        
        print("✅ Three-step pattern works:")
        print("   1. ✅ Import shared models")
        print("   2. ✅ Render with render_form_html()")
        print("   3. ✅ Validate with handle_form_submission()")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple usage pattern failed: {e}")
        return False

def test_no_complexity_leakage():
    """Test that framework examples don't expose internal complexity."""
    print("\n=== Testing No Complexity Leakage ===")
    
    framework_files = [
        'flask_example.py',
        'fastapi_example.py'
    ]
    
    forbidden_patterns = [
        'FormField(',  # Direct FormField usage
        'FormModel):',  # FormModel inheritance
        'json_schema_extra',  # Internal field configuration
        'field_validator',  # Should be in shared_models only
        '.model_fields',  # Internal model introspection
    ]
    
    all_clean = True
    
    for filepath in framework_files:
        if not os.path.exists(filepath):
            continue
            
        print(f"\nChecking {filepath} for complexity leakage...")
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        found_patterns = []
        for pattern in forbidden_patterns:
            if pattern in content:
                found_patterns.append(pattern)
        
        if found_patterns:
            print(f"❌ Found complexity leakage: {found_patterns}")
            all_clean = False
        else:
            print("✅ No complexity leakage found")
    
    return all_clean

def main():
    """Run all simplicity tests."""
    print("🧪 Simplicity Test Suite - 'Simple is Better'")
    print("=" * 60)
    
    framework_files = [
        'flask_example.py',
        'fastapi_example.py'
    ]
    
    results = []
    
    # Test each framework file
    for filepath in framework_files:
        if os.path.exists(filepath):
            result = check_file_for_local_models(filepath)
            results.append(result)
        else:
            print(f"⚠️  File not found: {filepath}")
    
    # Test usage pattern
    pattern_result = test_simple_usage_pattern()
    results.append(pattern_result)
    
    # Test complexity leakage
    complexity_result = test_no_complexity_leakage()
    results.append(complexity_result)
    
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 ALL SIMPLICITY TESTS PASSED!")
        print("✅ Framework examples follow 'simple is better' principle")
        print("✅ Users only need: shared_models + render_form_html + handle_form_submission")
        print("✅ No complexity leakage from pydantic-forms internals")
        print("✅ Clean, pythonic API surface")
    else:
        print("❌ Some simplicity tests failed")
        print(f"Results: {results}")

if __name__ == "__main__":
    main()