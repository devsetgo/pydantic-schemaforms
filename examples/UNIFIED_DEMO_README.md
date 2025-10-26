# Unified Pydantic Forms Demo

A comprehensive demonstration of the pydantic-forms library showcasing all major features in a single Flask application.

## Features Demonstrated

### 🎨 Multiple Themes
- **Bootstrap 5** - Modern, responsive design with extensive components
- **Material Design 3** - Google's design system with clean typography and animations

### 📋 Form Complexity Levels
1. **Minimal Forms** - Simple login forms with basic validation
2. **Medium Forms** - Contact forms with multiple field types and advanced validation
3. **Complex Forms** - Kitchen sink examples with all available input types

### 🏗️ Layout Systems
- **Vertical Layout** (Default) - Traditional stacked form arrangement
- **Horizontal Layout** - Side-by-side forms using Bootstrap grid
- **Tabbed Layout** - Multi-step forms organized in tabs

### 🔧 Technical Features
- **Python 3.14+ Template Strings** - Native string template support
- **Server-Side Validation** - Comprehensive Pydantic-based validation
- **Error Handling** - User-friendly error display and handling
- **Responsive Design** - Mobile-first responsive layouts
- **Type Safety** - Full Pydantic type validation and safety

## Running the Demo

```bash
# From the repository root
cd /workspaces/pydantic-forms
python examples/unified_demo.py
```

Then visit:
- **Main Page**: http://localhost:5000/
- **Bootstrap Examples**: http://localhost:5000/bootstrap/
- **Material Examples**: http://localhost:5000/material/
- **Layout Examples**: http://localhost:5000/layouts

## Available Routes

### Bootstrap Theme Routes
- `/bootstrap/minimal` - Simple login form
- `/bootstrap/medium` - Contact form with multiple fields
- `/bootstrap/complex` - Kitchen sink with all input types

### Material Design Routes
- `/material/minimal` - Material Design login form
- `/material/medium` - Material Design contact form
- `/material/complex` - Material Design kitchen sink

### Layout Demonstrations
- `/layouts` - All layout systems demonstrated

## Form Models

### MinimalLoginForm
Simple authentication form with:
- Username/email field with validation
- Password field with minimum length requirement
- Remember me checkbox
- Client and server-side validation

### MediumContactForm
Contact form demonstrating:
- Personal information fields (first name, last name)
- Communication fields (email, phone)
- Message composition (subject, message, priority)
- Preference settings (newsletter subscription)
- Cross-field validation and formatting

### ComplexKitchenSinkForm
Comprehensive form showcasing:
- **Text Inputs**: text, email, password, search, URL, telephone, textarea
- **Numeric Inputs**: number, float, range slider
- **Selection Inputs**: select dropdown, country selection, radio buttons, multi-select
- **Boolean Inputs**: checkbox, switch toggle
- **Date/Time Inputs**: date, time, datetime-local
- **Specialized Inputs**: color picker, file upload, hidden fields
- **User Profile**: role selection, biography, preferences

## Validation Features

### Client-Side Validation
- Real-time validation feedback
- Visual error indicators
- Bootstrap validation classes
- Interactive form elements

### Server-Side Validation
- Pydantic model validation
- Custom validation rules
- Cross-field validation
- Comprehensive error reporting

### Validation Rules Demonstrated
- Required fields
- String length constraints
- Email format validation
- Phone number formatting
- Numeric range validation
- Date range validation
- Password strength requirements
- Custom validation logic

## Styling and UX

### Bootstrap 5 Features
- Responsive grid system
- Form validation states
- Interactive components
- Bootstrap Icons integration
- Consistent spacing and typography

### Material Design Features
- Material typography (Roboto font)
- Material form controls
- Floating labels
- Material color palette
- Material animation patterns

### Custom Enhancements
- Gradient backgrounds and headers
- Smooth transitions and hover effects
- Custom form containers
- Professional card layouts
- Responsive navigation

## Code Structure

### Form Definition Pattern
```python
class MyForm(FormModel):
    field_name: str = FormField(
        title="Display Name",
        input_type="text",
        placeholder="Enter value...",
        help_text="Helpful description",
        icon="bi bi-icon",
        min_length=3,
        max_length=50
    )
```

### Route Handler Pattern
```python
@app.route('/my-form', methods=['GET', 'POST'])
def my_form():
    if request.method == 'POST':
        result = handle_form_submission(MyForm, request.form.to_dict())
        # Handle success/errors
    else:
        form_html = render_form_html(MyForm, framework="bootstrap")
        # Render form
```

### Layout System Usage
```python
class MyLayout(VerticalLayout):
    form = MyForm
    form_config = SectionDesign(
        section_title="Form Title",
        section_description="Form description",
        icon="form-icon"
    )
```

## Input Types Showcased

### Text-Based Inputs
- `text` - Basic text input
- `email` - Email with validation
- `password` - Password with masking
- `search` - Search input with styling
- `url` - URL with validation
- `tel` - Telephone input
- `textarea` - Multi-line text

### Numeric Inputs
- `number` - Integer/decimal numbers
- `range` - Range slider with live value

### Selection Inputs
- `select` - Dropdown selection
- `radio` - Radio button groups
- `checkbox` - Individual checkboxes
- Multi-select capabilities

### Date/Time Inputs
- `date` - Date picker
- `time` - Time picker
- `datetime-local` - Combined date/time

### Specialized Inputs
- `color` - Color picker
- `file` - File upload
- `hidden` - Hidden form fields

## Error Handling

### Validation Error Display
- Field-specific error messages
- Form-level error summaries
- Visual error indicators
- User-friendly error text

### Error Recovery
- Preserve form data on validation errors
- Clear error instructions
- Progressive validation feedback
- Graceful degradation

## Browser Compatibility

### Supported Browsers
- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Mobile Support
- Responsive design for all screen sizes
- Touch-friendly form controls
- Mobile-optimized layouts
- Adaptive typography

## Development Notes

### Python Requirements
- Python 3.14+ (strict requirement)
- Native template string support
- Modern Pydantic features

### Dependencies
- Flask for web framework
- Pydantic for validation
- Bootstrap 5 for UI framework
- Material Design fonts and icons

### Performance Considerations
- Template caching for improved rendering
- Efficient form validation
- Minimal JavaScript footprint
- Optimized CSS delivery

## Next Steps

This unified demo serves as:
1. **Documentation** - Living examples of all library features
2. **Testing Platform** - Manual testing of form functionality
3. **Integration Guide** - Pattern examples for real applications
4. **Development Reference** - Complete implementation examples

For production use, consider:
- Adding CSRF protection
- Implementing proper session management
- Adding comprehensive error logging
- Optimizing for specific deployment environments
- Adding advanced validation rules
- Implementing file upload handling

## Contributing

When adding new features to the library:
1. Update the appropriate form model in this demo
2. Add route handlers for new functionality
3. Include both Bootstrap and Material Design examples
4. Document new features in this README
5. Test all layouts and themes with new features

This unified demo should remain the comprehensive showcase of all pydantic-forms capabilities.