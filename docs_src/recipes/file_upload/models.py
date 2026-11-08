from pydantic_schemaforms import Field, FormModel, UploadedFile

MAX_BYTES = 5 * 1024 * 1024


class UploadForm(FormModel):
    title: str = Field(title='Title', min_length=2)
    document: UploadedFile = Field(
        title='Document',
        description='PDF or Word, up to 5 MB.',
        ui_max_size=MAX_BYTES,
        ui_options={'accept': '.pdf,.docx'},
    )
