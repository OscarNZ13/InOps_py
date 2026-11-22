from flask import abort


def test_app_starts(client):
    assert client.get("/").status_code == 200


def test_404(client):
    response = client.get("/no-existe")
    html = response.get_data(as_text=True)
    assert response.status_code == 404
    assert "Página no encontrada" in html and "Volver al inicio" in html


def test_405_has_its_own_page(client, login_as):
    user = login_as("admin")
    response = client.get(f"/users/{user.id_user}/deactivate")
    assert response.status_code == 405
    assert "Acción no permitida" in response.get_data(as_text=True)


def test_500_has_its_own_page(app, client):
    app.add_url_rule("/falla", "falla", lambda: abort(500))
    response = client.get("/falla")
    assert response.status_code == 500
    assert "Algo salió mal" in response.get_data(as_text=True)


def test_expired_csrf_token_returns_to_the_form(app, client):
    app.config["WTF_CSRF_ENABLED"] = True
    response = client.post(
        "/login",
        data={"login-username": "ana", "login-password": "clave-segura"},
        headers={"Referer": "http://localhost/login"},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    assert "La página expiró" in client.get("/login").get_data(as_text=True)


def test_expired_csrf_token_ignores_external_referrer(app, client):
    app.config["WTF_CSRF_ENABLED"] = True
    response = client.post("/login", data={}, headers={"Referer": "https://otro-sitio.com/x"})
    assert response.headers["Location"] == "/"
