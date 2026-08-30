#!/usr/bin/env python3
"""
Menu Order Example - checkbox_group/radio ui_options={'collapsible': True}
=============================================================================

Mounted into main.py's showcase app (see the "Collapsible Option Groups" tag)
demonstrating checkbox_group/radio's `ui_options={'collapsible': True,
'collapsed': True}` in a realistic restaurant order form. Purely
presentational -- it never changes which fields are required; that's still
driven entirely by each field's own Field(...) declaration, untouched by
collapsing/expanding.

MenuOrder below has plain top-level fields (customer_name, customer_email,
order_type) -- a "simple form" -- plus one model_list subform (`items`, a
repeating list of MenuItem line items). Each MenuItem picks a menu item and
patty count, sets a quantity, adds free-form notes, and customizes it via
three independently collapsible checkbox_group toppings sections -- so this
also exercises the feature inside a subform, not just at a form's top level.

This form mutates state (places an order), so it carries CSRF protection --
a token is issued on GET and verified before validation on POST, on
mismatch, re-rendering with a form-level error and never reaching model
validation -- following the exact same pattern as fastapi_routes.py's
login/register routes (issue_*_csrf_token/verify_*_csrf_token).

Run directly to print the rendered HTML to stdout, or mount `router` in a
FastAPI app to try it in a browser.
"""

import asyncio
import hmac
import secrets
from enum import Enum

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import EmailStr

from examples.fastapi_routes import log_timing, templates
from pydantic_schemaforms import Field, FormModel, parse_nested_form_data, render_form_html_async


class MenuItemName(str, Enum):
    cheeseburger = 'Cheeseburger'
    veggie_burger = 'Veggie Burger'
    chicken_sandwich = 'Chicken Sandwich'
    hot_dog = 'Hot Dog'


class OrderType(str, Enum):
    dine_in = 'Dine In'
    takeout = 'Takeout'
    delivery = 'Delivery'


class MenuItem(FormModel):
    """One order line item -- the "subform" repeated by MenuOrder.items
    below. Toppings are all optional (ordering a burger plain is valid), so
    collapsing a group never blocks submission -- collapsible only changes
    whether the checkboxes are visible by default, never whether they're
    required."""

    # Real Enum types don't auto-populate select/radio choices the way
    # Literal[...] does (Pydantic puts an Enum's members in a $ref'd $defs
    # entry, not inlined into the field's own schema, and this library does
    # no $ref resolution before choice-inference runs) -- pass
    # ui_options={'choices': [...]} explicitly, same as docs/recipes.md's
    # own Enum examples do.
    item: MenuItemName = Field(
        MenuItemName.cheeseburger,
        title='Item',
        ui_element='select',
        ui_options={'choices': [e.value for e in MenuItemName]},
    )
    # ge/le must bound the same range as the choices below -- ui_options only
    # decorates the rendered <input>s, it never validates anything server-side
    # (see CLAUDE.md/the AI instructions' "Constraints vs. ui_options" rule),
    # so a choice outside ge/le would render as a selectable, apparently-valid
    # option that then fails validation on submit with a confusing error.
    patties: int = Field(
        1,
        ge=1,
        le=4,
        title='Patties',
        ui_element='radio',
        ui_options={
            'choices': [
                {'value': 1, 'label': 'Single'},
                {'value': 2, 'label': 'Double'},
                {'value': 3, 'label': 'Triple'},
                {'value': 4, 'label': 'Quadruple'},
            ],
        },
    )
    quantity: int = Field(1, ge=1, le=10, title='Quantity', ui_element='quantity')
    vegetables: list[str] = Field(
        default_factory=list,
        title='Vegetables',
        ui_element='checkbox_group',
        ui_options={'choices': ['Lettuce', 'Tomato', 'Onion', 'Pickles'], 'collapsible': True},
    )
    condiments: list[str] = Field(
        default_factory=list,
        title='Condiments',
        ui_element='checkbox_group',
        ui_options={
            'choices': ['Ketchup', 'Mustard', 'Mayo', 'BBQ Sauce'],
            'collapsible': True,
            'collapsed': True,
        },
    )
    add_ons: list[str] = Field(
        default_factory=list,
        title='Add-Ons',
        ui_element='checkbox_group',
        ui_options={
            'choices': ['Bacon', 'Extra Cheese', 'Avocado'],
            'collapsible': True,
            'collapsed': True,
        },
    )
    special_instructions: str = Field(
        '',
        title='Special Instructions',
        ui_element='textarea',
        ui_options={'rows': 2},
        ui_placeholder='e.g. no onions, extra crispy...',
    )


class MenuOrder(FormModel):
    """The simple form (customer_name/customer_email/order_type) plus the
    `items` model_list subform -- see MenuItem above."""

    customer_name: str = Field(..., min_length=2, title='Your Name', ui_element='text')
    customer_email: EmailStr = Field(..., title='Email Address', ui_element='email')
    order_type: OrderType = Field(
        OrderType.dine_in,
        title='Order Type',
        ui_element='radio',
        ui_options={'choices': [e.value for e in OrderType]},
    )
    items: list[MenuItem] = Field(
        default_factory=lambda: [MenuItem()],
        title='Order Items',
        ui_element='model_list',
        min_length=1,
        max_length=10,
        ui_add_button_label='Add Another Item',
        ui_item_title_template='{quantity}x {item}',
        ui_collapsible_items=True,
        ui_items_expanded=True,
    )


MENU_ORDER_CSRF_SESSION_KEY = 'menu_order_csrf_token'


def issue_menu_order_csrf_token(request: Request) -> str:
    """Issue and persist a CSRF token for this order flow."""
    token = secrets.token_urlsafe(32)
    request.session[MENU_ORDER_CSRF_SESSION_KEY] = token
    return token


def verify_menu_order_csrf_token(request: Request, submitted_token) -> bool:
    """Verify a submitted token against the session token using constant-time compare."""
    expected_token = request.session.get(MENU_ORDER_CSRF_SESSION_KEY)
    if not expected_token or not submitted_token:
        return False
    return hmac.compare_digest(str(expected_token), str(submitted_token))


router = APIRouter(prefix='/menu-order', tags=['Collapsible Option Groups'])

_TITLE = 'Menu Order - Collapsible Option Groups'
_DESCRIPTION = (
    "checkbox_group's ui_options={'collapsible': True} turns a group's "
    '<legend> into a toggle that shows/hides its checkboxes -- purely '
    'presentational, it never touches which fields are required. Each order '
    "item's Vegetables/Condiments/Add-Ons groups collapse independently, and "
    'the whole items field is itself a model_list subform, so this also '
    'demonstrates the feature nested inside a repeating sub-form.'
)


@router.get('/', response_class=HTMLResponse)
async def show_form(request: Request, style: str = 'bootstrap', debug: bool = False):
    csrf_token = issue_menu_order_csrf_token(request)
    with log_timing('render_form_html_async'):
        form_html = await render_form_html_async(
            MenuOrder,
            submit_url='/menu-order/',
            framework=style,
            debug=debug,
            csrf_mode='required-provider',
            csrf_token_provider=csrf_token,
            csrf_field_name='csrf_token',
        )
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': _TITLE,
            'description': _DESCRIPTION,
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
        headers={'Cache-Control': 'no-store'},
    )


@router.post('/', response_class=HTMLResponse)
async def submit_form(request: Request, style: str = 'bootstrap', debug: bool = False):
    form_dict = dict(await request.form())
    submitted_csrf_token = form_dict.pop('csrf_token', None)
    # items[0].vegetables-style flat keys (from the model_list subform) ->
    # a nested {'items': [{...}]} dict, so result.data below comes back
    # nested too (flatten=True on .validate() would accept the same flat
    # input, but its *output* stays flat -- matching whichever shape was
    # given -- so parse_nested_form_data() here is what actually gets a
    # nested result.data below).
    submitted = parse_nested_form_data(form_dict)

    if not verify_menu_order_csrf_token(request, submitted_csrf_token):
        # On mismatch: re-render with a form-level error (not a field error,
        # since it isn't about any one field) and a fresh token, and never
        # reach MenuOrder.validate() -- an invalid/replayed/missing CSRF
        # token must not get a chance at a "your order was invalid because
        # X" response, which would confirm the request was at least parsed.
        csrf_error = 'CSRF verification failed. Refresh the page and submit again.'
        csrf_token = issue_menu_order_csrf_token(request)
        form_html = await render_form_html_async(
            MenuOrder,
            form_data=submitted,
            errors={'form': csrf_error},
            submit_url='/menu-order/',
            framework=style,
            debug=debug,
            csrf_mode='required-provider',
            csrf_token_provider=csrf_token,
            csrf_field_name='csrf_token',
        )
        return templates.TemplateResponse(
            request,
            'form.html',
            {
                'request': request,
                'title': _TITLE,
                'description': _DESCRIPTION,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
                'form_html': form_html,
                'errors': {'form': csrf_error},
            },
            status_code=403,
            headers={'Cache-Control': 'no-store'},
        )

    result = MenuOrder.validate(
        submitted,
        submit_url='/menu-order/',
        framework=style,
        csrf_mode='required-provider',
        csrf_field_name='csrf_token',
    )
    if not result.is_valid:
        # A fresh token for the re-rendered form -- csrf_mode/csrf_field_name
        # were already set on .validate() above, so render_with_errors_async
        # only needs a new provider value, not the mode/field-name again.
        csrf_token = issue_menu_order_csrf_token(request)
        form_html = await result.render_with_errors_async(
            csrf_token_provider=csrf_token, debug=debug
        )
        return templates.TemplateResponse(
            request,
            'form.html',
            {
                'request': request,
                'title': _TITLE,
                'description': _DESCRIPTION,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
                'form_html': form_html,
            },
            headers={'Cache-Control': 'no-store'},
        )

    # Success -- drop the token so it can't be replayed for a second order.
    request.session.pop(MENU_ORDER_CSRF_SESSION_KEY, None)
    item_count = sum(item['quantity'] for item in result.data['items'])
    # result.data['order_type'] is the actual OrderType member (Pydantic
    # keeps enums as-is in model_dump()); f-string formatting a `str, Enum`
    # member (not a 3.11+ `enum.StrEnum`) renders "OrderType.takeout", not
    # its value -- use .value explicitly.
    order_type = result.data['order_type'].value
    return templates.TemplateResponse(
        request,
        'success.html',
        {
            'request': request,
            'title': 'Order Placed',
            'message': f'{item_count} item(s) ordered for {result.data["customer_name"]} '
            f'({order_type}).',
            'data': result.data,
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'try_again_url': '/menu-order/',
        },
    )


async def _print_standalone_html() -> None:
    print(await render_form_html_async(MenuOrder, submit_url='/menu-order/'))


if __name__ == '__main__':
    asyncio.run(_print_standalone_html())
