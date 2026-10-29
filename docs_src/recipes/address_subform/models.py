from typing import Literal, Self

from pydantic import EmailStr, model_validator

from pydantic_schemaforms import Field, FormModel


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City', min_length=2)
    postal_code: str = Field(title='Postal code', pattern=r'^[A-Za-z0-9 -]{3,10}$')
    country: Literal['US', 'CA', 'GB', 'FR', 'DE'] = Field('US', title='Country')


class CheckoutForm(FormModel):
    email: EmailStr = Field(title='Email for the receipt')
    shipping: Address = Field(title='Shipping address')
    billing_same_as_shipping: bool = Field(True, title='Bill to the shipping address')
    billing: Address | None = Field(None, title='Billing address', ui_collapsed=True)

    @model_validator(mode='after')
    def billing_given(self) -> Self:
        if not self.billing_same_as_shipping and self.billing is None:
            raise ValueError('Enter a billing address, or bill to the shipping address')
        return self

    def billing_address(self) -> Address:
        return self.shipping if self.billing_same_as_shipping else self.billing
