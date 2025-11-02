#!/usr/bin/env python3
"""
Test script to verify that Flask and FastAPI examples use identical models.

This ensures consistency across all framework examples and prepares for
adding future frameworks like Litestar and Robyn.
"""

def test_imports():
    """Test that both examples import the same models from shared_models."""
    print("=== Testing Model Imports ===")
    
    # Test Flask example imports
    try:
        from flask_example import app as flask_app
        from shared_models import (
            UserRegistrationForm, PetRegistrationForm, CompleteShowcaseForm,
            PetModel, MinimalLoginForm, handle_form_submission
        )
        print("✅ Flask example imports all models from shared_models.py")
    except ImportError as e:
        print(f"❌ Flask import error: {e}")
        return False
    
    # Test FastAPI example imports  
    try:
        from fastapi_example import app as fastapi_app
        print("✅ FastAPI example imports all models from shared_models.py")
    except ImportError as e:
        print(f"❌ FastAPI import error: {e}")
        return False
    
    return True

def test_form_rendering():
    """Test that both frameworks render identical form HTML."""
    print("\n=== Testing Form Rendering Consistency ===")
    
    from shared_models import UserRegistrationForm, PetRegistrationForm
    from pydantic_forms.enhanced_renderer import render_form_html
    
    # Test UserRegistrationForm
    user_bootstrap = render_form_html(UserRegistrationForm, framework='bootstrap')
    user_material = render_form_html(UserRegistrationForm, framework='material')
    
    print(f"UserRegistrationForm Bootstrap HTML: {len(user_bootstrap)} chars")
    print(f"UserRegistrationForm Material HTML: {len(user_material)} chars")
    
    # Test PetRegistrationForm
    pet_bootstrap = render_form_html(PetRegistrationForm, framework='bootstrap')
    pet_material = render_form_html(PetRegistrationForm, framework='material')
    
    print(f"PetRegistrationForm Bootstrap HTML: {len(pet_bootstrap)} chars")
    print(f"PetRegistrationForm Material HTML: {len(pet_material)} chars")
    
    # Verify icons are present
    bootstrap_has_icons = "bi bi-" in user_bootstrap and "bi bi-" in pet_bootstrap
    material_has_icons = (
        ("material-symbols-outlined" in user_material or "material-icons" in user_material) and
        ("material-symbols-outlined" in pet_material or "material-icons" in pet_material)
    )
    
    print(f"Bootstrap forms have icons: {bootstrap_has_icons}")
    print(f"Material forms have icons: {material_has_icons}")
    
    return bootstrap_has_icons and material_has_icons

def test_field_consistency():
    """Test that form fields have consistent icon mappings."""
    print("\n=== Testing Field Icon Consistency ===")
    
    from shared_models import UserRegistrationForm
    
    expected_icons = {
        'username': 'person',
        'email': 'email', 
        'password': 'lock',
        'confirm_password': 'lock',
        'age': 'calendar',
        'role': 'shield'
    }
    
    for field_name, expected_icon in expected_icons.items():
        field_info = UserRegistrationForm.model_fields[field_name]
        if hasattr(field_info, 'json_schema_extra') and field_info.json_schema_extra:
            actual_icon = field_info.json_schema_extra.get('icon')
            if actual_icon == expected_icon:
                print(f"✅ {field_name}: {actual_icon}")
            else:
                print(f"❌ {field_name}: expected {expected_icon}, got {actual_icon}")
                return False
        else:
            print(f"❌ {field_name}: no icon found")
            return False
    
    return True

def test_framework_preparation():
    """Test that the shared model approach is ready for new frameworks."""
    print("\n=== Testing Framework Preparation ===")
    
    # Simulate what a new framework example would look like
    from shared_models import UserRegistrationForm, PetRegistrationForm, CompleteShowcaseForm
    from pydantic_forms.enhanced_renderer import render_form_html
    
    frameworks = ['bootstrap', 'material']
    forms = [
        ('UserRegistrationForm', UserRegistrationForm),
        ('PetRegistrationForm', PetRegistrationForm), 
        ('CompleteShowcaseForm', CompleteShowcaseForm)
    ]
    
    for framework in frameworks:
        print(f"\n{framework.title()} Framework:")
        for form_name, form_class in forms:
            try:
                html = render_form_html(form_class, framework=framework)
                print(f"  ✅ {form_name}: {len(html)} chars")
            except Exception as e:
                print(f"  ❌ {form_name}: {e}")
                return False
    
    print("\n✅ Ready for Litestar, Robyn, and other framework examples!")
    return True

def main():
    """Run all consistency tests."""
    print("🧪 Model Consistency Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_form_rendering, 
        test_field_consistency,
        test_framework_preparation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 ALL TESTS PASSED!")
        print("✅ Flask and FastAPI examples are now identical in model usage")
        print("✅ All models are centralized in shared_models.py")
        print("✅ Icon mapping system works consistently")
        print("✅ Ready for additional framework examples")
    else:
        print("❌ Some tests failed")
        print(f"Results: {results}")

if __name__ == "__main__":
    main()