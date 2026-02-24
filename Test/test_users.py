"""
Tests para las rutas de gestión de usuarios.

Cubre:
- Login: éxito, contraseña incorrecta, usuario inexistente
- GET /usuarios: admin OK, empleado 403, sin token 403
- GET /usuarios/{id}: admin OK, no encontrado 404, empleado 403
- POST /usuarios: admin OK, email duplicado 400, empleado 403, validaciones 422
- PUT /usuarios/{id}: admin OK, no encontrado 404, empleado 403
- DELETE /usuarios/{id}: admin OK, no encontrado 404, empleado 403
"""

import pytest


# ──────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────

class TestLogin:
    def test_login_exitoso(self, client, admin_headers):
        """Login correcto devuelve token y datos del usuario."""
        response = client.post("/login", json={
            "email": "admin@test.com",
            "password": "Admin123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@test.com"
        assert "password" not in data["user"]

    def test_login_contrasena_incorrecta(self, client, admin_headers):
        """Contraseña errónea devuelve 401."""
        response = client.post("/login", json={
            "email": "admin@test.com",
            "password": "Wrongpass1",
        })
        assert response.status_code == 401

    def test_login_usuario_no_existe(self, client):
        """Email inexistente devuelve 401 (evita enumeración de usuarios)."""
        response = client.post("/login", json={
            "email": "noexiste@test.com",
            "password": "SomePass1",
        })
        assert response.status_code == 401

    def test_login_email_invalido(self, client):
        """Email con formato inválido devuelve 422."""
        response = client.post("/login", json={
            "email": "no-es-un-email",
            "password": "SomePass1",
        })
        assert response.status_code == 422


# ──────────────────────────────────────────────
# GET /usuarios
# ──────────────────────────────────────────────

class TestListarUsuarios:
    def test_admin_puede_listar(self, client, admin_headers):
        """Admin recibe la lista de usuarios."""
        response = client.get("/usuarios", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_respuesta_no_expone_password(self, client, admin_headers):
        """Ningún objeto en la lista expone la contraseña."""
        response = client.get("/usuarios", headers=admin_headers)
        for user in response.json():
            assert "password" not in user

    def test_empleado_no_puede_listar(self, client, empleado_headers):
        """Empleado recibe 403."""
        response = client.get("/usuarios", headers=empleado_headers)
        assert response.status_code == 403

    def test_sin_token_rechazado(self, client):
        """Sin token recibe 401 (HTTPBearer no encuentra credenciales)."""
        response = client.get("/usuarios")
        assert response.status_code == 401


# ──────────────────────────────────────────────
# GET /usuarios/{id}
# ──────────────────────────────────────────────

class TestObtenerUsuarioPorId:
    def test_admin_puede_obtener(self, client, admin_headers, create_user):
        """Admin puede obtener un usuario por ID."""
        user_id = create_user("getbyid@test.com")
        response = client.get(f"/usuarios/{user_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert "password" not in data

    def test_usuario_no_encontrado(self, client, admin_headers):
        """ID inexistente devuelve 404."""
        response = client.get("/usuarios/99999", headers=admin_headers)
        assert response.status_code == 404

    def test_empleado_no_puede_obtener(self, client, empleado_headers, create_user):
        """Empleado recibe 403 aunque el usuario exista."""
        user_id = create_user("getbyid_emp@test.com")
        response = client.get(f"/usuarios/{user_id}", headers=empleado_headers)
        assert response.status_code == 403

    def test_sin_token_rechazado(self, client):
        """Sin token recibe 401 (HTTPBearer no encuentra credenciales)."""
        response = client.get("/usuarios/1")
        assert response.status_code == 401


# ──────────────────────────────────────────────
# POST /usuarios
# ──────────────────────────────────────────────

class TestCrearUsuario:
    def test_admin_puede_crear(self, client, admin_headers):
        """Admin crea un usuario correctamente."""
        response = client.post("/usuarios", headers=admin_headers, json={
            "name": "Nuevo Usuario",
            "email": "nuevo@test.com",
            "password": "Password1",
            "rol": "Empleado",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "nuevo@test.com"
        assert data["rol"] == "Empleado"
        assert "password" not in data
        assert "id" in data

    def test_email_duplicado_rechazado(self, client, admin_headers, create_user):
        """Intentar crear un usuario con email ya registrado devuelve 400."""
        create_user("duplicado@test.com")
        response = client.post("/usuarios", headers=admin_headers, json={
            "name": "Duplicado",
            "email": "duplicado@test.com",
            "password": "Password1",
            "rol": "Empleado",
        })
        assert response.status_code == 400

    def test_empleado_no_puede_crear(self, client, empleado_headers):
        """Empleado recibe 403 al intentar crear un usuario."""
        response = client.post("/usuarios", headers=empleado_headers, json={
            "name": "Intento",
            "email": "intento@test.com",
            "password": "Password1",
            "rol": "Empleado",
        })
        assert response.status_code == 403

    def test_sin_token_rechazado(self, client):
        """Sin token recibe 401 (HTTPBearer no encuentra credenciales)."""
        response = client.post("/usuarios", json={
            "name": "Sin Token",
            "email": "sintoken@test.com",
            "password": "Password1",
            "rol": "Empleado",
        })
        assert response.status_code == 401

    def test_contrasena_sin_mayuscula_rechazada(self, client, admin_headers):
        """Contraseña sin mayúscula devuelve 422."""
        response = client.post("/usuarios", headers=admin_headers, json={
            "name": "Usuario Valido",
            "email": "weakpass@test.com",
            "password": "sinmayuscula1",
            "rol": "Empleado",
        })
        assert response.status_code == 422

    def test_contrasena_sin_numero_rechazada(self, client, admin_headers):
        """Contraseña sin número devuelve 422."""
        response = client.post("/usuarios", headers=admin_headers, json={
            "name": "Usuario Valido",
            "email": "weakpass2@test.com",
            "password": "SinNumeroAqui",
            "rol": "Empleado",
        })
        assert response.status_code == 422

    def test_contrasena_sin_minuscula_rechazada(self, client, admin_headers):
        """Contraseña sin minúscula devuelve 422."""
        response = client.post("/usuarios", headers=admin_headers, json={
            "name": "Usuario Valido",
            "email": "weakpass3@test.com",
            "password": "SINMINUSCULA1",
            "rol": "Empleado",
        })
        assert response.status_code == 422

    def test_nombre_corto_rechazado(self, client, admin_headers):
        """Nombre con menos de 3 caracteres devuelve 422."""
        response = client.post("/usuarios", headers=admin_headers, json={
            "name": "AB",
            "email": "shortname@test.com",
            "password": "Password1",
            "rol": "Empleado",
        })
        assert response.status_code == 422

    def test_rol_invalido_rechazado(self, client, admin_headers):
        """Rol fuera del Literal permitido devuelve 422."""
        response = client.post("/usuarios", headers=admin_headers, json={
            "name": "Rol Invalido",
            "email": "invalidrol@test.com",
            "password": "Password1",
            "rol": "SuperAdmin",
        })
        assert response.status_code == 422


# ──────────────────────────────────────────────
# PUT /usuarios/{id}
# ──────────────────────────────────────────────

class TestActualizarUsuario:
    def test_admin_puede_actualizar(self, client, admin_headers, create_user):
        """Admin actualiza un usuario correctamente."""
        user_id = create_user("update_me@test.com")
        response = client.put(f"/usuarios/{user_id}", headers=admin_headers, json={
            "name": "Nombre Actualizado",
            "email": "updated@test.com",
            "password": "NewPass1",
            "rol": "Empleado",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Nombre Actualizado"
        assert data["email"] == "updated@test.com"
        assert "password" not in data

    def test_usuario_no_encontrado(self, client, admin_headers):
        """ID inexistente devuelve 404."""
        response = client.put("/usuarios/99999", headers=admin_headers, json={
            "name": "No Existe",
            "email": "noexiste_up@test.com",
            "password": "NewPass1",
            "rol": "Empleado",
        })
        assert response.status_code == 404

    def test_empleado_no_puede_actualizar(self, client, empleado_headers, create_user):
        """Empleado recibe 403."""
        user_id = create_user("no_update@test.com")
        response = client.put(f"/usuarios/{user_id}", headers=empleado_headers, json={
            "name": "Intento",
            "email": "intento_up@test.com",
            "password": "NewPass1",
            "rol": "Empleado",
        })
        assert response.status_code == 403

    def test_sin_token_rechazado(self, client):
        """Sin token recibe 401 (HTTPBearer no encuentra credenciales)."""
        response = client.put("/usuarios/1", json={
            "name": "Sin Token",
            "email": "sintoken_up@test.com",
            "password": "NewPass1",
            "rol": "Empleado",
        })
        assert response.status_code == 401


# ──────────────────────────────────────────────
# DELETE /usuarios/{id}
# ──────────────────────────────────────────────

class TestEliminarUsuario:
    def test_admin_puede_eliminar(self, client, admin_headers, create_user):
        """Admin elimina un usuario correctamente."""
        user_id = create_user("delete_me@test.com")
        response = client.delete(f"/usuarios/{user_id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["msg"] == "Usuario eliminado correctamente"

    def test_usuario_eliminado_no_existe(self, client, admin_headers, create_user):
        """Después de eliminar, el usuario ya no es encontrado."""
        user_id = create_user("deleted_check@test.com")
        client.delete(f"/usuarios/{user_id}", headers=admin_headers)
        response = client.get(f"/usuarios/{user_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_usuario_no_encontrado(self, client, admin_headers):
        """ID inexistente devuelve 404."""
        response = client.delete("/usuarios/99999", headers=admin_headers)
        assert response.status_code == 404

    def test_empleado_no_puede_eliminar(self, client, empleado_headers, create_user):
        """Empleado recibe 403."""
        user_id = create_user("no_delete@test.com")
        response = client.delete(f"/usuarios/{user_id}", headers=empleado_headers)
        assert response.status_code == 403

    def test_sin_token_rechazado(self, client):
        """Sin token recibe 401 (HTTPBearer no encuentra credenciales)."""
        response = client.delete("/usuarios/1")
        assert response.status_code == 401
