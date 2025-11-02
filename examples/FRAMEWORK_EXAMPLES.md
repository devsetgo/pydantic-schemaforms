# Framework Examples - Simple is Better

## Philosophy: "Simple is Better"

Following Python's principle of simplicity, pydantic-forms framework examples demonstrate that users only need **three simple steps**:

1. **Create** form models in `shared_models.py`
2. **Render** with `render_form_html()`
3. **Validate** with `handle_form_submission()`

**No local FormModel definitions. No complex imports. No pydantic-forms internals.**

## The Three-Step Pattern

### Step 1: Import Shared Models
```python
from shared_models import UserRegistrationForm, PetRegistrationForm
```

### Step 2: Render Forms  
```python
from pydantic_forms.enhanced_renderer import render_form_html

# Bootstrap styling
form_html = render_form_html(UserRegistrationForm, framework='bootstrap')

# Material Design styling  
form_html = render_form_html(UserRegistrationForm, framework='material')
```

### Step 3: Validate Forms
```python
from shared_models import handle_form_submission

result = handle_form_submission(UserRegistrationForm, form_data)
if result['success']:
    # Handle success
    data = result['data']
else:
    # Handle validation errors
    errors = result['errors']
```

That's it! **Simple is better.**

## Architecture

### Shared Models (`shared_models.py`)
- **Single Source of Truth**: All form models are defined in `examples/shared_models.py`
- **Framework Independent**: Models use semantic icon names that work across all UI frameworks
- **Comprehensive**: Includes all form types from simple login to complex showcase forms

### Framework Examples
Each framework example (`flask_example.py`, `fastapi_example.py`, etc.) follows the simple three-step pattern:

```python
# Step 1: Import shared models (no local definitions!)
from shared_models import (
    UserRegistrationForm, PetRegistrationForm, CompleteShowcaseForm
)

# Step 2: Import rendering function (only what you need!)
from pydantic_forms.enhanced_renderer import render_form_html

# Step 3: Render forms with one simple call
def user_form(style="bootstrap"):
    form_html = render_form_html(UserRegistrationForm, framework=style)
    return render_template("user.html", form_html=form_html)

# Step 4: Validate with one simple call  
def user_post(form_data):
    result = handle_form_submission(UserRegistrationForm, form_data)
    return handle_result(result)
```

**No FormModel imports. No FormField usage. No complexity leakage.**

## Available Models

### Basic Forms
- `MinimalLoginForm` - Simple username/password login
- `UserRegistrationForm` - User registration with validation
- `MediumContactForm` - Contact form with multiple field types

### Advanced Forms  
- `PetRegistrationForm` - Complex form with owner info + dynamic pet list
- `CompleteShowcaseForm` - Comprehensive showcase of all input types and features

### Component Models
- `PetModel` - Individual pet information with all input types
- `EmergencyContactModel` - Emergency contact with relationship selection

## Icon System

### Semantic Icons
All models use semantic icon names that automatically map to framework-specific icons:

```python
username: str = FormField(
    icon="person",  # Maps to "bi bi-person" (Bootstrap) or "person" (Material)
    # ... other config
)
```

### Supported Mappings
- `person` → `bi bi-person` (Bootstrap) / `person` (Material)
- `email` → `bi bi-envelope` (Bootstrap) / `email` (Material) 
- `lock` → `bi bi-lock` (Bootstrap) / `lock` (Material)
- `calendar` → `bi bi-calendar` (Bootstrap) / `calendar_today` (Material)
- `shield` → `bi bi-shield` (Bootstrap) / `shield` (Material)

## Framework Support

### Current Examples
- ✅ **Flask** (`flask_example.py`) - Uses shared models, render_form_html
- ✅ **FastAPI** (`fastapi_example.py`) - Uses shared models, render_form_html

### Future Framework Examples

#### Litestar Example (`litestar_example.py`)
```python
from litestar import Litestar, get, post
from shared_models import UserRegistrationForm, PetRegistrationForm
from pydantic_forms.enhanced_renderer import render_form_html

@get("/user")
async def user_form(style: str = "bootstrap") -> str:
    form_html = render_form_html(UserRegistrationForm, framework=style)
    return render_template("user.html", form_html=form_html)
```

#### Robyn Example (`robyn_example.py`)
```python
from robyn import Robyn
from shared_models import UserRegistrationForm, PetRegistrationForm  
from pydantic_forms.enhanced_renderer import render_form_html

app = Robyn(__file__)

@app.get("/user")
async def user_form(request):
    style = request.query_params.get("style", "bootstrap")
    form_html = render_form_html(UserRegistrationForm, framework=style)
    return render_template("user.html", form_html=form_html)
```

## Benefits

### 🎯 **Consistency**
- Identical forms across all frameworks
- Same validation rules and field configurations
- Consistent icon usage and styling

### 🚀 **Maintainability** 
- Single place to update form definitions
- No duplicate model definitions
- Easy to add new fields or validation

### 🔧 **Extensibility**
- Simple to add new framework examples
- Framework-specific customization only where needed
- Icon mapping system handles UI differences automatically

### 🧪 **Testing**
- Shared test suite validates model consistency
- Framework examples can focus on framework-specific concerns
- Easy to verify cross-framework compatibility

## Adding New Framework Examples

To add a new framework example:

1. **Create framework file** (e.g., `litestar_example.py`)
2. **Import shared models**:
   ```python
   from shared_models import UserRegistrationForm, PetRegistrationForm, etc.
   ```
3. **Use render_form_html**:
   ```python
   form_html = render_form_html(FormClass, framework=style)
   ```
4. **Follow framework patterns** for routing, templates, etc.
5. **Test with model consistency suite**:
   ```bash
   python test_model_consistency.py
   ```

## Template Compatibility

All framework examples share the same templates in `examples/templates/`:
- `user.html` - User registration form template
- `pets.html` - Pet registration form template  
- `showcase.html` - Complete showcase template
- `home.html` - Landing page template

Templates are framework-agnostic and work with Flask, FastAPI, and future frameworks.

## Conclusion

This shared models architecture provides:
- ✅ **Consistency** across all framework examples
- ✅ **Easy maintenance** with single source of truth
- ✅ **Simple extension** for new frameworks
- ✅ **Icon mapping** that works across UI frameworks
- ✅ **Template reuse** across all examples

Ready for Litestar, Robyn, and any future framework examples! 🚀