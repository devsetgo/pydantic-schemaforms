from typing import Literal

from pydantic_schemaforms import Field, FormModel


class SurveyForm(FormModel):
    """A short feedback survey: every question is optional except the overall rating."""

    # A star rating is an int: ge/le are the real limits, the stars are only how it's shown.
    overall: int = Field(title='How was your visit overall?', ge=1, le=5, ui_element='star_rating')
    # Literal choices render as options; radio shows all of them at once.
    recommend: Literal['Yes', 'Maybe', 'No'] = Field(
        'Maybe', title='Would you recommend us?', ui_element='radio'
    )
    # list[Literal[...]] lets the user pick several.
    liked: list[Literal['Staff', 'Price', 'Speed', 'Quality']] = Field(
        default_factory=list, title='What did you like?', ui_element='checkbox_group'
    )
    comments: str = Field('', title='Anything else?', max_length=1000, ui_element='textarea')
