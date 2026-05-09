from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from bms_data_generator.api.control import get_service as get_control_service
from bms_data_generator.api.datasets import get_service as get_dump_service


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from bms_data_generator.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def reset_services() -> None:
    """Limpia el estado del singleton entre tests."""
    get_control_service().reset()
    get_dump_service().reset()
    yield
