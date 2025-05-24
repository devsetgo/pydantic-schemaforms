import datetime
import decimal
import enum
import uuid
from typing import (
    Annotated,
    Any,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from pydantic import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    UUID6,
    UUID7,
    UUID8,
    AnyUrl,
    AwareDatetime,
    BaseModel,
    ByteSize,
    DirectoryPath,
    EmailStr,
    Field,
    FilePath,
    FiniteFloat,
    FutureDate,
    FutureDatetime,
    HttpUrl,
    IPvAnyAddress,
    IPvAnyInterface,
    IPvAnyNetwork,
    Json,
    NaiveDatetime,
    NegativeFloat,
    NegativeInt,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PastDate,
    PastDatetime,
    PaymentCardNumber,
    PositiveFloat,
    PositiveInt,
    SecretBytes,
    SecretStr,
    StrictBool,
    StrictBytes,
    StrictFloat,
    StrictInt,
    StrictStr,
    conbytes,
    condecimal,
    confloat,
    confrozenset,
    conint,
    conlist,
    conset,
    constr,
    model_validator,
)

from PySchemaForms.schema_form import FormModel


class ColorEnum(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


T = TypeVar("T")


class NestedModel(FormModel):
    nested_str: str = Field(..., description="Nested string field")
    nested_int: int = Field(..., description="Nested int field")


class KitchenSinkModel(FormModel, Generic[T]):
    # Standard types
    string_field: str = Field(..., description="A string field")
    int_field: int = Field(..., description="An integer field")
    float_field: float = Field(..., description="A float field")
    bool_field: bool = Field(..., description="A boolean field")
    bytes_field: bytes = Field(b"default", description="A bytes field")
    list_field: List[str] = Field(default_factory=list, description="A list of strings")
    dict_field: Dict[str, int] = Field(default_factory=dict, description="A dict field")
    set_field: Set[int] = Field(default_factory=set, description="A set of ints")
    tuple_field: Tuple[int, str] = Field((1, "a"), description="A tuple field")
    optional_field: Optional[str] = Field(None, description="An optional string")
    union_field: Union[int, str] = Field(..., description="A union of int or str")
    literal_field: Literal["a", "b", "c"] = Field("a", description="A literal field")
    enum_field: ColorEnum = Field(ColorEnum.RED, description="An enum field")
    annotated_field: Annotated[int, Field(ge=0, le=10)] = Field(
        5, description="Annotated int field"
    )
    any_field: Any = Field("anything", description="Any type field")
    nested_model: NestedModel = Field(default_factory=NestedModel, description="Nested model field")
    list_of_models: List[NestedModel] = Field(
        default_factory=list, description="List of nested models"
    )
    # Pydantic types
    secret_str: SecretStr = Field(..., description="A secret string")
    secret_bytes: SecretBytes = Field(..., description="A secret bytes")
    email: EmailStr = Field(..., description="An email address")
    url: AnyUrl = Field(..., description="A URL")
    http_url: HttpUrl = Field(..., description="An HTTP URL")
    ipv_any_address: IPvAnyAddress = Field(..., description="An IP address")
    ipv_any_interface: IPvAnyInterface = Field(..., description="An IP interface")
    ipv_any_network: IPvAnyNetwork = Field(..., description="An IP network")
    json_field: Json = Field(..., description="A JSON field")
    payment_card: PaymentCardNumber = Field(..., description="A payment card number")
    byte_size: ByteSize = Field(..., description="A byte size")
    dir_path: DirectoryPath = Field(..., description="A directory path")
    file_path: FilePath = Field(..., description="A file path")
    # Pydantic date/time types
    date_field: datetime.date = Field(..., description="A date")
    datetime_field: datetime.datetime = Field(..., description="A datetime")
    time_field: datetime.time = Field(..., description="A time")
    timedelta_field: datetime.timedelta = Field(..., description="A timedelta")
    past_date: PastDate = Field(..., description="A past date")
    future_date: FutureDate = Field(..., description="A future date")
    past_datetime: PastDatetime = Field(..., description="A past datetime")
    future_datetime: FutureDatetime = Field(..., description="A future datetime")
    aware_datetime: AwareDatetime = Field(..., description="An aware datetime")
    naive_datetime: NaiveDatetime = Field(..., description="A naive datetime")
    # Pydantic numeric types
    positive_int: PositiveInt = Field(..., description="A positive int")
    negative_int: NegativeInt = Field(..., description="A negative int")
    non_negative_int: NonNegativeInt = Field(..., description="A non-negative int")
    non_positive_int: NonPositiveInt = Field(..., description="A non-positive int")
    positive_float: PositiveFloat = Field(..., description="A positive float")
    negative_float: NegativeFloat = Field(..., description="A negative float")
    non_negative_float: NonNegativeFloat = Field(..., description="A non-negative float")
    non_positive_float: NonPositiveFloat = Field(..., description="A non-positive float")
    finite_float: FiniteFloat = Field(..., description="A finite float")
    strict_bool: StrictBool = Field(..., description="A strict bool")
    strict_bytes: StrictBytes = Field(..., description="A strict bytes")
    strict_float: StrictFloat = Field(..., description="A strict float")
    strict_int: StrictInt = Field(..., description="A strict int")
    strict_str: StrictStr = Field(..., description="A strict str")
    # UUIDs
    uuid1: UUID1 = Field(..., description="A UUID1")
    uuid3: UUID3 = Field(..., description="A UUID3")
    uuid4: UUID4 = Field(..., description="A UUID4")
    uuid5: UUID5 = Field(..., description="A UUID5")
    uuid6: UUID6 = Field(..., description="A UUID6")
    uuid7: UUID7 = Field(..., description="A UUID7")
    uuid8: UUID8 = Field(..., description="A UUID8")
    # Constrained types
    conint_field: conint(ge=0, le=100) = Field(50, description="A constrained int")
    confloat_field: confloat(gt=0, lt=100) = Field(10.5, description="A constrained float")
    condecimal_field: condecimal(gt=0, lt=100) = Field(
        decimal.Decimal("10.5"), description="A constrained decimal"
    )
    constr_field: constr(min_length=3, max_length=10) = Field(
        "abc", description="A constrained str"
    )
    conbytes_field: conbytes(min_length=2, max_length=8) = Field(
        b"ab", description="A constrained bytes"
    )
    conlist_field: conlist(int, min_length=1, max_length=3) = Field(
        [1], description="A constrained list"
    )
    conset_field: conset(str, min_length=1, max_length=3) = Field(
        {"a"}, description="A constrained set"
    )
    confrozenset_field: confrozenset(float, min_length=1, max_length=3) = Field(
        frozenset([1.1]), description="A constrained frozenset"
    )
    # Generic type
    generic_field: Optional[T] = Field(None, description="A generic field")

    @model_validator(mode="after")
    def check_secret(self) -> "KitchenSinkModel":
        # Example custom validation
        if self.secret_str.get_secret_value() == "forbidden":
            raise ValueError("Forbidden secret string")
        return self

    class Config:
        populate_by_name = True
