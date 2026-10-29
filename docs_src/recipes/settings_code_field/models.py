import json
import tomllib
from typing import Any

from pydantic import field_validator

from pydantic_schemaforms import Field, FormModel


class ServiceSettings(FormModel):
    name: str = Field(title='Service name', pattern=r'^[a-z][a-z0-9-]*$')
    config: str = Field(
        '{\n  "replicas": 2\n}',
        title='Config (JSON)',
        ui_element='textarea',
        ui_options={'language': 'json', 'rows': 10},
    )
    build: str = Field(
        '[tool.build]\ntarget = "release"\n',
        title='Build settings (TOML)',
        ui_element='textarea',
        ui_options={'language': 'toml', 'rows': 6},
    )
    deploy_script: str = Field(
        '',
        title='Deploy script',
        ui_element='textarea',
        ui_options={'language': 'bash', 'code_highlight': False},
    )

    @field_validator('config')
    @classmethod
    def valid_json_object(cls, value: str) -> str:
        try:
            parsed: Any = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f'Not valid JSON: {exc.msg} (line {exc.lineno})') from None
        if not isinstance(parsed, dict):
            raise ValueError('The config must be a JSON object')
        return value

    @field_validator('build')
    @classmethod
    def valid_toml(cls, value: str) -> str:
        try:
            tomllib.loads(value)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f'Not valid TOML: {exc}') from None
        return value
