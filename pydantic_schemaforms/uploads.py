"""Uploaded files: the value type for file fields and the server-side limits on them.

Type a field ``UploadedFile`` (one file) or ``list[UploadedFile]`` (several) and
it renders as a file input; ``FormModel.validate()`` turns the framework's own
upload object (Starlette's ``UploadFile``, Werkzeug's ``FileStorage``) into an
``UploadedFile``. ``Field(ui_max_size=..., ui_max_files=...)`` and
``ui_options={"accept": ...}`` are checked on the server, so their messages land
under the field like any other error.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import types
from dataclasses import dataclass
from typing import IO, Any, Union, get_args, get_origin

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.fields import FieldInfo
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import PydanticCustomError, core_schema

_SPOOL_BYTES = 1024 * 1024


class UploadedFile:
    """A file submitted through a form.

    ``filename`` and ``content_type`` are what the browser sent, so they are
    hints, not facts: store the file under a name you generate, check its
    content before you trust it, and escape ``filename`` before putting it in
    HTML (``html(t"...")`` does).
    """

    def __init__(self, filename: str, content_type: str, file: IO[bytes]) -> None:
        self.filename = filename
        self.content_type = content_type
        self.file = file

    @classmethod
    def from_upload(cls, upload: Any) -> UploadedFile:
        """Wrap a Starlette ``UploadFile``, Werkzeug ``FileStorage`` or anything shaped like them."""

        stream = _stream_of(upload)
        if stream is None:
            raise TypeError(f'{type(upload).__name__} is not an uploaded file')
        if not _is_seekable(stream):
            # size needs to seek to the end and back, so copy a one-pass stream first.
            buffer = tempfile.SpooledTemporaryFile(max_size=_SPOOL_BYTES)
            shutil.copyfileobj(stream, buffer)
            buffer.seek(0)
            stream = buffer
        content_type = str(getattr(upload, 'content_type', None) or '')
        return cls(
            filename=str(getattr(upload, 'filename', None) or ''),
            content_type=content_type.split(';', 1)[0].strip().lower(),
            file=stream,
        )

    @property
    def size(self) -> int:
        """The file's size in bytes, measured from the file, not taken from the request."""

        position = self.file.tell()
        self.file.seek(0, os.SEEK_END)
        end = self.file.tell()
        self.file.seek(position)
        return end

    def read(self, size: int = -1) -> bytes:
        return self.file.read(size)

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        return self.file.seek(offset, whence)

    def __repr__(self) -> str:
        return (
            f'UploadedFile(filename={self.filename!r}, content_type={self.content_type!r}, '
            f'size={self.size})'
        )

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            _to_uploaded_file,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda value: value.filename, when_used='json'
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # format "binary" alone also describes bytes fields; ui_element marks a file input.
        return {'type': 'string', 'format': 'binary', 'ui_element': 'file'}


def _stream_of(upload: Any) -> IO[bytes] | None:
    for attribute in ('file', 'stream'):
        stream = getattr(upload, attribute, None)
        if callable(getattr(stream, 'read', None)):
            return stream
    return None


def _is_seekable(stream: Any) -> bool:
    seekable = getattr(stream, 'seekable', None)
    return bool(seekable()) if callable(seekable) else False


def is_upload(value: Any) -> bool:
    """Whether *value* is an uploaded file, as ours or as the web framework's object."""

    return isinstance(value, UploadedFile) or (
        hasattr(value, 'filename') and _stream_of(value) is not None
    )


def is_blank_upload(value: Any) -> bool:
    """Whether a file input was left empty: Starlette sends ``""``, Werkzeug an unnamed file."""

    if isinstance(value, list):
        return bool(value) and all(is_blank_upload(item) for item in value)
    return value == '' or (is_upload(value) and not value.filename)


def _to_uploaded_file(value: Any) -> UploadedFile:
    if isinstance(value, UploadedFile):
        return value
    if is_upload(value) and value.filename:
        return UploadedFile.from_upload(value)
    if value == '' or is_upload(value):
        raise PydanticCustomError('file_missing', 'Choose a file to upload.')
    raise PydanticCustomError('file_type', 'Expected an uploaded file.')


def mentions_uploaded_file(annotation: Any) -> bool:
    if annotation is UploadedFile:
        return True
    return any(mentions_uploaded_file(arg) for arg in get_args(annotation))


def _allows_several(annotation: Any) -> bool:
    if get_origin(annotation) is list:
        return any(mentions_uploaded_file(arg) for arg in get_args(annotation))
    return any(_allows_several(arg) for arg in get_args(annotation))


def is_upload_annotation(annotation: Any) -> bool:
    """Whether a field is typed as ``UploadedFile`` or a list of them, optionally ``| None``."""

    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        return any(
            is_upload_annotation(arg) for arg in get_args(annotation) if arg is not type(None)
        )
    if origin is list:
        return get_args(annotation)[:1] == (UploadedFile,)
    return annotation is UploadedFile


def format_size(size: int) -> str:
    """``5242880`` -> ``"5 MB"``, in the 1024-based units file pickers use."""

    amount = float(size)
    units = ['bytes', 'KB', 'MB', 'GB']
    while amount >= 1024 and len(units) > 1:
        amount /= 1024
        units.pop(0)
    text = f'{amount:.1f}'.removesuffix('.0')
    return '1 byte' if size == 1 else f'{text} {units[0]}'


def _accept_tokens(accept: str) -> list[str]:
    return [token.strip().lower() for token in accept.split(',') if token.strip()]


def accepts(accept: str, upload: UploadedFile) -> bool:
    """Whether *upload* matches an ``accept`` list by extension or content type, as the browser does."""

    tokens = _accept_tokens(accept)
    name = upload.filename.lower()
    mime = upload.content_type
    for token in tokens:
        if token.startswith('.'):
            if name.endswith(token):
                return True
        elif token.endswith('/*'):
            if mime.startswith(token[:-1]):
                return True
        elif token == mime:
            return True
    return not tokens


@dataclass(frozen=True)
class _UploadLimits:
    """Pydantic metadata ``Field()`` adds for a file field's limits; see ``attach_upload_limits``."""

    max_size: int | None
    max_files: int | None
    accept: str | None

    def __get_pydantic_core_schema__(
        self, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        schema = handler(source)
        if not mentions_uploaded_file(source):
            if self.max_size is not None or self.max_files is not None:
                raise TypeError(
                    'ui_max_size and ui_max_files check uploaded files, so type the field '
                    f'UploadedFile or list[UploadedFile], not {source!r}'
                )
            # accept on a field that isn't UploadedFile only filters the browser's picker.
            return schema
        if self.max_files is not None and not _allows_several(source):
            raise TypeError('ui_max_files needs a list[UploadedFile] field')
        return core_schema.no_info_after_validator_function(self._check, schema)

    def _check(self, value: Any) -> Any:
        if isinstance(value, list):
            files = value
        elif value is None:
            files = []
        else:
            files = [value]
        if self.max_files is not None and len(files) > self.max_files:
            noun = 'file' if self.max_files == 1 else 'files'
            raise PydanticCustomError(
                'too_many_files',
                'Choose at most {max_files} ' + noun + '.',
                {'max_files': self.max_files},
            )
        for upload in files:
            if self.accept and not accepts(self.accept, upload):
                raise PydanticCustomError(
                    'file_not_accepted',
                    '{filename} is not an accepted file type. Accepted: {accepted}.',
                    {
                        'filename': upload.filename,
                        'accepted': ', '.join(_accept_tokens(self.accept)),
                    },
                )
            if self.max_size is not None and upload.size > self.max_size:
                raise PydanticCustomError(
                    'file_too_large',
                    '{filename} is larger than {limit}.',
                    {'filename': upload.filename, 'limit': format_size(self.max_size)},
                )
        return value


def check_upload_limits(ui_max_size: Any, ui_max_files: Any) -> None:
    for name, value in (('ui_max_size', ui_max_size), ('ui_max_files', ui_max_files)):
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 1
        ):
            raise ValueError(f'{name} must be a whole number of at least 1, not {value!r}')


def attach_upload_limits(field_info: FieldInfo, extra: dict[str, Any]) -> FieldInfo:
    """Have Pydantic check a file field's ``ui_max_size``, ``ui_max_files`` and ``accept``.

    Added as field metadata, so the check runs wherever Pydantic validates the
    model, including sub-forms and list items, with the error at the field.
    """

    options = extra.get('ui_options')
    accept = options.get('accept') if isinstance(options, dict) else None
    max_size = extra.get('ui_max_size')
    max_files = extra.get('ui_max_files')
    if max_size is None and max_files is None and not accept:
        return field_info
    field_info.metadata.append(
        _UploadLimits(max_size, max_files, accept if isinstance(accept, str) else None)
    )
    return field_info
