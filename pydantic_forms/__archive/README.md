# Archived Pydantic Forms Modules

This directory contains modules that have been archived because they were superseded by newer, better implementations. These files are kept for historical reference and to understand the evolution of the library.

## Archived Modules

### `ui_elements.py` 
**Superseded by:** `inputs/` directory structure  
**Reason:** The monolithic ui_elements.py was replaced by a well-organized modular input system with separate files for different input categories (text_inputs.py, numeric_inputs.py, etc.).

### `form_layout.py`
**Superseded by:** `layouts.py`  
**Reason:** The form_layout.py had a basic implementation that was replaced by a more comprehensive layout system with better Python 3.14 template string support and more layout options.

### `form_model.py`
**Superseded by:** `schema_form.py`  
**Reason:** The form_model.py was replaced by schema_form.py which provides better FormModel integration with enhanced Field() function supporting React JSON Schema Forms compatible UI parameters.

### `form_renderer.py`
**Superseded by:** `enhanced_renderer.py` and `modern_renderer.py`  
**Reason:** The basic form_renderer.py was replaced by more advanced renderers that support multiple frameworks, better error handling, and modern Python 3.14 template strings.

### `template_compat.py`
**Superseded by:** Direct Python 3.14 template string usage  
**Reason:** This file was empty and no longer needed with proper template string implementation throughout the codebase.

## Migration Guide

If you were using any of these archived modules, here's how to migrate:

### From `ui_elements` to `inputs/`
```python
# OLD
from pydantic_forms.ui_elements import TextInput, EmailInput

# NEW  
from pydantic_forms.inputs import TextInput, EmailInput
```

### From `form_layout` to `layouts`
```python
# OLD
from pydantic_forms.form_layout import HorizontalLayout

# NEW
from pydantic_forms.layouts import HorizontalLayout
```

### From `form_model` to `schema_form`
```python
# OLD
from pydantic_forms.form_model import FormModel

# NEW
from pydantic_forms.schema_form import FormModel, Field
```

### From `form_renderer` to `enhanced_renderer`
```python
# OLD
from pydantic_forms.form_renderer import FormRenderer

# NEW
from pydantic_forms.enhanced_renderer import EnhancedFormRenderer
# or
from pydantic_forms.modern_renderer import ModernFormRenderer
```

## Archive Date
October 19, 2025

## Notes
These modules were archived as part of the library reorganization and cleanup. The new implementations provide better functionality, cleaner APIs, and full React JSON Schema Forms compatibility.