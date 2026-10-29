from datetime import date
from decimal import Decimal

from pydantic import computed_field

from pydantic_schemaforms import Field, FormModel


class LineItem(FormModel):
    product: str = Field(title='Product', min_length=2)
    quantity: int = Field(1, title='Quantity', ge=1, le=999)
    unit_price: Decimal = Field(title='Unit price', ge=0, decimal_places=2, ui_element='currency')

    @computed_field
    @property
    def total(self) -> Decimal:
        return self.quantity * self.unit_price


class OrderForm(FormModel):
    customer: str = Field(title='Customer', ui_autofocus=True)
    delivery_date: date = Field(title='Delivery date')
    items: list[LineItem] = Field(
        default_factory=list,
        title='Line items',
        min_length=1,
        max_length=50,
        ui_add_button_label='Add a line',
        ui_item_title_template='{product}',
    )
    notes: str = Field('', title='Notes', ui_element='textarea')
