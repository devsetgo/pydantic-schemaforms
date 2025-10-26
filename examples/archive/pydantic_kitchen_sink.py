from pydantic import (  # PaymentCardNumber,
    UUID4,
    AwareDatetime,
    BaseModel,
    ByteSize,
    DirectoryPath,
    Field,
    FilePath,
    FiniteFloat,
    FutureDate,
    FutureDatetime,
    NaiveDatetime,
    NegativeFloat,
    NegativeInt,
    NewPath,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PastDate,
    PastDatetime,
    PositiveFloat,
    SecretBytes,
    SecretStr,
    Strict,
    StrictBool,
    StrictBytes,
    StrictFloat,
    StrictInt,
    StrictStr,
    condate,
    confloat,
    conint,
    constr,
)


class AllTypesExampleModel(BaseModel):
    conint_int: conint(gt=0, lt=50) = Field(
        10,
        title="Constrained Int Example",
        description="An integer between 1 and 49.",
        example=25,
    )
    constr_str: constr(pattern=r"^abc", min_length=3, max_length=10) = Field(
        "abc123",
        title="Constrained Str Example",
        description="A string that starts with 'abc' and is 3-10 chars long.",
        example="abcXYZ",
    )
    confloat_float: confloat(ge=0.0, le=100.0) = Field(
        3.14,
        title="Constrained Float Example",
        description="A float between 0.0 and 100.0.",
        example=42.0,
    )
    negative_float: NegativeFloat = Field(
        -1.5,
        title="Negative Float Example",
        description="Must be negative.",
        example=-2.3,
    )
    strict_str_str: StrictStr = Field(
        "StrictData",
        title="Strict Str Example",
        description="Does not allow int or float as valid input.",
        example="OnlyStringAccepted",
    )
    strict_int_int: StrictInt = Field(
        42,
        title="Strict Int Example",
        description="Only accepts pure integers (no floats).",
        example=7,
    )
    strict_bool_bool: StrictBool = Field(
        True,
        title="Strict Bool Example",
        description="Strict boolean must be either True/False, not 1/0.",
        example=True,
    )
    uuid4_field: UUID4 = Field(
        ...,
        title="UUID4 Example",
        description="A valid UUID4 value.",
        example="550e8400-e29b-41d4-a716-446655440000",
    )
    secret_str_password: SecretStr = Field(
        "supersecret",
        title="Secret Str Example",
        description="Stores a secret string, often used for passwords.",
        example="MyPa$$w0rd",
    )
    past_date_birthday: PastDate = Field(
        ...,
        title="Past Date Example",
        description="Must be a date in the past (YYYY-MM-DD).",
        example="1990-01-01",
    )
    future_date_event: FutureDate = Field(
        ...,
        title="Future Date Example",
        description="Must be a date in the future (YYYY-MM-DD).",
        example="2100-12-31",
    )
    negative_int_field: NegativeInt = Field(-10, title="Negative Int", example=-5)
    non_negative_int_field: NonNegativeInt = Field(10, title="Non-Negative Int", example=0)
    non_positive_int_field: NonPositiveInt = Field(0, title="Non-Positive Int", example=-1)
    positive_float_field: PositiveFloat = Field(3.14, title="Positive Float", example=1.23)
    non_negative_float_field: NonNegativeFloat = Field(
        0.0, title="Non-Negative Float", example=0.42
    )
    non_positive_float_field: NonPositiveFloat = Field(
        -0.1, title="Non-Positive Float", example=-2.71
    )
    finite_float_field: FiniteFloat = Field(42.0, title="Finite Float", example=3.99)
    # payment_card_field: PaymentCardNumber = Field("4111111111111111", title="Payment Card Example")
    byte_size_field: ByteSize = Field(1024, title="Byte Size Example")
    past_datetime_field: PastDatetime = Field(
        ..., title="Past Datetime", example="2000-01-01T12:00:00"
    )
    future_datetime_field: FutureDatetime = Field(
        ..., title="Future Datetime", example="2999-12-31T23:59:59"
    )
    constrained_date_field: condate(ge="2020-01-01") = Field(
        "2021-05-05", title="Constrained Date", example="2021-01-01"
    )
    aware_dt_field: AwareDatetime = Field(..., title="Aware Datetime")
    naive_dt_field: NaiveDatetime = Field(..., title="Naive Datetime")
    file_path_field: FilePath = Field("/path/to/file", title="File Path Example")
    directory_path_field: DirectoryPath = Field(
        "/path/to/directory", title="Directory Path Example"
    )
    new_path_field: NewPath = Field("/path/to/new_path", title="New Path Example")
    secret_bytes_field: SecretBytes = Field(b"secret_data", title="Secret Bytes Example")
    strict_bytes_field: StrictBytes = Field(b"strict_data", title="Strict Bytes Example")
    strict_float_field: StrictFloat = Field(1.0, title="Strict Float Example")
    strict_field: Strict = Field(..., title="Strict Example")


if __name__ == "__main__":
    from pprint import pprint

    # Example usage
    # pprint(AllTypesExampleModel.model_json_schema(), indent=4)
    pprint(AllTypesExampleModel.model_json_schema(), indent=4)
