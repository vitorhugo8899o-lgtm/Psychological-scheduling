from pydantic import BaseModel, ConfigDict, Field, field_validator


class ServiceSchema(BaseModel):
    name: str = Field(min_length=7)
    description: str = Field(min_length=10)
    price: float = Field(ge=50)
    duration_minutes: int = Field(ge=30)

    model_config = ConfigDict(from_attributes=True)

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str):
        space = value.replace(' ', '')
        if not space:
            raise ValueError('Preencha um título valído!')

        return value

    @field_validator('description')
    @classmethod
    def validate_description(cls, value: str):
        space = value.replace(' ', '')
        if not space:
            raise ValueError('Preencha uma descrição valído!')

        return value


class ServiceResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    duration_minutes: int

    model_config = ConfigDict(from_attributes=True)