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

    if (status) {
    const allowedOps = ['=', '!=', '<', '<=', '>', '>='];
    if (!allowedOps.includes(operator ?? '=')) throw new Error('Invalid operator');
    q = q.andWhere('status', operator ?? '=', status);
    }

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


    const allowedBrands = [
       'payment.visa.com',
       'payment.mastercard.com',
       'payment.amex.com'
      ];

    if (!allowedBrands.includes(paymentBrand)) {
      throw new Error('Unsupported payment brand');
    }

    const paymentResponse = await axios.post(`https://${paymentBrand}/payments`, {

      ccNumber,
      ccv,
      expirationDate
    });
    if (paymentResponse.status !== 200) {
      throw new Error('Payment failed');
    }

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
      const sanitizedName = path.basename(pdfName);
      const invoicesDir = path.resolve(__dirname,'../../invoices');
      const filePath = path.join(invoicesDir, sanitizedName);

      if (!filePath.startsWith(invoicesDir)) {
        throw new Error('Invalid file path');
      }
      const data = await fs.readFile(filePath);
      return data;
    } catch (error) {
      // send the error to the standard output
      console.error('Error reading receipt file:', error);
      throw new Error('Receipt not found');
    }
  }
}

export default InvoiceService;
