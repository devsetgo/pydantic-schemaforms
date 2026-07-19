"""
Selection input components using Python 3.14 template strings.
Includes SelectInput, RadioGroup, CheckboxInput, and multi-select components.
"""

import json
from html import escape
from typing import Any

from pydantic_schemaforms.tstring import substitute
from .base import FormInput, SelectInputBase


class SelectInput(SelectInputBase):
    """Dropdown select input with support for single and multiple selection."""

    ui_element: str = 'select'

    template = """<select ${attributes}>${options}</select>"""

    valid_attributes: list[str] = SelectInputBase.valid_attributes + [
        'size',
        'multiple',
        'autofocus',
    ]

    def get_input_type(self) -> str:
        return 'select'

    def render(self, options: list[dict[str, Any]], **kwargs: Any) -> str:
        """Render select input with provided options."""
        # Build options HTML
        options_html = self._build_options(options)

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)

        # Don't include type attribute for select
        if 'type' in attrs:
            del attrs['type']

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        return substitute(self.template, attributes=attributes_str, options=options_html)

    def _build_options(self, options: list[dict[str, Any]]) -> str:
        """Build HTML options from list of option dictionaries."""
        option_parts = []

        for option in options:
            if isinstance(option, dict):
                value = option.get('value', '')
                label = option.get('label', str(value))
                selected = option.get('selected', False)
                disabled = option.get('disabled', False)

                attrs = [f'value="{escape(str(value))}"']

                if selected:
                    attrs.append('selected')
                if disabled:
                    attrs.append('disabled')

                attrs_str = ' '.join(attrs)
                option_parts.append(f'<option {attrs_str}>{escape(label)}</option>')
            else:
                # Simple string option
                option_parts.append(
                    f'<option value="{escape(str(option))}">{escape(str(option))}</option>'
                )

        return '\n'.join(option_parts)


class MultiSelectInput(SelectInput):
    """Multi-select dropdown with enhanced functionality."""

    ui_element: str = 'multiselect'

    def render(
        self,
        options: list[dict[str, Any]],
        enhanced: bool = True,
        searchable: bool = True,
        search_placeholder: str = 'Search...',
        **kwargs: Any,
    ) -> str:
        """Render multi-select with multiple attribute set.

        The real <select multiple> is always rendered and is what the form
        submits, JS or not. When `enhanced`, it's wrapped with a chips/search
        UI that reads its option data straight off the <select> (single
        source of truth) and only hides the native control after the
        enhanced UI has successfully built, so a JS load failure never
        leaves the field invisible or unusable.
        """
        kwargs['multiple'] = True
        select_html = super().render(options, **kwargs)

        if not enhanced:
            return select_html

        field_id = kwargs.get('id', kwargs.get('name', ''))
        if not field_id:
            return select_html

        search_html = (
            f'<input type="text" class="multiselect-search" '
            f'placeholder="{escape(search_placeholder)}" />'
            if searchable
            else ''
        )

        return f"""
<div class="multiselect-enhanced" data-target="{field_id}">
    <div class="multiselect-chips" id="{field_id}_chips"></div>
    {search_html}
    <ul class="multiselect-dropdown" id="{field_id}_dropdown" hidden></ul>
    {select_html}
</div>
<style>
.multiselect-enhanced {{
    position: relative;
}}
.multiselect-chips {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}}
.multiselect-chips:not(:empty) {{
    margin-bottom: 6px;
}}
.multiselect-chip {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #e2e8f0;
    color: #1c1b1f;
    border-radius: 12px;
    padding: 2px 8px;
    font-size: 0.875rem;
}}
.multiselect-chip-remove {{
    cursor: pointer;
    font-weight: bold;
}}
.multiselect-search {{
    display: block;
    width: 100%;
    box-sizing: border-box;
    padding: 6px 10px;
    border: 1px solid #79747e;
    border-radius: 4px;
}}
.multiselect-dropdown {{
    list-style: none;
    margin: 6px 0 0;
    padding: 0;
    max-height: 180px;
    overflow-y: auto;
    border: 1px solid #79747e;
    border-radius: 4px;
}}
.multiselect-option {{
    padding: 6px 10px;
    cursor: pointer;
}}
.multiselect-option:hover {{
    background: #f1f5f9;
}}
.multiselect-option-selected {{
    background: #e0e7ff;
    font-weight: 600;
}}
/* Applied by the enhancement script once the chips/search/dropdown UI has
   successfully built -- the real <select> stays the form's source of truth
   and in the DOM, just visually replaced by the UI above it. */
.multiselect-native-hidden {{
    display: none !important;
}}
</style>
<script>
document.addEventListener('DOMContentLoaded', function() {{
    const select = document.getElementById('{field_id}');
    const chipsEl = document.getElementById('{field_id}_chips');
    const dropdownEl = document.getElementById('{field_id}_dropdown');
    const searchEl = document.querySelector('[data-target="{field_id}"] .multiselect-search');
    if (!select || !chipsEl || !dropdownEl) return;

    function renderChips() {{
        chipsEl.innerHTML = '';
        Array.from(select.selectedOptions).forEach(function(opt) {{
            const chip = document.createElement('span');
            chip.className = 'multiselect-chip';
            chip.textContent = opt.textContent;
            const remove = document.createElement('span');
            remove.className = 'multiselect-chip-remove';
            remove.textContent = '\\u00d7';
            remove.addEventListener('click', function() {{
                opt.selected = false;
                select.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }});
            chip.appendChild(remove);
            chipsEl.appendChild(chip);
        }});
    }}

    function renderDropdown(filterText) {{
        dropdownEl.innerHTML = '';
        const filter = (filterText || '').toLowerCase();
        Array.from(select.options).forEach(function(opt) {{
            if (filter && !opt.textContent.toLowerCase().includes(filter)) return;
            const item = document.createElement('li');
            item.textContent = opt.textContent;
            item.className = opt.selected
                ? 'multiselect-option multiselect-option-selected'
                : 'multiselect-option';
            item.addEventListener('click', function() {{
                opt.selected = !opt.selected;
                select.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }});
            dropdownEl.appendChild(item);
        }});
    }}

    select.addEventListener('change', function() {{
        renderChips();
        renderDropdown(searchEl ? searchEl.value : '');
    }});

    if (searchEl) {{
        searchEl.addEventListener('focus', function() {{
            dropdownEl.hidden = false;
            renderDropdown(searchEl.value);
        }});
        searchEl.addEventListener('input', function() {{
            renderDropdown(searchEl.value);
        }});
        document.addEventListener('click', function(e) {{
            if (!e.target.closest('[data-target="{field_id}"]')) {{
                dropdownEl.hidden = true;
            }}
        }});
    }}

    renderChips();
    renderDropdown('');
    select.classList.add('multiselect-native-hidden');
}});
</script>
"""


class CheckboxInput(FormInput):
    """Single checkbox input."""

    ui_element: str = 'checkbox'

    template = """<input type="checkbox" ${attributes} />"""

    valid_attributes: list[str] = FormInput.valid_attributes + ['checked', 'value']

    def get_input_type(self) -> str:
        return 'checkbox'

    def render(self, label: str | None = None, **kwargs: Any) -> str:
        """Render checkbox with optional label."""
        # Set default value if not provided
        if 'value' not in kwargs:
            kwargs['value'] = '1'

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Render checkbox
        checkbox_html = f'<input {attributes_str} />'

        if label:
            field_name = kwargs.get('name', '')
            field_id = kwargs.get('id', field_name)
            checkbox_html = f'<label for="{field_id}">{checkbox_html} {escape(label)}</label>'

        return checkbox_html


class CheckboxGroup(SelectInputBase):
    """Group of checkbox inputs for multiple selections."""

    ui_element: str = 'checkbox_group'

    template = """<fieldset ${fieldset_attributes}>
    <legend>${legend}</legend>
    ${checkboxes}
</fieldset>"""

    def get_input_type(self) -> str:
        return 'checkbox-group'

    def render(
        self,
        options: list[dict[str, Any]],
        group_name: str,
        legend: str | None = None,
        variant: str = 'stacked',
        **kwargs: Any,
    ) -> str:
        """Render group of checkboxes.

        variant='button_group' styles items as an adjacent button row instead
        of stacked checkboxes -- presentation only, no change to the
        underlying independent-selection semantics. Actual visual styling
        (removing borders between adjacent items, etc.) is left to the app's
        CSS, same as every other framework-styling concern in this library.
        """
        item_class = 'checkbox-item'
        if variant == 'button_group':
            item_class += ' checkbox-item-button-group'

        checkboxes = []

        for i, option in enumerate(options):
            value = option.get('value', '')
            label = option.get('label', str(value))
            checked = option.get('checked', False)
            disabled = option.get('disabled', False)

            checkbox_id = f'{group_name}_{i}'
            checkbox_attrs = {
                'type': 'checkbox',
                'name': group_name,
                'id': checkbox_id,
                'value': value,
            }

            if checked:
                checkbox_attrs['checked'] = True
            if disabled:
                checkbox_attrs['disabled'] = True

            # Add any additional attributes from kwargs
            for attr in ['class', 'style']:
                if attr in kwargs:
                    checkbox_attrs[attr] = kwargs[attr]

            checkbox_input = CheckboxInput()
            checkbox_html = checkbox_input.render(**checkbox_attrs)

            # Wrap in label
            checkbox_item = f"""
            <div class="{item_class}">
                <label for="{checkbox_id}">
                    {checkbox_html}
                    <span class="checkbox-label">{escape(label)}</span>
                </label>
            </div>
            """
            checkboxes.append(checkbox_item)

        # Build fieldset attributes -- class always includes just the base +
        # variant modifier, deliberately NOT kwargs['class']: field_renderer.py
        # sets that to the per-item checkbox_class (e.g. Bootstrap's
        # form-check-input, sized 1em x 1em) so each individual checkbox
        # renders correctly (see the per-item loop above) -- applying that
        # same class to the *fieldset* forces the whole group's box down to
        # 1em x 1em too, and its content overflows onto whatever follows it.
        fieldset_class = 'checkbox-group'
        if variant == 'button_group':
            fieldset_class += ' checkbox-group-button-group'

        fieldset_attrs: dict[str, Any] = {'class': fieldset_class}
        for attr in ['style', 'disabled']:
            if attr in kwargs:
                fieldset_attrs[attr] = kwargs[attr]

        fieldset_attributes_str = self._build_attributes_string(fieldset_attrs)
        checkboxes_html = '\n'.join(checkboxes)
        legend_text = legend or group_name.replace('_', ' ').title()

        return substitute(
            self.template,
            fieldset_attributes=fieldset_attributes_str,
            legend=escape(legend_text),
            checkboxes=checkboxes_html,
        )


class RadioInput(FormInput):
    """Single radio button input."""

    template = """<input type="radio" ${attributes} />"""

    valid_attributes: list[str] = FormInput.valid_attributes + ['checked', 'value']

    def get_input_type(self) -> str:
        return 'radio'

    def render(self, **kwargs: Any) -> str:
        """Render a radio input element."""

        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        attributes_str = self._build_attributes_string(attrs)
        return f'<input {attributes_str} />'


class RadioGroup(SelectInputBase):
    """Group of radio button inputs for single selection."""

    ui_element: str = 'radio'

    template = """<fieldset ${fieldset_attributes}>
    <legend>${legend}</legend>
    ${radio_buttons}
</fieldset>"""

    def get_input_type(self) -> str:
        return 'radio-group'

    def render(
        self,
        options: list[dict[str, Any]],
        group_name: str,
        legend: str | None = None,
        variant: str = 'stacked',
        **kwargs: Any,
    ) -> str:
        """Render group of radio buttons.

        variant='segmented' styles items as adjacent buttons instead of
        stacked radios -- presentation only, no change to the underlying
        exclusive-choice semantics. Actual visual styling (removing borders
        between adjacent options, etc.) is left to the app's CSS, same as
        every other framework-styling concern in this library.
        """
        item_class = 'radio-item'
        if variant == 'segmented':
            item_class += ' radio-item-segmented'

        radio_buttons = []

        for i, option in enumerate(options):
            value = option.get('value', '')
            label = option.get('label', str(value))
            checked = option.get('checked', False)
            disabled = option.get('disabled', False)

            radio_id = f'{group_name}_{i}'
            radio_attrs = {'type': 'radio', 'name': group_name, 'id': radio_id, 'value': value}

            if checked:
                radio_attrs['checked'] = True
            if disabled:
                radio_attrs['disabled'] = True

            # Add any additional attributes from kwargs
            for attr in ['class', 'style']:
                if attr in kwargs:
                    radio_attrs[attr] = kwargs[attr]

            radio_input = RadioInput()
            radio_html = radio_input.render(**radio_attrs)

            # Wrap in label
            radio_item = f"""
            <div class="{item_class}">
                <label for="{radio_id}">
                    {radio_html}
                    <span class="radio-label">{escape(label)}</span>
                </label>
            </div>
            """
            radio_buttons.append(radio_item)

        # Build fieldset attributes -- class always includes just the base +
        # variant modifier, deliberately NOT kwargs['class']: field_renderer.py
        # sets that to the per-item checkbox_class (e.g. Bootstrap's
        # form-check-input, sized 1em x 1em) so each individual radio renders
        # correctly (see the per-item loop above) -- applying that same class
        # to the *fieldset* forces the whole group's box down to 1em x 1em
        # too, and its content overflows onto whatever follows it.
        fieldset_class = 'radio-group'
        if variant == 'segmented':
            fieldset_class += ' radio-group-segmented'

        fieldset_attrs: dict[str, Any] = {'class': fieldset_class}
        for attr in ['style', 'disabled']:
            if attr in kwargs:
                fieldset_attrs[attr] = kwargs[attr]

        fieldset_attributes_str = self._build_attributes_string(fieldset_attrs)
        radio_buttons_html = '\n'.join(radio_buttons)
        legend_text = legend or group_name.replace('_', ' ').title()

        return substitute(
            self.template,
            fieldset_attributes=fieldset_attributes_str,
            legend=escape(legend_text),
            radio_buttons=radio_buttons_html,
        )


class ToggleSwitch(CheckboxInput):
    """Toggle switch styled as a modern switch instead of checkbox.

    The checkbox and its slider <span> must be direct siblings for the CSS
    `input:checked + .toggle-switch-slider` selector to match -- both live
    directly inside the wrapping <label> (clicking anywhere in the label
    toggles the underlying checkbox, same as the classic W3Schools pattern).
    """

    ui_element: str = 'toggle'
    ui_element_aliases: tuple[str, ...] = ('toggle_switch', 'checkbox_toggle')

    def render(self, **kwargs: Any) -> str:
        """Render toggle switch with self-contained CSS -- no app-supplied stylesheet needed."""
        # Add toggle-specific classes
        current_class = kwargs.get('class', '')
        kwargs['class'] = f'{current_class} toggle-switch'.strip()

        field_name = kwargs.get('name', '')
        field_id = kwargs.get('id', field_name)
        label = kwargs.pop('label', None)

        checkbox_html = super().render(**kwargs)

        return f"""
        <label class="toggle-switch-wrapper toggle-switch-label" for="{field_id}">
            {checkbox_html}
            <span class="toggle-switch-slider"></span>
            {f'<span class="toggle-switch-text">{escape(label)}</span>' if label else ''}
        </label>
        <style>
        .toggle-switch-wrapper {{
            position: relative;
            display: inline-block;
            width: 46px;
            height: 24px;
            vertical-align: middle;
            cursor: pointer;
        }}
        .toggle-switch-wrapper input[type="checkbox"] {{
            opacity: 0;
            width: 0;
            height: 0;
        }}
        .toggle-switch-slider {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .3s;
            border-radius: 24px;
        }}
        .toggle-switch-slider::before {{
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
        }}
        .toggle-switch-wrapper input:checked + .toggle-switch-slider {{
            background-color: #2196F3;
        }}
        .toggle-switch-wrapper input:focus + .toggle-switch-slider {{
            box-shadow: 0 0 1px #2196F3;
        }}
        .toggle-switch-wrapper input:checked + .toggle-switch-slider::before {{
            transform: translateX(22px);
        }}
        .toggle-switch-wrapper input:disabled + .toggle-switch-slider {{
            opacity: .5;
            cursor: not-allowed;
        }}
        .toggle-switch-wrapper input:disabled {{
            cursor: not-allowed;
        }}
        .toggle-switch-text {{
            margin-left: 8px;
            vertical-align: middle;
            cursor: pointer;
        }}
        </style>
        """


class ComboBoxInput(SelectInput):
    """Combo box input that combines text input with dropdown selection."""

    ui_element: str = 'combobox'

    template = """<div class="combobox-wrapper">
    <input type="text" ${input_attributes} list="${datalist_id}" />
    <datalist id="${datalist_id}">
        ${options}
    </datalist>
    <ul class="combobox-listbox" id="${listbox_id}" role="listbox" hidden></ul>
</div>"""

    def render(
        self,
        options: list[dict[str, Any]],
        filter_mode: str = 'contains',
        min_chars: int = 0,
        **kwargs: Any,
    ) -> str:
        """Render combo box with a native datalist fallback plus a JS-filtered listbox.

        The <input list=...> + <datalist> pair stays exactly as before (the no-JS
        fallback). The listbox reads its option data straight from the sibling
        <datalist> — no duplicated option list to keep in sync.
        """
        field_name = kwargs.get('name', '')
        field_id = kwargs.get('id', field_name)
        kwargs.setdefault('id', field_id)
        datalist_id = f'{field_name}_datalist'
        listbox_id = f'{field_name}_listbox'

        # Build options for datalist
        options_html = ''
        for option in options:
            if isinstance(option, dict):
                value = option.get('value', '')
                label = option.get('label', str(value))
                options_html += f'<option value="{escape(str(value))}">{escape(label)}</option>\n'
            else:
                options_html += f'<option value="{escape(str(option))}"></option>\n'

        # Build input attributes
        input_attrs = self.validate_attributes(**kwargs)
        if 'type' in input_attrs:
            del input_attrs['type']
        input_attributes_str = self._build_attributes_string(input_attrs)

        combo_html = substitute(
            self.template,
            input_attributes=input_attributes_str,
            datalist_id=datalist_id,
            options=options_html,
            listbox_id=listbox_id,
        )

        if not field_id:
            return combo_html

        script = f"""
<script>
document.addEventListener('DOMContentLoaded', function() {{
    const input = document.getElementById('{field_id}');
    const datalist = document.getElementById('{datalist_id}');
    const listbox = document.getElementById('{listbox_id}');
    if (!input || !datalist || !listbox) return;

    const filterMode = {json.dumps(filter_mode)};
    const minChars = {min_chars};
    let activeIndex = -1;

    function renderListbox() {{
        const query = input.value.trim().toLowerCase();
        listbox.innerHTML = '';
        activeIndex = -1;
        if (query.length < minChars) {{
            listbox.hidden = true;
            return;
        }}
        Array.from(datalist.options).forEach(function(opt) {{
            const label = (opt.textContent || opt.value).toLowerCase();
            const matches = filterMode === 'startswith' ? label.startsWith(query) : label.includes(query);
            if (query && !matches) return;
            const li = document.createElement('li');
            li.textContent = opt.textContent || opt.value;
            li.dataset.value = opt.value;
            li.setAttribute('role', 'option');
            li.addEventListener('mousedown', function(e) {{
                e.preventDefault();
                input.value = opt.value;
                listbox.hidden = true;
            }});
            listbox.appendChild(li);
        }});
        listbox.hidden = listbox.children.length === 0;
    }}

    function setActive(index) {{
        Array.from(listbox.children).forEach(function(li, i) {{
            li.classList.toggle('combobox-option-active', i === index);
        }});
        activeIndex = index;
    }}

    input.addEventListener('input', renderListbox);
    input.addEventListener('focus', renderListbox);
    input.addEventListener('keydown', function(e) {{
        const opts = Array.from(listbox.children);
        if (e.key === 'ArrowDown') {{
            e.preventDefault();
            if (opts.length) setActive((activeIndex + 1) % opts.length);
        }} else if (e.key === 'ArrowUp') {{
            e.preventDefault();
            if (opts.length) setActive((activeIndex - 1 + opts.length) % opts.length);
        }} else if (e.key === 'Enter' && activeIndex >= 0 && opts[activeIndex]) {{
            e.preventDefault();
            input.value = opts[activeIndex].dataset.value;
            listbox.hidden = true;
        }} else if (e.key === 'Escape') {{
            listbox.hidden = true;
        }}
    }});
    document.addEventListener('click', function(e) {{
        if (e.target !== input) {{
            listbox.hidden = true;
        }}
    }});
}});
</script>
"""
        return combo_html + script
