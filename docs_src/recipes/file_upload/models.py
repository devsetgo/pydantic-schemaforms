from typing import Any

from pydantic_schemaforms import Field, FormModel


class UploadForm(FormModel):
    title: str = Field(title='Title', min_length=2)
    document: Any = Field(
        None,
        title='Document',
        description='PDF or Word, up to 5 MB.',
        ui_element='file',
        ui_options={'accept': '.pdf,.docx'},
    )


ALLOWED_TYPES = {'.pdf', '.docx'}
MAX_BYTES = 5 * 1024 * 1024
