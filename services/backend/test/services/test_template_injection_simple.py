import os
import time
import pytest
import requests

# direccion del backend y MailHog (pueden cambiar si usas otros puertos)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000")
MAILHOG_URL = os.getenv("MAILHOG_URL", "http://localhost:8025")

# email que se usa para las pruebas
TEST_EMAIL = "template_test@example.com"

# textos maliciosos que intentan hacer una inyección de plantilla
MALICIOUS_TEXTS = [
    "{{__proto__.constructor('return process')()}}",
    "<script>alert('xss')</script>",
    "{% include 'etc/passwd' %}",
]

def borrar_correos_mailhog():
    """Elimina los correos actuales de MailHog para empezar limpio."""
    try:
        requests.delete(f"{MAILHOG_URL}/api/v1/messages", timeout=3)
    except Exception:
        pass

def esperar_correo(segundos=6):
    """
    Espera unos segundos hasta que llegue un correo nuevo a MailHog.
    Devuelve el texto del correo si llega, o None si no llega nada.
    """
    fin = time.time() + segundos
    while time.time() < fin:
        try:
            r = requests.get(f"{MAILHOG_URL}/api/v2/messages", timeout=3)
            data = r.json()
            mensajes = data.get("items", [])
            if mensajes:
                return mensajes[0]["Content"]["Body"]
        except Exception:
            pass
        time.sleep(1)
    return None

@pytest.mark.parametrize("texto", MALICIOUS_TEXTS)
def test_no_ejecuta_plantillas_maliciosas(texto):
    """
    Verifica que si se intenta registrar un usuario con texto malicioso,
    el correo que llega no tenga ejecución de código ni etiquetas <script>.
    """
    borrar_correos_mailhog()

    # enviamos el usuario con texto malicioso
    url = f"{BACKEND_URL}/auth"
    datos = {"username": texto, "email": TEST_EMAIL, "password": "Passw0rd!"}

    try:
        respuesta = requests.post(url, json=datos, timeout=10)
    except Exception:
        pytest.skip("No se pudo conectar al backend")

    # si la API responde correctamente
    assert respuesta.status_code in (200, 201)

    # esperamos el correo
    cuerpo = esperar_correo()
    if cuerpo is None:
        pytest.skip("No se recibió correo en MailHog")

    cuerpo = cuerpo.lower()

    # revisamos que no haya código peligroso en el correo
    assert "<script" not in cuerpo, "El correo contiene etiquetas <script> (posible inyección)"
    assert "process" not in cuerpo, "El correo contiene texto de ejecución ('process')"
    assert "constructor(" not in cuerpo, "El correo contiene código ejecutado ('constructor(')"

@pytest.mark.simple
def test_usuario_normal_envia_correo_limpio():
    """
    Verifica que un usuario normal ('pepito') genera un correo limpio,
    sin etiquetas ni símbolos raros.
    """
    borrar_correos_mailhog()

    url = f"{BACKEND_URL}/auth"
    datos = {"username": "pepito", "email": TEST_EMAIL, "password": "Passw0rd!"}

    try:
        respuesta = requests.post(url, json=datos, timeout=10)
    except Exception:
        pytest.skip("No se pudo conectar al backend")

    assert respuesta.status_code in (200, 201)

    cuerpo = esperar_correo()
    if cuerpo is None:
        pytest.skip("No se recibió correo en MailHog")

    cuerpo = cuerpo.lower()

    # El correo debe contener el nombre, pero no etiquetas ni símbolos peligrosos
    assert "pepito" in cuerpo
    assert "<script" not in cuerpo
    assert "{{" not in cuerpo
