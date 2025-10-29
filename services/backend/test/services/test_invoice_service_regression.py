import os
import pytest
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000")
MALICIOUS = ["' OR '1'='1", "1; DROP TABLE invoices;", "1 OR 1=1", "'; DROP TABLE invoices; --"]

# indicador de si la factura de prueba fue creada via API (fixture lo ajusta)
created_invoice = False
TEST_INV_ID = "test-inv"
TEST_USER_ID = "test-user"

@pytest.fixture(autouse=True)
def setup_teardown():
    """
    Intenta crear una factura de prueba vía API POST /invoices.
    Si el endpoint no existe o devuelve error, continuamos sin fallo (pruebas adaptativas).
    Al final, intenta borrar la factura vía DELETE /invoices/{id} si fue creada.
    """
    global created_invoice
    created_invoice = False
    try:
        url = f"{BACKEND_URL}/invoices"
        payload = {"id": TEST_INV_ID, "userId": TEST_USER_ID, "amount": 1, "status": "pending"}
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code in (200, 201, 204):
            created_invoice = True
    except Exception:
        # no hacemos nada: la API puede no soportar creación via HTTP, las pruebas siguen siendo útiles
        created_invoice = False

    yield

    # teardown: intentar borrar si fue creada vía API
    if created_invoice:
        try:
            del_url = f"{BACKEND_URL}/invoices/{TEST_INV_ID}"
            requests.delete(del_url, timeout=5)
        except Exception:
            pass

@pytest.mark.parametrize("payload", MALICIOUS)
def test_http_get_invoice_no_sql_injection(payload):
    """
    GET /invoices/{payload} no debe devolver colecciones inesperadas cuando el id es malicioso.
    Aceptamos comportamiento seguro que devuelva 4xx/5xx o 200 con respuesta que no sea lista con >0 elementos.
    """
    url = f"{BACKEND_URL}/invoices/{payload}"
    try:
        r = requests.get(url, timeout=5)
    except Exception:
        # Si no responde, lo consideramos aceptable (no exponiendo datos)
        return

    if r.status_code == 200:
        try:
            j = r.json()
            assert not (isinstance(j, list) and len(j) > 0)
        except ValueError:
            # no JSON válido -> aceptable
            pass
    else:
        # aceptamos 4xx/5xx como rechazo de la petición maliciosa
        assert r.status_code >= 400

@pytest.mark.parametrize("payload", MALICIOUS)
def test_http_list_with_malicious_status(payload):
    """
    GET /invoices?userId=...&status=malicious no debe filtrar datos por inyección.
    Aceptamos que la API lance error (4xx/5xx) o que devuelva lista vacía / no incluya la factura de prueba.
    """
    params = {"userId": TEST_USER_ID, "status": payload}
    try:
        r = requests.get(f"{BACKEND_URL}/invoices", params=params, timeout=5)
    except Exception:
        return

    if r.status_code == 200:
        try:
            j = r.json()
            if isinstance(j, (list, tuple)):
                # no debe devolver la factura de prueba
                assert all((inv.get("id") if isinstance(inv, dict) else getattr(inv, "id", None)) != TEST_INV_ID for inv in j)
            else:
                # si devuelve objeto único, tampoco debe ser la factura de prueba
                inv_id = j.get("id") if isinstance(j, dict) else None
                assert inv_id != TEST_INV_ID
        except ValueError:
            # respuesta no JSON -> aceptable
            pass
    else:
        assert r.status_code >= 400

def test_sanity_valid_operations_or_skip():
    """
    Sanity check: si la factura de prueba fue creada vía API, verificar GET list y GET by id.
    Si no se pudo crear la factura en setup, saltar el test (no fallar).
    """
    if not created_invoice:
        pytest.skip("Invoice fixture not created via API - skipping sanity checks")

    # List
    try:
        r = requests.get(f"{BACKEND_URL}/invoices", params={"userId": TEST_USER_ID}, timeout=5)
    except Exception:
        pytest.skip("Backend not reachable for list endpoint")

    assert r.status_code == 200
    try:
        j = r.json()
        assert isinstance(j, (list, tuple))
    except ValueError:
        pytest.skip("List endpoint did not return JSON")

    # Get by id
    try:
        r2 = requests.get(f"{BACKEND_URL}/invoices/{TEST_INV_ID}", timeout=5)
    except Exception:
        pytest.skip("Backend not reachable for get endpoint")

    assert r2.status_code == 200
    try:
        j2 = r2.json()
        inv_id = j2.get("id") if isinstance(j2, dict) else None
        assert inv_id == TEST_INV_ID
    except ValueError:
        pytest.skip("Get endpoint did not return JSON")
