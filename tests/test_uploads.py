"""UploadedFile and the server-side upload limits (#242)."""

import io
import re
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from flask import Flask, request as flask_request
from werkzeug.datastructures import CombinedMultiDict, FileStorage

from pydantic_schemaforms import (
    Field,
    FormField,
    FormModel,
    UploadedFile,
    render_form_html,
)
from pydantic_schemaforms.uploads import accepts, format_size

EMPTY_PART = ('', b'', 'application/octet-stream')


class Reference(FormModel):
    name: str = Field(title='Name')
    letter: UploadedFile | None = Field(None, title='Letter', ui_max_size=5)


class Proof(FormModel):
    scan: UploadedFile = Field(title='Scan', ui_options={'accept': '.pdf'})


class Application(FormModel):
    resume: UploadedFile = Field(title='Resume', ui_max_size=10, ui_options={'accept': '.pdf'})
    cover: UploadedFile | None = Field(None, title='Cover letter')
    photos: list[UploadedFile] = Field(
        default_factory=list, title='Photos', ui_max_files=2, ui_options={'accept': 'image/*'}
    )


class Nested(FormModel):
    proof: Proof = Field(title='Proof')
    references: list[Reference] = Field(default_factory=list, title='References')


def _upload(name: str, content: bytes = b'x', content_type: str = 'application/pdf') -> Any:
    return FileStorage(io.BytesIO(content), filename=name, content_type=content_type)


def _fastapi_client(model: type[FormModel], seen: dict[str, Any]) -> TestClient:
    app = FastAPI()

    @app.post('/')
    async def submit(request: Request) -> dict[str, Any]:
        result = model.validate(await request.form(), submit_url='/')
        seen['result'] = result
        if result.is_valid:
            seen['contents'] = {
                name: value.read()
                for name, value in result.data.items()
                if isinstance(value, UploadedFile)
            }
        return {'valid': result.is_valid, 'errors': result.errors}

    return TestClient(app)


def _flask_post(model: type[FormModel], data: dict[str, Any]) -> dict[str, Any]:
    app = Flask(__name__)
    seen: dict[str, Any] = {}

    @app.post('/')
    def submit() -> dict[str, Any]:
        result = model.validate(
            CombinedMultiDict([flask_request.form, flask_request.files]), submit_url='/'
        )
        seen['result'] = result
        # Flask closes the uploaded files once the request ends.
        sizes = {
            name: value.size
            for name, value in (result.data or {}).items()
            if isinstance(value, UploadedFile)
        }
        return {'valid': result.is_valid, 'errors': result.errors, 'sizes': sizes}

    body = app.test_client().post('/', data=data, content_type='multipart/form-data').json
    assert body is not None
    return {**body, 'result': seen['result']}


def test_fastapi_upload_becomes_an_uploaded_file() -> None:
    seen: dict[str, Any] = {}
    response = _fastapi_client(Application, seen).post(
        '/',
        files=[
            ('resume', ('cv.pdf', b'12345', 'application/pdf; charset=binary')),
            ('cover', EMPTY_PART),
            ('photos', ('a.png', b'1', 'image/png')),
        ],
    )
    assert response.json() == {'valid': True, 'errors': {}}
    data = seen['result'].data
    resume = data['resume']
    assert isinstance(resume, UploadedFile)
    assert (resume.filename, resume.content_type, resume.size) == ('cv.pdf', 'application/pdf', 5)
    assert seen['contents']['resume'] == b'12345'
    assert data['cover'] is None
    assert [photo.filename for photo in data['photos']] == ['a.png']


def test_flask_upload_becomes_an_uploaded_file() -> None:
    body = _flask_post(
        Application,
        {
            'resume': (io.BytesIO(b'123'), 'cv.pdf', 'application/pdf'),
            'cover': (io.BytesIO(b''), ''),
            'photos': [
                (io.BytesIO(b'1'), 'a.png', 'image/png'),
                (io.BytesIO(b'2'), 'b.jpg', 'image/jpeg'),
            ],
        },
    )
    assert body['valid'], body['errors']
    data = body['result'].data
    # Werkzeug reports content_length 0 for a file part, so size is measured from the file.
    assert body['sizes'] == {'resume': 3}
    assert data['cover'] is None
    assert [photo.filename for photo in data['photos']] == ['a.png', 'b.jpg']


@pytest.mark.parametrize('framework', ['fastapi', 'flask'])
def test_empty_file_inputs_are_not_submitted(framework: str) -> None:
    if framework == 'fastapi':
        seen: dict[str, Any] = {}
        errors = (
            _fastapi_client(Application, seen)
            .post(
                '/', files=[('resume', EMPTY_PART), ('cover', EMPTY_PART), ('photos', EMPTY_PART)]
            )
            .json()['errors']
        )
    else:
        empty = (io.BytesIO(b''), '')
        errors = _flask_post(Application, {'resume': empty, 'cover': empty, 'photos': empty})[
            'errors'
        ]
    assert errors == {'resume': 'Field required'}


def test_limits_report_friendly_messages_under_each_field() -> None:
    seen: dict[str, Any] = {}
    errors = (
        _fastapi_client(Application, seen)
        .post(
            '/',
            files=[
                ('resume', ('cv.pdf', b'x' * 11, 'application/pdf')),
                ('photos', ('a.png', b'1', 'image/png')),
                ('photos', ('b.png', b'1', 'image/png')),
                ('photos', ('c.png', b'1', 'image/png')),
            ],
        )
        .json()['errors']
    )
    assert errors == {
        'resume': 'cv.pdf is larger than 10 bytes.',
        'photos': 'Choose at most 2 files.',
    }


def test_accept_is_checked_on_the_server() -> None:
    seen: dict[str, Any] = {}
    errors = (
        _fastapi_client(Application, seen)
        .post(
            '/',
            files=[
                ('resume', ('cv.exe', b'1', 'application/pdf')),
                ('photos', ('notes.txt', b'1', 'text/plain')),
            ],
        )
        .json()['errors']
    )
    assert errors == {
        'resume': 'cv.exe is not an accepted file type. Accepted: .pdf.',
        'photos': 'notes.txt is not an accepted file type. Accepted: image/*.',
    }


@pytest.mark.parametrize(
    ('accept', 'filename', 'content_type', 'expected'),
    [
        ('.pdf,.docx', 'CV.PDF', 'application/octet-stream', True),
        ('.tar.gz', 'site.tar.gz', 'application/gzip', True),
        ('image/*', 'photo', 'image/heic', True),
        ('application/pdf', 'cv', 'application/pdf', True),
        ('.pdf, image/*', 'cv.doc', 'application/msword', False),
        ('image/*', 'imagefile.txt', 'text/plain', False),
        ('application/pdf', 'cv.pdf', 'text/plain', False),
    ],
)
def test_accept_matches_like_the_browser(
    accept: str, filename: str, content_type: str, expected: bool
) -> None:
    upload = UploadedFile(filename, content_type, io.BytesIO(b''))
    assert accepts(accept, upload) is expected


def test_errors_land_inside_sub_forms_and_list_items() -> None:
    body = _flask_post(
        Nested,
        {
            'proof.scan': (io.BytesIO(b'1'), 'scan.doc', 'application/msword'),
            'references[0].name': 'Bo',
            'references[0].letter': (io.BytesIO(b'123456'), 'letter.pdf', 'application/pdf'),
        },
    )
    assert body['errors'] == {
        'proof': {'scan': 'scan.doc is not an accepted file type. Accepted: .pdf.'},
        'references': {'0': {'letter': 'letter.pdf is larger than 5 bytes.'}},
    }


def test_limits_apply_outside_validate_too() -> None:
    with pytest.raises(ValueError, match='larger than 5 bytes'):
        Reference(name='Bo', letter=UploadedFile('l.pdf', 'application/pdf', io.BytesIO(b'123456')))


def test_an_uploaded_file_type_renders_as_a_file_input() -> None:
    html = render_form_html(Application, submit_url='/')
    assert 'enctype="multipart/form-data"' in html
    inputs = {
        name: tag
        for tag in re.findall(r'<input[^>]*type="file"[^>]*>', html)
        if (name := re.search(r'name="([^"]+)"', tag).group(1))  # type: ignore[union-attr]
    }
    assert set(inputs) == {'resume', 'cover', 'photos'}
    assert 'multiple' in inputs['photos']
    assert 'multiple' not in inputs['resume']
    assert 'accept=".pdf"' in inputs['resume']


def test_a_bytes_field_still_renders_as_text() -> None:
    class Blob(FormModel):
        payload: bytes = Field(b'', title='Payload')

    html = render_form_html(Blob, submit_url='/')
    assert 'type="file"' not in html


def test_rerender_escapes_the_filename_and_never_prefills_the_input() -> None:
    body = _flask_post(
        Application,
        {'resume': (io.BytesIO(b'1'), '<script>x</script>.exe', 'application/x-msdownload')},
    )
    html = body['result'].render_with_errors()
    assert '<script>x</script>' not in html
    assert '&lt;script&gt;x&lt;/script&gt;.exe is not an accepted file type' in html
    assert 'FileStorage' not in html
    assert not re.search(r'<input[^>]*type="file"[^>]*value=', html)


def test_display_and_json_show_the_filename() -> None:
    upload = UploadedFile('cv.pdf', 'application/pdf', io.BytesIO(b'1'))
    model = Application(resume=upload)
    assert model.model_dump()['resume'] is upload
    assert '"resume":"cv.pdf"' in model.model_dump_json()
    assert 'cv.pdf' in Application.render_display(model.model_dump())


def test_form_field_takes_the_same_limits() -> None:
    class Legacy(FormModel):
        attachment: UploadedFile = FormField(title='Attachment', ui_max_size=2)

    with pytest.raises(ValueError, match='larger than 2 bytes'):
        Legacy(attachment=UploadedFile('a.txt', 'text/plain', io.BytesIO(b'123')))


def test_accept_on_an_untyped_file_field_stays_a_browser_hint() -> None:
    class Old(FormModel):
        document: Any = Field(None, ui_element='file', ui_options={'accept': '.pdf'})

    assert Old(document='anything.exe').document == 'anything.exe'


def test_limits_need_an_uploaded_file_field() -> None:
    with pytest.raises(TypeError, match='type the field UploadedFile'):

        class _Wrong(FormModel):
            name: str = Field('', ui_max_size=10)

    with pytest.raises(TypeError, match=r'ui_max_files needs a list\[UploadedFile\]'):

        class _Single(FormModel):
            doc: UploadedFile | None = Field(None, ui_max_files=2)


@pytest.mark.parametrize('bad', [0, -1, 1.5, True, '5MB'])
def test_limits_must_be_positive_whole_numbers(bad: Any) -> None:
    with pytest.raises(ValueError, match='ui_max_size must be a whole number'):
        Field(None, ui_max_size=bad)


def test_a_plain_value_is_not_an_upload() -> None:
    with pytest.raises(ValueError, match='Expected an uploaded file'):
        Application(resume='cv.pdf')  # type: ignore[arg-type]


def test_a_one_pass_stream_is_copied_so_size_works() -> None:
    class OnePass(io.RawIOBase):
        def __init__(self) -> None:
            self._data = io.BytesIO(b'abcdef')

        def readable(self) -> bool:
            return True

        def readinto(self, buffer: Any) -> int:
            chunk = self._data.read(len(buffer))
            buffer[: len(chunk)] = chunk
            return len(chunk)

    class Upload:
        filename = 'a.bin'
        content_type = None
        file = OnePass()

    uploaded = UploadedFile.from_upload(Upload())
    assert uploaded.content_type == ''
    assert uploaded.size == 6
    assert uploaded.read() == b'abcdef'


@pytest.mark.parametrize(
    ('size', 'text'),
    [
        (1, '1 byte'),
        (1023, '1023 bytes'),
        (1536, '1.5 KB'),
        (5 * 1024 * 1024, '5 MB'),
        (3 * 1024**3, '3 GB'),
    ],
)
def test_format_size(size: int, text: str) -> None:
    assert format_size(size) == text


def test_a_blank_upload_outside_a_form_asks_for_a_file() -> None:
    blank = FileStorage(io.BytesIO(b''), filename='')
    with pytest.raises(ValueError, match='Choose a file to upload'):
        Application(resume=blank)  # type: ignore[arg-type]


def test_from_upload_rejects_an_object_without_a_stream() -> None:
    with pytest.raises(TypeError, match='str is not an uploaded file'):
        UploadedFile.from_upload('cv.pdf')


def test_seek_rewinds_the_file() -> None:
    upload = UploadedFile('a.txt', 'text/plain', io.BytesIO(b'abc'))
    assert upload.read() == b'abc'
    assert upload.seek(0) == 0
    assert upload.read(1) == b'a'


def test_an_optional_limited_field_can_be_left_empty() -> None:
    assert Reference(name='Bo', letter=None).letter is None
