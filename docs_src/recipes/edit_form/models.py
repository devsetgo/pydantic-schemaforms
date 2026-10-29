from datetime import date
from enum import Enum

from pydantic_schemaforms import Field, FormModel


class Status(str, Enum):
    draft = 'draft'
    active = 'active'
    archived = 'archived'


class ProductForm(FormModel):
    name: str = Field(title='Name', min_length=2)
    price: float = Field(title='Price', ge=0)
    status: Status = Field(Status.draft, title='Status')
    launch_date: date | None = Field(None, title='Launch date')
    featured: bool = Field(False, title='Featured on the home page')


PRODUCTS = {  # stands in for your database
    1: {
        'id': 1,
        'name': 'Desk lamp',
        'price': 39.5,
        'status': Status.active,
        'launch_date': date(2026, 3, 1),
        'featured': True,
        'created_by': 'ada',
    },
}
