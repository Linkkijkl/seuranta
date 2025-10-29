import pytest


@pytest.mark.asyncio
async def test_root(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200

def test_static_styles_exist(client):
    response = client.get("/static/styles.css")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_name_form(async_client):
    form_data = {"username": "Alex"}
    response = await async_client.post("/name-form", data=form_data)
    assert response.status_code == 302
