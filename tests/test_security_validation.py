"""Regressão: limites e validações de entrada (auditoria de segurança)."""

from datetime import time
from http import HTTPStatus

import pytest
from pydantic import ValidationError

from app.api.v1.util.util import escape_like
from app.schemas.psychologist_schema import (
    DeleteAvailabilySchema,
    MedicalRecordCreate,
    PsychologistAvaliabiliteBlock,
    PsychologistAvaliabiliteCreate,
)
from app.schemas.service_schema import ServiceQuery, ServiceSchema

MAX_RECORD_CHARS = 10_000
MAX_BLOCKS = 20


def _block(days=(0,), start=time(8), end=time(12)):
    return {'days_of_the_week': list(days), 'start_time': start, 'end_time': end}


def test_medical_record_description_has_an_upper_bound():
    ok = MedicalRecordCreate(
        id_user=1, id_appoiment=1, description='x' * MAX_RECORD_CHARS
    )
    assert len(ok.description) == MAX_RECORD_CHARS

    with pytest.raises(ValidationError):
        MedicalRecordCreate(
            id_user=1, id_appoiment=1, description='x' * (MAX_RECORD_CHARS + 1)
        )

    with pytest.raises(ValidationError):
        MedicalRecordCreate(id_user=1, id_appoiment=1, description='')


def test_availability_block_must_end_after_it_starts():
    with pytest.raises(ValidationError):
        PsychologistAvaliabiliteBlock(**_block(start=time(12), end=time(8)))

    with pytest.raises(ValidationError):
        PsychologistAvaliabiliteBlock(**_block(start=time(8), end=time(8)))


def test_availability_days_are_deduplicated_and_capped():
    block = PsychologistAvaliabiliteBlock(**_block(days=(1, 1, 2, 1, 2)))
    assert block.days_of_the_week == [1, 2]

    with pytest.raises(ValidationError):
        PsychologistAvaliabiliteBlock(**_block(days=[0] * 8))


def test_availability_request_has_a_block_limit():
    PsychologistAvaliabiliteCreate(availabilities=[_block()] * MAX_BLOCKS)

    with pytest.raises(ValidationError):
        PsychologistAvaliabiliteCreate(availabilities=[_block()] * (MAX_BLOCKS + 1))

    with pytest.raises(ValidationError):
        PsychologistAvaliabiliteCreate(availabilities=[])


@pytest.mark.parametrize('day', [-1, 7, 99])
def test_delete_availability_rejects_invalid_weekday(day):
    # Antes o validador RETORNAVA o ValueError (nunca falhava) e o objeto de erro
    # virava parâmetro SQL.
    with pytest.raises(ValidationError):
        DeleteAvailabilySchema(
            days_of_the_week=day, start_time='08:00', end_time='09:00'
        )


def test_service_filter_and_schema_limits():
    with pytest.raises(ValidationError):
        ServiceQuery(limit=101)

    with pytest.raises(ValidationError):
        ServiceQuery(name='a' * 101)

    with pytest.raises(ValidationError):
        ServiceSchema(
            name='n' * 201, description='d' * 20, price=100, duration_minutes=50
        )


def test_escape_like_neutralizes_wildcards():
    assert escape_like('100%') == '100\\%'
    assert escape_like('a_b') == 'a\\_b'
    assert escape_like('x\\y') == 'x\\\\y'


@pytest.mark.asyncio
async def test_percent_sign_in_name_filter_is_literal(token_client, service, service2):
    everything = await token_client.get('/api/v1/services/filter?name=Terapia')
    wildcard = await token_client.get('/api/v1/services/filter?name=%25')
    underscore = await token_client.get('/api/v1/services/filter?name=T_rapia')

    assert len(everything.json()) == 2  # noqa: PLR2004
    # `%` e `_` agora são texto, não curingas: nenhum nome os contém
    assert wildcard.status_code == HTTPStatus.OK
    assert 'Nenhum serviço encontrado' in wildcard.json()['message']
    assert 'Nenhum serviço encontrado' in underscore.json()['message']


@pytest.mark.asyncio
async def test_huge_request_bodies_are_rejected_before_being_read(token_client):
    body = '{"message": "' + 'a' * 1_100_000 + '"}'

    response = await token_client.post(
        '/api/v1/chat-user', content=body, headers={'content-type': 'application/json'}
    )

    assert response.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
