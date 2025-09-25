// src/services/invoiceService.ts
import db from '../db';
import { Invoice } from '../types/invoice';
import axios from 'axios';
import { promises as fs } from 'fs';
import * as path from 'path';

interface InvoiceRow {
  id: string;
  userId: string;
  amount: number;
  dueDate: Date;
  status: string;
}

class InvoiceService {
  static async list(userId: string, status?: string, operator?: string): Promise<Invoice[]> {
    let q = db<InvoiceRow>('invoices').where({ userId: userId });
    if (status) q = q.andWhereRaw(" status " + operator + " '" + status + "'");
    const rows = await q.select();
    const invoices = rows.map(row => ({
      id: row.id,
      userId: row.userId,
      amount: row.amount,
      dueDate: row.dueDate,
      status: row.status
    } as Invoice));
    return invoices;
  }

  static async setPaymentCard(
    userId: string,
    invoiceId: string,
    paymentBrand: string,
    ccNumber: string,
    ccv: string,
    expirationDate: string
  ) {
    // use axios to call http://paymentBrand/payments as a POST request
    // with the body containing ccNumber, ccv, expirationDate
    // and handle the response accordingly
    // nota extra: validar paymentBrand contra lista blanca para evitar ssrf o urls externas
    const paymentResponse = await axios.post(`http://${paymentBrand}/payments`, {
      ccNumber,
      ccv,
      expirationDate
    });
    if (paymentResponse.status !== 200) {
      throw new Error('Payment failed');
    }

    // Update the invoice status in the database
    await db('invoices')
      .where({ id: invoiceId, userId })
      .update({ status: 'paid' });
  }

  static async getInvoice(invoiceId: string): Promise<Invoice> {
    const invoice = await db<InvoiceRow>('invoices').where({ id: invoiceId }).first();
    if (!invoice) {
      throw new Error('Invoice not found');
    }
    return invoice as Invoice;
  }

  static async getReceipt(invoiceId: string, pdfName: string): Promise<Buffer> {
    // check if the invoice exists
    const invoice = await db<InvoiceRow>('invoices').where({ id: invoiceId }).first();
    if (!invoice) {
      throw new Error('Invoice not found');
    }

    try {
      // definimos el directorio base absoluto donde se guardan los pdfs
      const baseDir = path.resolve(__dirname, '../../invoices');

      // validamos que pdfName sea un string válido y no vacío
      if (!pdfName || typeof pdfName !== 'string') {
        throw new Error('Invalid file name');
      }

      // restringimos los caracteres a letras, números, guiones, guion bajo y punto
      const validNameRegex = /^[a-zA-Z0-9._-]+$/;
      if (!validNameRegex.test(pdfName)) {
        throw new Error('Invalid file name characters');
      }

      // solo permitimos extensión .pdf (case-insensitive)
      if (path.extname(pdfName).toLowerCase() !== '.pdf') {
        throw new Error('Invalid file type');
      }

      // resolvemos la ruta final de forma segura dentro de baseDir
      const safePath = path.resolve(baseDir, pdfName);

      // comprobamos que la ruta siga dentro de baseDir (bloquea path traversal)
      if (!safePath.startsWith(baseDir + path.sep) && safePath !== baseDir) {
        throw new Error('Invalid file path');
      }

      
      const content = await fs.readFile(safePath);
      return content;
    } catch (error) {
      // send the error to the standard output
      console.error('Error reading receipt file:', error);
      throw new Error('Receipt not found');
    }
  }
}

export default InvoiceService;
