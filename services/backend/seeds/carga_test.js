/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> } 
 */
const bcrypt = require("bcrypt");

exports.seed = async function (knex) {
  // limpiar primero (opcional, para no duplicar)
  await knex("users").del();
  await knex("invoices").del();

  const hashedTestPassword = await bcrypt.hash(process.env.SEED_TEST_PASS || "changeme123", 10);
  const hashedProdPassword = await bcrypt.hash(process.env.SEED_PROD_PASS || "changeme123", 10);

  await knex("users").insert([
    {
      id: 1,
      username: "test",
      email: "test@example.local",
      password: hashedTestPassword,
      first_name: "Test",
      last_name: "User",
      activated: true,
    },
    {
      id: 2,
      username: "prod",
      email: "prod@example.local",
      password: hashedProdPassword,
      first_name: "Prod",
      last_name: "User",
      activated: true,
    },
  ]);

  await knex("invoices").insert([
    {
      id: 1,
      userId: 1,
      amount: 101.0,
      dueDate: new Date("2025-01-01"),
      status: "unpaid",
    },
    {
      id: 2,
      userId: 1,
      amount: 102.0,
      dueDate: new Date("2025-01-01"),
      status: "paid",
    },
    {
      id: 3,
      userId: 1,
      amount: 103.0,
      dueDate: new Date("2025-01-01"),
      status: "paid",
    },
    {
      id: 4,
      userId: 2,
      amount: 99.0,
      dueDate: new Date("2025-01-01"),
      status: "unpaid",
    },
  ]);
};
