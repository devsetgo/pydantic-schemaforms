"""
Numeric input components using Python 3.14 template strings.
Includes NumberInput, RangeInput, and specialized numeric inputs.
"""

from typing import Union

from .base import NumericInput


class NumberInput(NumericInput):
    """Standard numeric input field with step controls."""

    ui_element = "number"

    template = """<input type="number" ${attributes} />"""

    def get_input_type(self) -> str:
        return "number"

    def render(self, **kwargs) -> str:
        # Add input mode for mobile keyboards
        if "inputmode" not in kwargs:
            kwargs["inputmode"] = "numeric"

        # Set default step if not provided
        if "step" not in kwargs:
            kwargs["step"] = "1"

        return super().render(**kwargs)


class RangeInput(NumericInput):
    """Range slider input for selecting values within a range."""

    ui_element = "range"

    template = """<input type="range" ${attributes} />"""

    def get_input_type(self) -> str:
        return "range"

    def render(self, show_value: bool = True, **kwargs) -> str:
        """Render range input with optional value display."""
        range_html = super().render(**kwargs)

        if show_value:
            field_name = kwargs.get("name", "")
            value = kwargs.get("value", kwargs.get("min", "0"))

            # Add value display and JavaScript to update it
            value_display = f"""
            <output for="{field_name}" id="{field_name}-value">{value}</output>
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const range = document.getElementById('{field_name}');
                const output = document.getElementById('{field_name}-value');
                if (range && output) {{
                    range.addEventListener('input', function() {{
                        output.textContent = this.value;
                    }});
                }}
            }});
            </script>
            """
            return range_html + value_display

        return range_html


class PercentageInput(NumberInput):
    """Percentage input with automatic % formatting."""

    def render(self, **kwargs) -> str:
        # Set percentage-specific constraints
        kwargs["min"] = kwargs.get("min", "0")
        kwargs["max"] = kwargs.get("max", "100")
        kwargs["step"] = kwargs.get("step", "0.1")
        kwargs["placeholder"] = kwargs.get("placeholder", "50.0")

        # Add percentage symbol to placeholder if not present
        if "%" not in str(kwargs.get("placeholder", "")):
            kwargs["placeholder"] = f"{kwargs['placeholder']}%"

        return super().render(**kwargs)


class DecimalInput(NumberInput):
    """Decimal number input with configurable precision."""

    def render(self, decimal_places: int = 2, **kwargs) -> str:
        # Set step based on decimal places
        step = 1 / (10**decimal_places)
        kwargs["step"] = kwargs.get("step", str(step))
        kwargs["inputmode"] = "decimal"

        return super().render(**kwargs)


class IntegerInput(NumberInput):
    """Integer-only input field."""

    def render(self, **kwargs) -> str:
        # Force step to 1 for integers
        kwargs["step"] = "1"
        kwargs["inputmode"] = "numeric"

        return super().render(**kwargs)


class AgeInput(IntegerInput):
    """Age input with sensible defaults."""

    def render(self, **kwargs) -> str:
        # Set age-appropriate constraints
        kwargs["min"] = kwargs.get("min", "0")
        kwargs["max"] = kwargs.get("max", "150")
        kwargs["placeholder"] = kwargs.get("placeholder", "25")

        return super().render(**kwargs)


class QuantityInput(IntegerInput):
    """Quantity input for shopping carts, inventory, etc."""

    def render(self, **kwargs) -> str:
        # Set quantity-appropriate constraints
        kwargs["min"] = kwargs.get("min", "1")
        kwargs["placeholder"] = kwargs.get("placeholder", "1")

        return super().render(**kwargs)


class ScoreInput(NumberInput):
    """Score input with configurable min/max range."""

    def render(
        self, min_score: Union[int, float] = 0, max_score: Union[int, float] = 100, **kwargs
    ) -> str:
        kwargs["min"] = str(min_score)
        kwargs["max"] = str(max_score)
        kwargs["step"] = kwargs.get(
            "step", "1" if isinstance(min_score, int) and isinstance(max_score, int) else "0.1"
        )

        return super().render(**kwargs)


class RatingInput(RangeInput):
    """Rating input using range slider with star display."""

    def render(self, max_rating: int = 5, **kwargs) -> str:
        # Set rating constraints
        kwargs["min"] = "1"
        kwargs["max"] = str(max_rating)
        kwargs["step"] = "1"
        kwargs["value"] = kwargs.get("value", "3")

        field_name = kwargs.get("name", "")

        # Custom rendering with star display
        range_html = super().render(show_value=False, **kwargs)

        # Add star rating display
        stars_html = f"""
        <div class="star-rating" id="{field_name}-stars">
            {'★' * int(kwargs.get("value", "3"))}{'☆' * (max_rating - int(kwargs.get("value", "3")))}
        </div>
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const range = document.getElementById('{field_name}');
            const stars = document.getElementById('{field_name}-stars');
            if (range && stars) {{
                range.addEventListener('input', function() {{
                    const value = parseInt(this.value);
                    const maxRating = {max_rating};
                    stars.textContent = '★'.repeat(value) + '☆'.repeat(maxRating - value);
                }});
            }}
        }});
        </script>
        """

        return range_html + stars_html


class SliderInput(RangeInput):
    """Enhanced slider with custom styling and labels."""

    def render(self, show_labels: bool = True, **kwargs) -> str:
        """Render slider with optional min/max labels."""
        slider_html = super().render(show_value=True, **kwargs)

        if show_labels:
            min_val = kwargs.get("min", "0")
            max_val = kwargs.get("max", "100")
            kwargs.get("name", "")

            labels_html = f"""
            <div class="slider-labels" style="display: flex; justify-content: space-between; margin-top: 5px;">
                <span class="slider-min">{min_val}</span>
                <span class="slider-max">{max_val}</span>
            </div>
            """
            return slider_html + labels_html

        return slider_html


class TemperatureInput(NumberInput):
    """Temperature input with unit selection."""

    def render(self, unit: str = "celsius", **kwargs) -> str:
        """Render temperature input with unit indicator."""
        if unit.lower() in ["celsius", "c"]:
            kwargs["placeholder"] = kwargs.get("placeholder", "20°C")
            kwargs["min"] = kwargs.get("min", "-273.15")  # Absolute zero
            kwargs["max"] = kwargs.get("max", "1000")
        elif unit.lower() in ["fahrenheit", "f"]:
            kwargs["placeholder"] = kwargs.get("placeholder", "68°F")
            kwargs["min"] = kwargs.get("min", "-459.67")  # Absolute zero in F
            kwargs["max"] = kwargs.get("max", "1800")
        elif unit.lower() in ["kelvin", "k"]:
            kwargs["placeholder"] = kwargs.get("placeholder", "293K")
            kwargs["min"] = kwargs.get("min", "0")  # Absolute zero
            kwargs["max"] = kwargs.get("max", "1273")

        kwargs["step"] = kwargs.get("step", "0.1")

        return super().render(**kwargs)
