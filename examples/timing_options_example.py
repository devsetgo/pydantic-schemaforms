"""
Complete example showing all timing display options.
"""

from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.schema_form import Field, FormModel


class UserRegistration(FormModel):
    """User registration form"""
    username: str = Field(..., min_length=3, description="Choose a username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="At least 8 characters")
    age: int = Field(..., ge=18, description="Must be 18 or older")


# Example 1: Default - no timing display (timing is still logged)
print("Example 1: Default rendering (timing logged only)")
print("-" * 60)
html1 = render_form_html(UserRegistration)
print(f"HTML size: {len(html1)} bytes")
print("✓ Timing logged to INFO level")
print()

# Example 2: show_timing=True - small text below submit button
print("Example 2: show_timing=True (inline display)")
print("-" * 60)
html2 = render_form_html(UserRegistration, show_timing=True)
print(f"HTML size: {len(html2)} bytes")
if "Rendered in" in html2:
    print("✓ Timing displayed below submit button")
print()

# Example 3: debug=True - timing in debug panel header
print("Example 3: debug=True (debug panel with timing)")
print("-" * 60)
html3 = render_form_html(UserRegistration, debug=True)
print(f"HTML size: {len(html3)} bytes")
if "Debug panel (development only)" in html3 and "s render" in html3:
    print("✓ Timing displayed in debug panel header")
print()

# Example 4: Both show_timing and debug enabled
print("Example 4: show_timing=True + debug=True (both displays)")
print("-" * 60)
html4 = render_form_html(UserRegistration, show_timing=True, debug=True)
print(f"HTML size: {len(html4)} bytes")
has_inline = "Rendered in" in html4 and "s</div>" in html4
has_debug = "Debug panel (development only)" in html4 and "s render" in html4
if has_inline and has_debug:
    print("✓ Both inline timing and debug panel timing displayed")
print()

print("=" * 60)
print("Summary:")
print("  • Timing is ALWAYS logged at INFO level")
print("  • show_timing=True: Adds small text below submit button")
print("  • debug=True: Adds comprehensive debug panel with timing")
print("  • Both can be used simultaneously")
print("=" * 60)
