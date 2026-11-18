def test_app_starts(client):
    assert client.get("/").status_code == 200


def test_404(client):
    assert client.get("/no-existe").status_code == 404
