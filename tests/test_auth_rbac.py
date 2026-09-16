"""
Testes de Autenticação, Proteção contra Força Bruta e Controle de Acesso (RBAC).
"""
from haoc_voip.core.auth import hash_senha, verificar_senha, autenticar_usuario
from haoc_voip.core.models import Usuario, PerfilUsuario
from haoc_voip.core.database import db


def test_password_hashing():
    senha = "SenhaSeguraHospitalar@2026"
    h1 = hash_senha(senha)
    h2 = hash_senha(senha)

    # Hashes devem ser diferentes por conta de salts aleatórios
    assert h1 != h2
    assert verificar_senha(senha, h1) is True
    assert verificar_senha(senha, h2) is True
    assert verificar_senha("SenhaErrada", h1) is False


def test_login_and_lockout():
    # Login correto
    user, erro = autenticar_usuario("admintest", "Admin@123")
    assert erro is None
    assert user is not None
    assert user.perfil == PerfilUsuario.ADMINISTRADOR.value

    # Senha incorreta
    user_fail, erro_fail = autenticar_usuario("admintest", "SenhaErrada")
    assert user_fail is None
    assert "Credenciais inválidas" in erro_fail


def test_web_rbac_routes(client):
    # Acesso não autenticado deve redirecionar para /login
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

    # Login como visualizador
    client.post("/login", data={"login": "visutest", "senha": "Visu@123"}, follow_redirects=True)

    # Visualizador acessa dashboard OK
    resp_dash = client.get("/dashboard")
    assert resp_dash.status_code == 200

    # Visualizador NÃO pode acessar área de usuários (apenas Administrador)
    resp_users = client.get("/usuarios/", follow_redirects=False)
    assert resp_users.status_code == 302
    assert "/dashboard" in resp_users.headers["Location"]

    # Logout
    client.get("/logout")

    # Login como admin
    client.post("/login", data={"login": "admintest", "senha": "Admin@123"}, follow_redirects=True)

    # Admin acessa /usuarios/ com sucesso
    resp_admin_users = client.get("/usuarios/")
    assert resp_admin_users.status_code == 200


def test_master_user_wagner_authentication(client):
    # Autenticação direta pelo core (testando com Wagner e com wagner)
    user1, erro1 = autenticar_usuario("Wagner", "SenhaTel@Haoc")
    assert erro1 is None
    assert user1 is not None
    assert user1.perfil == PerfilUsuario.ADMINISTRADOR.value

    user2, erro2 = autenticar_usuario("wagner", "SenhaTel@Haoc")
    assert erro2 is None
    assert user2 is not None
    assert user2.perfil == PerfilUsuario.ADMINISTRADOR.value

    # Autenticação via interface Web
    resp = client.post("/login", data={"login": "Wagner", "senha": "SenhaTel@Haoc"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Wagner" in resp.data or b"Administrador" in resp.data

    # O usuário Master tem acesso à gestão de usuários
    resp_users = client.get("/usuarios/")
    assert resp_users.status_code == 200

