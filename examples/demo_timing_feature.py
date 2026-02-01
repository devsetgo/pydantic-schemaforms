"""
Demo script showing the render timing feature in action.
This demonstrates logging, debug panel display, and inline timing.
"""

import logging
from pydantic_schemaforms.schema_form import Field, FormModel

# Configure logging to see the timing logs
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)


class ContactForm(FormModel):
    """A simple contact form"""
    name: str = Field(..., min_length=2, description="Your full name")
    email: str = Field(..., description="Email address")
    subject: str = Field(..., min_length=5, description="Message subject")
    message: str = Field(..., min_length=10, description="Your message")


def demo_basic_timing():
    """Demo 1: Basic timing with logging"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Form Rendering with Timing Logs")
    print("="*60)

    from pydantic_schemaforms.enhanced_renderer import render_form_html

    html = render_form_html(ContactForm, debug=False)

    print("Form rendered (check logs above for timing)")
    print(f"HTML length: {len(html)} characters")


def demo_show_timing():
    """Demo 2: Inline timing display below submit button"""
    print("\n" + "="*60)
    print("DEMO 2: Inline Timing Display (show_timing=True)")
    print("="*60)

    from pydantic_schemaforms.enhanced_renderer import render_form_html

    html = render_form_html(ContactForm, show_timing=True)

    # Extract timing from inline display
    import re
    match = re.search(r'Rendered in ([\d.]+)s</div>', html)

    if match:
        render_time = match.group(1)
        print(f"✓ Inline timing display shows: {render_time} seconds")
        print("✓ Timing appears below submit button in small text")
    else:
        print("✗ Could not find inline timing")

    print(f"HTML length: {len(html)} characters")


def demo_debug_panel_timing():
    """Demo 3: Timing displayed in debug panel"""
    print("\n" + "="*60)
    print("DEMO 3: Debug Panel Timing")
    print("="*60)
    print("DEMO 2: Timing in Debug Panel")
    print("="*60)

    from pydantic_schemaforms.enhanced_renderer import render_form_html

    html = render_form_html(ContactForm, debug=True)

    # Extract timing from debug panel
    import re
    match = re.search(r'Debug panel \(development only\) — ([\d.]+)s render', html)

    if match:
        render_time = match.group(1)
        print(f"✓ Debug panel shows render time: {render_time} seconds")
        print("✓ Timing is visible in the debug panel summary")
    else:
        print("✗ Could not find timing in debug panel")

    print(f"HTML length: {len(html)} characters")


def demo_multiple_renders():
    """Demo 3: Multiple renders showing consistent timing"""
    print("\n" + "="*60)
    print("DEMO 3: Multiple Renders with Timing Comparison")
    print("="*60)

    from pydantic_schemaforms.enhanced_renderer import render_form_html
    import re

    times = []
    for _i in range(5):
        html = render_form_html(ContactForm, debug=True)

        match = re.search(r'— ([\d.]+)s render', html)
        if match:
            times.append(float(match.group(1)))

    if times:
        avg_time = sum(times) / len(times)
        print("\nRendering Statistics:")
        print(f"  Renders: {len(times)}")
        print(f"  Average: {avg_time:.4f} seconds")
        print(f"  Min: {min(times):.4f} seconds")
        print(f"  Max: {max(times):.4f} seconds")


def demo_form_builder_timing():
    """Demo 4: Timing with render_form_html wrapper"""
    print("\n" + "="*60)
    print("DEMO 4: render_form_html wrapper with Timing")
    print("="*60)

    from pydantic_schemaforms.render_form import render_form_html

    html = render_form_html(ContactForm, debug=True, framework="bootstrap")

    import re
    match = re.search(r'— ([\d.]+)s render', html)
    if match:
        print(f"✓ Form rendered in {match.group(1)} seconds (via render_form_html)")

    print(f"HTML includes HTMX scripts: {'htmx' in html}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*10 + "PYDANTIC-SCHEMAFORMS RENDER TIMING DEMO")
    print("="*70)
    print("\nThis demo shows the timing features:")
    print("  1. Logs render time automatically")
    print("  2. show_timing=True: Displays timing below submit button")
    print("  3. debug=True: Displays timing in debug panel header")
    print("  4. Both can be used together")

    demo_basic_timing()
    demo_show_timing()
    demo_debug_panel_timing()
    demo_multiple_renders()
    demo_form_builder_timing()

    print("\n" + "="*70)
    print("✓ All demos completed successfully!")
    print("="*70 + "\n")
