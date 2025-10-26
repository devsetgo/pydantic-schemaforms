# Pydantic Forms Examples

This directory contains comprehensive examples demonstrating the capabilities of the pydantic-forms library.

## Flask Examples

The main Flask example (`flask_examples.py`) showcases all the features of pydantic-forms with a complete web interface.

### Features Demonstrated

1. **Minimal Forms** (`/minimal`)
   - Simple login form
   - Basic contact form
   - Essential validation
   - Clean, responsive design

2. **Medium Complexity Forms** (`/medium`)
   - Auto-generated forms from Pydantic models
   - Manual form construction with custom organization
   - Multi-section forms with cards
   - Advanced field types and validation

3. **Kitchen Sink Form** (`/kitchen`)
   - Every available input type
   - All validation options
   - Advanced features (CSRF, honeypot, file uploads)
   - Complete showcase of capabilities

4. **Layout Examples** (`/layouts`)
   - Vertical layout (default)
   - Horizontal layout with Bootstrap grid
   - Responsive grid layouts
   - Tab-based organization
   - Card layouts

### Running the Flask Examples

From the repository root directory:

```bash
# Install the package in development mode
pip install -e .

# Run the Flask demo
PYTHONPATH=/workspaces/pydantic-forms python examples/flask_examples.py
```

Then visit: http://localhost:5001

### Example Features

- **Type-Safe Forms**: All forms are generated from Pydantic models with automatic validation
- **Multiple Layouts**: Vertical, horizontal, grid, tabs, and cards
- **Responsive Design**: Bootstrap 5 with mobile-first approach
- **Validation**: Both client-side and server-side validation with error handling
- **Framework Integration**: Demonstrates Flask integration patterns
- **Modern UI**: Clean, professional interface with icons and animations

### Code Structure

- `flask_examples.py` - Main Flask application with all routes and examples
- `archive/` - Previous example files moved here for reference

### Pydantic Models Used

1. **LoginModel** - Simple email/password authentication
2. **ContactModel** - Standard contact form with urgency levels
3. **UserProfileModel** - Medium complexity with personal info, account settings, and preferences  
4. **KitchenSinkModel** - Comprehensive model showing all field types and validations

### Integration Patterns

The examples demonstrate several integration patterns:

- **Auto-generation** from Pydantic models using `AutoFormBuilder`
- **Manual construction** with `FormBuilder` for custom layouts
- **Form validation** with error handling and user feedback
- **Data processing** with type-safe model validation
- **Layout systems** for organizing complex forms

## Archive

The `archive/` directory contains previous examples that have been superseded by the comprehensive Flask demo:

- `example.py` - Low-level UI components demo
- `example_two.py` - Alternative form examples  
- `pydantic_kitchen_sink.py` - Pydantic model examples
- `simple_example.py` - Basic usage examples
- And others...

These are kept for reference and backward compatibility.

## Next Steps

After exploring these examples, you can:

1. Integrate pydantic-forms into your own Flask application
2. Explore the FastAPI integration (similar patterns)
3. Customize themes and layouts for your brand
4. Add advanced validation rules and custom components
5. Build complex multi-step forms with the layout system

For more information, see the main project documentation.