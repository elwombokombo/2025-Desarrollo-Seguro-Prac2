import os
import pytest
from src.services.invoiceService import InvoiceService
from src.utils.db import db

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000")

INVOICE_BY_ID_PATH = "/invoices/{}"
INVOICE_LIST_PATH = "/invoices"

MALICIOUS_IDS = [
    "' OR '1'='1",
    "1; DROP TABLE invoices;",
    "'; DROP TABLE invoices; --",
    "1 OR 1=1",
    "\" OR \"\" = \"",
]

MALICIOUS_USERIDS = [
    "1 OR 1=1",
    "' OR '1'='1",
    "username'; DROP TABLE invoices; --",
]

MALICIOUS_INPUTS = [
    "' OR '1'='1",
    "'; DROP TABLE invoices; --",
    "1 OR 1=1",
    "\" OR \"\" = \""
]

MALICIOUS_OPERATORS = [
    "= ' OR '1'='1",
    ">= ' OR 1=1; --",
    "IN (SELECT * FROM users)",
    "LIKE '%'"
]

def is_error_status(code):
    """Consideramos como seguro cualquier status que no sea 200 OK para un intento malicioso.
    Pero algunos endpoints podrían devolver 422/400/404 en caso de input inválido."""
    return code in (400, 401, 403, 404, 422, 500) or code != 200

@pytest.mark.parametrize("malicious", MALICIOUS_IDS)
def test_get_invoice_sql_injection(malicious):
    """Intento de inyección en GET /invoices/{invoiceId}"""
    url = BACKEND_URL + INVOICE_BY_ID_PATH.format(malicious)
    resp = requests.get(url, timeout=5)

    # No debe devolver 200 OK con datos arbitrarios por el payload malicioso
    assert is_error_status(resp.status_code), (
        f"Respuesta inesperada {resp.status_code} para payload malicioso: {malicious}\n"
        f"Contenido: {resp.text[:200]}"
    )

    # Si devuelve JSON, no debe ser una lista grande ni contener múltiples facturas
    try:
        j = resp.json()
        # si devolviera una lista completa, sería sospechoso: bloqueamos ese caso
        if isinstance(j, list):
            assert len(j) == 0, f"Payload malicioso devolvió lista con elementos: {malicious}"
    except ValueError:
        # no viene JSON -> ok (puede ser HTML de error, texto, etc.)
        pass

@pytest.mark.parametrize("malicious", MALICIOUS_USERIDS)
def test_list_invoices_sql_injection(malicious):
    """Intento de inyección en GET /invoices?userId=..."""
    url = BACKEND_URL + INVOICE_LIST_PATH
    params = {"userId": malicious}
    resp = requests.get(url, params=params, timeout=5)

    # No debería devolver 200 OK con un listado amplio por el payload malicioso
    assert is_error_status(resp.status_code), (
        f"Respuesta inesperada {resp.status_code} para query maliciosa userId={malicious}\n"
        f"Contenido: {resp.text[:200]}"
    )

    # Si devuelve JSON, exigir que sea una lista vacía o un error claro
    try:
        j = resp.json()
        if isinstance(j, list):
            assert len(j) == 0, f"Payload malicioso devolvió lista con elementos: userId={malicious}"
    except ValueError:
        pass

def test_sanity_list_invoices_available():
    """Comprobación simple para asegurarnos que el endpoint funciona con input válido.
    (Esto evita falsos positivos si el servidor está abajo)."""
    url = BACKEND_URL + INVOICE_LIST_PATH
    # userId 'test-user' debería existir o al menos no causar 500
    resp = requests.get(url, params={"userId": "test-user"}, timeout=5)
    assert resp.status_code in (200, 404, 400, 422), (
        "Endpoint /invoices no respondió como se esperaba. Asegurate que el backend esté corriendo."
    )

class TestInvoiceServiceRegression:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Setup test database
        self.valid_user_id = "test-user-id"
        self.valid_invoice_id = "test-invoice-id"
        
        # Crear factura de prueba
        db('invoices').insert({
            'id': self.valid_invoice_id,
            'userId': self.valid_user_id,
            'amount': 100,
            'status': 'pending'
        })
        
        yield
        
        # Cleanup
        db('invoices').where('id', self.valid_invoice_id).delete()

    @pytest.mark.parametrize("malicious", MALICIOUS_INPUTS)
    def test_list_invoices_sql_injection(self, malicious):
        """Prueba inyección SQL en método list()"""
        # No debería exponer datos con status malicioso
        result = InvoiceService.list(
            userId=self.valid_user_id,
            status=malicious
        )
        assert len(result) == 0, f"Payload malicioso retornó datos: {malicious}"

    @pytest.mark.parametrize("malicious", MALICIOUS_OPERATORS)
    def test_list_invoices_operator_injection(self, malicious):
        """Prueba inyección SQL en operador del método list()"""
        with pytest.raises(Exception):
            InvoiceService.list(
                userId=self.valid_user_id,
                status="pending",
                operator=malicious
            )

    @pytest.mark.parametrize("malicious", MALICIOUS_INPUTS)
    def test_get_invoice_sql_injection(self, malicious):
        """Prueba inyección SQL en getInvoice()"""
        with pytest.raises(Exception):
            InvoiceService.getInvoice(invoiceId=malicious)

    def test_valid_operations_work(self):
        """Sanity check - operaciones válidas deben funcionar"""
        # Lista facturas
        invoices = InvoiceService.list(userId=self.valid_user_id)
        assert len(invoices) > 0

        # Obtiene factura específica
        invoice = InvoiceService.getInvoice(self.valid_invoice_id)
        assert invoice is not None
        assert invoice.id == self.valid_invoice_id
