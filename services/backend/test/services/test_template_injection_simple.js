/**
 * Pruebas de regresión: Template Injection en creación de usuario
 * Estas pruebas usan Jest y supertest para verificar que el backend
 * no procese entradas maliciosas como plantillas.
 */

const request = require("supertest");
const nodemailer = require("nodemailer");

// Mock del transporte de correo (para no enviar mails reales)
jest.mock("nodemailer");
const sendMailMock = jest.fn().mockResolvedValue({ messageId: "mocked-id" });
nodemailer.createTransport.mockReturnValue({ sendMail: sendMailMock });

// Configuración del servidor backend
// Ajustá el path según donde exportás la app (ej: ../src/index.js o ../src/app.js)
const app = require("../src/index");

// Entradas maliciosas que intentarían causar inyección de plantilla
const MALICIOUS = [
  "{{__proto__.constructor('return process')()}}",
  "<script>alert('xss')</script>",
  "{% include 'etc/passwd' %}",
];

// Email de prueba
const TEST_EMAIL = "template_test@example.com";

describe("Mitigación de Template Injection en createUser", () => {
  beforeEach(() => {
    sendMailMock.mockClear();
  });

  test("Crea usuario con nombre normal y envía correo limpio", async () => {
    const user = {
      username: "pepito",
      email: TEST_EMAIL,
      password: "Passw0rd!",
    };

    const res = await request(app).post("/auth").send(user);

    expect([200, 201]).toContain(res.status);
    expect(sendMailMock).toHaveBeenCalledTimes(1);

    const html = sendMailMock.mock.calls[0][0].html.toLowerCase();

    expect(html).toContain("pepito");
    expect(html).not.toContain("<script");
    expect(html).not.toContain("{{");
  });

  test.each(MALICIOUS)(
    "No ejecuta payload malicioso en correo: %s",
    async (payload) => {
      const user = {
        username: payload,
        email: TEST_EMAIL,
        password: "Passw0rd!",
      };

      const res = await request(app).post("/auth").send(user);

      expect([200, 201]).toContain(res.status);
      expect(sendMailMock).toHaveBeenCalledTimes(1);

      const html = sendMailMock.mock.calls[0][0].html.toLowerCase();

      // No debe ejecutar código ni mostrar etiquetas inseguras
      expect(html).not.toContain("<script");
      expect(html).not.toContain("process");
      expect(html).not.toContain("constructor(");
      expect(html).not.toContain("{{");
    }
  );
});
