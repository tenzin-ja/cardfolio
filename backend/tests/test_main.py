from fastapi.testclient import TestClient

from app.main import app

#creates a client that can send tst requests to the FastAPI app
client = TestClient(app)

def test_read_root():

    '''
    check that the backend root route is running correctly.
    '''
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Cardfolio backend is running"
    }

