"""Step-by-step saving for the wizard: ``wizard_options={"save_steps": True}``.

Each step is its own page and POST. ``FormModel.validate_step()`` checks the
step just submitted against the app's saved draft and returns a
``WizardStepResult``; the app stores ``result.draft`` and renders the result.

The draft holds what was submitted, not validated values: a step is checked by
validating the whole model on the draft plus that step and keeping only that
step's errors. (Pydantic runs ``@model_validator(mode="after")`` even for a
single-field assignment, so a field-by-field check would fire cross-step
validators on half a model.) The final submit is an ordinary full validation.
"""

from __future__ import annotations

import asyncio
import io
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .error_tree import has_errors
from .uploads import UploadedFile, is_upload

if TYPE_CHECKING:
    from .schema_form import FormModel

# Wire names, owned by the library: apps never read or write them.
STEP_FIELD = '_sf_wizard_step'
ACTION_FIELD = '_sf_wizard'
# The data a review_step wizard was first rendered with, carried through a failed
# submit so the review still marks what changed since then.
ORIGINAL_FIELD = '_sf_original'
_SAVED_FILE_KEY = '__sf_saved_file__'
_DRAFT_VERSION = 1


class SavedFile(UploadedFile):
    """A file accepted on an earlier step, in a ``save_steps`` wizard's final data.

    Its content was handed to the app on the step it was uploaded; ``ref`` is
    whatever the app set on that ``UploadedFile`` to find it again.
    """

    def __init__(self, filename: str, content_type: str, size: int, ref: Any = None) -> None:
        super().__init__(filename, content_type, io.BytesIO())
        self._size = size
        self.ref = ref

    @property
    def size(self) -> int:
        return self._size

    def read(self, size: int = -1) -> bytes:
        raise OSError(
            f'{self.filename} was uploaded on an earlier step; read it from where the app '
            'stored it (its ref is SavedFile.ref).'
        )


@dataclass
class StepState:
    """Where a ``save_steps`` wizard is: its data so far, current and furthest step."""

    data: dict[str, Any] = field(default_factory=dict)
    step: int = 0
    reached: int = 0

    @classmethod
    def from_draft(cls, draft: Any) -> StepState:
        if draft is None:
            return cls()
        if not isinstance(draft, dict) or draft.get('version') != _DRAFT_VERSION:
            raise ValueError(
                'draft= must be a result.draft from FormModel.validate_step(), stored unchanged'
            )
        step = _whole_number(draft.get('step'))
        return cls(
            data=_from_json(draft.get('data') or {}),
            step=step,
            reached=max(step, _whole_number(draft.get('reached'))),
        )

    def to_draft(self) -> dict[str, Any]:
        return {
            'version': _DRAFT_VERSION,
            'step': self.step,
            'reached': self.reached,
            'data': _to_json(self.data),
        }


def _whole_number(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _to_json(value: Any) -> Any:
    """The draft's stored form: uploads become their details, everything else stays."""

    if isinstance(value, dict):
        return {key: _to_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_json(item) for item in value]
    if isinstance(value, UploadedFile):
        return {
            _SAVED_FILE_KEY: {
                'filename': value.filename,
                'content_type': value.content_type,
                'size': value.size,
                'ref': getattr(value, 'ref', None),
            }
        }
    return value


def _from_json(value: Any) -> Any:
    if isinstance(value, dict):
        saved = value.get(_SAVED_FILE_KEY)
        if isinstance(saved, dict) and len(value) == 1:
            return SavedFile(
                str(saved.get('filename') or ''),
                str(saved.get('content_type') or ''),
                _whole_number(saved.get('size')),
                saved.get('ref'),
            )
        return {key: _from_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_from_json(item) for item in value]
    return value


def original_to_json(data: Any) -> str:
    from pydantic_core import to_jsonable_python

    return json.dumps(to_jsonable_python(_to_json(data), fallback=str))


def original_from_json(text: Any) -> Any:
    """The starting values back from ``ORIGINAL_FIELD``; None if absent or unreadable."""

    if not isinstance(text, str) or not text:
        return None
    try:
        return _from_json(json.loads(text))
    except ValueError:
        return None


def _is_blank(value: Any) -> bool:
    from .uploads import is_blank_upload

    return is_blank_upload(value)


def _keep_saved_files(new: Any, old: Any) -> Any:
    """A file input left empty on a revisited step keeps the file saved earlier."""

    if isinstance(old, SavedFile) and _is_blank(new):
        return old
    if isinstance(new, dict) and isinstance(old, dict):
        merged = dict(new)
        for key, old_item in old.items():
            if key in new:
                merged[key] = _keep_saved_files(new[key], old_item)
            elif _contains_saved_file(old_item):
                merged[key] = old_item
        return merged
    if isinstance(new, list) and isinstance(old, list):
        return [
            _keep_saved_files(item, old[index]) if index < len(old) else item
            for index, item in enumerate(new)
        ]
    return new


def _contains_saved_file(value: Any) -> bool:
    if isinstance(value, SavedFile):
        return True
    if isinstance(value, dict):
        return any(_contains_saved_file(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_saved_file(item) for item in value)
    return False


def _new_uploads(value: Any) -> list[UploadedFile]:
    if isinstance(value, SavedFile):
        return []
    if isinstance(value, UploadedFile):
        return [value]
    if isinstance(value, dict):
        return [upload for item in value.values() for upload in _new_uploads(item)]
    if isinstance(value, list):
        return [upload for item in value for upload in _new_uploads(item)]
    return []


def _with_uploads(value: Any) -> Any:
    """Turn the framework's upload objects into ``UploadedFile`` so the app can tag them."""

    if isinstance(value, dict):
        return {key: _with_uploads(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_with_uploads(item) for item in value]
    if is_upload(value) and not isinstance(value, UploadedFile) and value.filename:
        return UploadedFile.from_upload(value)
    return value


def step_field_names(
    model_cls: type[FormModel], wizard_options: dict[str, Any] | None = None
) -> list[list[str]]:
    """The top-level field names on each wizard step, in order. A review step
    (``review_step``) comes last and has none."""

    from .enhanced_renderer import _general_group_title
    from .rendering.layout_engine import LayoutEngine
    from .rendering.schema_parser import build_schema_metadata

    metadata = build_schema_metadata(model_cls)
    groups = LayoutEngine.group_fields(
        metadata, 'wizard', _general_group_title(model_cls, metadata)
    )
    from .rendering.layout_engine import review_options

    steps = [[name for name, _schema in fields] for _title, fields in groups]
    return [*steps, []] if review_options(wizard_options) else steps


def check_save_steps(render_kwargs: dict[str, Any]) -> None:
    options = render_kwargs.get('wizard_options') or {}
    if render_kwargs.get('layout') != 'wizard' or not options.get('save_steps'):
        raise ValueError(
            "validate_step() needs layout='wizard' and wizard_options={'save_steps': True}, "
            'the same options the form was rendered with.'
        )


def _parse_action(raw: Any, step: int, reached: int, last: int) -> tuple[str, int]:
    """The button pressed, as (kind, target step).

    No action (Enter in a field, the form's own submit button) means Next, and
    Next on the last step is the final submit. Submit counts only on the last
    step, and a jump only to a step already reached, so an edited request can't
    skip ahead; anything else just shows the current step again.
    """

    action = raw if isinstance(raw, str) else ''
    if action == 'back':
        return 'back', max(step - 1, 0)
    if action.startswith('goto:') and action[5:].isdigit():
        target = int(action[5:])
        return (
            ('goto', target) if target != step and target <= min(reached, last) else ('stay', step)
        )
    if step >= last:
        return 'submit', last
    return 'next', step + 1


@dataclass
class WizardStepResult:
    """What ``FormModel.validate_step()`` found, and the page to show next."""

    form_model_cls: Any
    is_valid: bool
    is_complete: bool
    data: dict[str, Any]
    errors: dict[Any, Any]
    files: list[UploadedFile]
    step: int
    _state: StepState
    _render_state: StepState
    _render_errors: dict[Any, Any]
    _submit_url: str | None = None
    _framework: str = 'bootstrap'
    _render_kwargs: dict[str, Any] = field(default_factory=dict)

    @property
    def draft(self) -> dict[str, Any]:
        """The wizard's progress to store as-is and pass back as ``draft=``.

        Read it after storing this step's files, so a ``ref`` set on each
        ``UploadedFile`` is kept.
        """

        return self._state.to_draft()

    def render(self, framework: str | None = None, **kwargs: Any) -> str:
        """The next step, or this step again with its errors."""

        if self.is_complete:
            raise ValueError('The wizard is complete; there is no step left to render.')
        url = kwargs.pop('submit_url', None) or self._submit_url
        if not url:
            raise ValueError('submit_url is required. Pass it to validate_step() or here.')
        options = {**self._render_kwargs, **kwargs}
        options['draft'] = self._render_state.to_draft()
        return self.form_model_cls.render_form(
            errors=self._render_errors,
            framework=framework or self._framework,
            submit_url=url,
            **options,
        )

    async def render_async(self, framework: str | None = None, **kwargs: Any) -> str:
        return await asyncio.to_thread(self.render, framework, **kwargs)


def validate_step(
    model_cls: type[FormModel],
    raw: Any,
    *,
    draft: Any,
    submit_url: str | None,
    framework: str,
    render_kwargs: dict[str, Any],
) -> WizardStepResult:
    from .form_data import decode_submission
    from .validation import validate_form_data

    check_save_steps(render_kwargs)
    steps = step_field_names(model_cls, render_kwargs.get('wizard_options'))
    last = len(steps) - 1
    saved = StepState.from_draft(draft)

    submission = decode_submission(raw)
    step = min(_whole_number(_as_int(submission.pop(STEP_FIELD, None))), last)
    kind, target = _parse_action(
        submission.pop(ACTION_FIELD, None), step, max(saved.reached, step), last
    )
    linear = (render_kwargs.get('wizard_options') or {}).get('linear', True)

    step_names = set(steps[step])
    submitted = {
        name: _keep_saved_files(_with_uploads(submission[name]), saved.data.get(name))
        for name in step_names
        if name in submission
    }
    for name in step_names - set(submitted):
        if _contains_saved_file(saved.data.get(name)):
            submitted[name] = saved.data[name]
    merged = {
        **{key: value for key, value in saved.data.items() if key not in step_names},
        **submitted,
    }
    result = validate_form_data(model_cls, merged, from_form=True)
    step_errors = {key: value for key, value in result.errors.items() if key in step_names}
    step_valid = not has_errors(step_errors)

    common = {
        'form_model_cls': model_cls,
        'files': _new_uploads(submitted) if step_valid else [],
        '_submit_url': submit_url,
        '_framework': framework,
        '_render_kwargs': render_kwargs,
    }

    if kind == 'submit':
        if result.is_valid:
            done = StepState(merged, last, last)
            return WizardStepResult(
                is_valid=True,
                is_complete=True,
                data=result.data,
                errors={},
                step=last,
                _state=done,
                _render_state=done,
                _render_errors={},
                **common,
            )
        failed = _first_step_with_errors(steps, result.errors, default=last)
        state = StepState(merged if step_valid else saved.data, step, saved.reached)
        return WizardStepResult(
            is_valid=step_valid,
            is_complete=False,
            data=merged,
            errors=result.errors,
            step=failed,
            _state=state,
            _render_state=StepState(merged, failed, max(saved.reached, step)),
            _render_errors=result.errors,
            **common,
        )

    # Next, a linear jump forward and "stay" need a valid step; Back never blocks.
    blocks = kind in ('next', 'stay') or (kind == 'goto' and target > step and linear)
    if not step_valid and blocks:
        stay = StepState(merged, step, saved.reached)
        return WizardStepResult(
            is_valid=False,
            is_complete=False,
            data=merged,
            errors=step_errors,
            step=step,
            _state=StepState(saved.data, step, saved.reached),
            _render_state=stay,
            _render_errors=step_errors,
            **common,
        )

    # A valid step is kept; invalid input on a step being left is dropped.
    data = merged if step_valid else saved.data
    moved = StepState(data, target, max(saved.reached, target))
    return WizardStepResult(
        is_valid=step_valid,
        is_complete=False,
        data=data,
        errors=step_errors,
        step=target,
        _state=moved,
        _render_state=moved,
        _render_errors={},
        **common,
    )


def _as_int(value: Any) -> Any:
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def _first_step_with_errors(steps: list[list[str]], errors: dict[Any, Any], *, default: int) -> int:
    for index, names in enumerate(steps):
        if any(has_errors(errors.get(name)) for name in names):
            return index
    return default
