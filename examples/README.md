# Pydantic Forms Examples

This directory contains comprehensive examples demonstrating the capabilities of the pydantic-forms library.

## 🚀 Demo Applications

### Flask Demo (unified_demo.py)
A complete Flask application showcasing all features of pydantic-forms:

**Features:**
- Minimal, medium, and complex form examples
- Bootstrap 5 and Material Design 3 themes
- All layout types: vertical, horizontal, side-by-side, and tabbed
- Complete form validation and error handling
- Proper Jinja2 template architecture

**Run the Flask demo:**
```bash
cd examples
python unified_demo.py
```

Visit: http://localhost:5000/

### FastAPI Demo (fastapi_demo.py) ⚡
An async FastAPI application with the same features as the Flask demo, optimized for high performance:

**Features:**
- Async form rendering for maximum performance
- Concurrent layout rendering using `asyncio.gather()`
- Same template compatibility as Flask demo
- FastAPI async route handlers
- Modern Python 3.14+ template strings

**Quick start:**
```bash
cd examples
./run_fastapi_demo.sh --dev
```

**Devcontainer/Codespaces quick start:**
```bash
cd examples
./start_fastapi.sh --dev
```

**Manual installation:**
```bash
# Install FastAPI and dependencies (if needed)
pip install "fastapi[all]" uvicorn

# Run the server
cd examples
uvicorn fastapi_demo:app --reload
```

Visit: http://localhost:8000/

## 📁 Project Structure

```
examples/
├── README.md                          # This file
├── unified_demo.py                    # Flask demo application
├── fastapi_demo.py                    # FastAPI demo application
├── run_fastapi_demo.sh               # FastAPI installation script
├── templates/                         # Jinja2 templates (shared by both demos)
│   ├── base.html                     # Base template with navigation
│   ├── home.html                     # Landing page
│   ├── bootstrap_*.html              # Bootstrap-themed templates
│   ├── material_*.html               # Material Design templates
│   ├── layouts.html                  # Bootstrap layout demonstrations
│   └── material_layouts.html         # Material Design layout demonstrations
├── static/                           # Static assets
│   ├── css/                         # Custom stylesheets
│   └── js/                          # JavaScript files
└── archive/                          # Legacy examples
    ├── simple_example.py             # Basic usage example
    ├── pydantic_example.py           # Pydantic integration
    └── form_model_demo.py            # FormModel demonstration
```

## 🎨 Available Themes

### Bootstrap 5
- Modern responsive design
- Complete component library
- Professional appearance
- Extensive customization options

### Material Design 3
- Google's latest design language
- Authentic Material components
- Dynamic color theming
- Accessible and inclusive

## 📐 Layout Options

All layout types are available in both Bootstrap and Material Design:

1. **Vertical Layout** (default)
   - Fields stacked vertically
   - Best for most forms
   - Mobile-friendly

2. **Horizontal Layout**
   - Labels and inputs side-by-side
   - Compact design
   - Good for desktop

3. **Side-by-Side Layout**
   - Form fields arranged in two columns
   - Efficient use of space
   - Great for longer forms

4. **Tabbed Layout**
   - Fields organized into tabs
   - Perfect for complex forms
   - Better user experience for multi-section forms

## 🔧 Form Examples

### Minimal Login Form
- Username/password fields
- Remember me checkbox
- Basic validation
- Simple and clean

### Medium Contact Form
- Personal information section
- Message details
- Priority selection (enum)
- Email validation

### Complex Kitchen Sink Form
- All input types demonstration
- Text, email, password, number inputs
- Select dropdowns, checkboxes
- Date pickers
- Complex validation rules

## 🚀 Performance Features

### Async Rendering (FastAPI Demo)
- Non-blocking form generation
- Concurrent layout rendering
- Thread pool execution for CPU-bound operations
- Optimal for high-traffic applications

### Template Caching
- Jinja2 template compilation caching
- Reduced rendering overhead
- Better performance in production

## 📱 Responsive Design

All examples are fully responsive and work across:
- Desktop browsers
- Tablets
- Mobile devices
- Various screen sizes

## 🔍 Testing the Examples

1. **Start a demo application**
2. **Try different form types:**
   - Minimal: Basic login form
   - Medium: Contact form with validation
   - Complex: Kitchen sink with all input types
3. **Switch between themes:**
   - Bootstrap: Modern professional appearance
   - Material: Google's design language
4. **Test different layouts:**
   - Navigate to /layouts or /material/layouts
   - Compare layout rendering
   - Test responsiveness
5. **Test form validation:**
   - Submit invalid data
   - Check error messages
   - Verify validation rules

## 🔧 Development

### Adding New Examples
1. Create a new form model inheriting from `FormModel`
2. Add validation methods if needed
3. Create route handlers for GET/POST
4. Add template files
5. Update navigation in `base.html`

### Customizing Themes
1. Modify CSS files in `static/css/`
2. Update templates in `templates/`
3. Customize form rendering options
4. Test across different browsers

### Performance Testing
1. Use the FastAPI demo for async testing
2. Monitor rendering times
3. Test with concurrent requests
4. Profile memory usage

## 📚 Additional Resources

- [Main README](../README.md) - Project overview
- [API Documentation](../docs/) - Detailed API reference
- [Contributing Guide](../contribute.md) - Development guidelines
- [License](../LICENSE) - Usage terms

## 🤝 Contributing

We welcome contributions! Please see our [contributing guide](../contribute.md) for details on:
- Setting up the development environment
- Creating new examples
- Testing your changes
- Submitting pull requests

## 📄 License

These examples are part of the pydantic-forms project and are licensed under the same terms. See [LICENSE](../LICENSE) for details.