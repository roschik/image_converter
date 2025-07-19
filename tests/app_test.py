from flask.testing import FlaskClient
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def client():
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_read_main(client: FlaskClient):
    response = client.get("/")
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}. Ответ: {response.data}"
