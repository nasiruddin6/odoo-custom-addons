# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class SOInvoiceWizard(models.TransientModel):
	_name = 'so.invoice.wizard'
	_description = 'SO Invoice Wizard'
	
	invoice_for = fields.Selection([
		('down_payment', 'Down Payment'),
		('admin_fees', 'Admin Fees'),
		('stamp_duty', 'Stamp Duty Fees'),
		('registration', 'Registration Fees'),
		('mutation', 'Mutation Fees'),
		('installment_before', 'Installment Before Handover'),
		('installment_on', 'Installment On Handover'),
		('installment_after', 'Installment After Handover'),
		('others', 'Others'),
	], string='Invoice For', required=True, default='down_payment')
	invoice_date = fields.Date(string='Invoice Date', required=True)
	amount = fields.Float(string='Amount', required=True)
	description = fields.Text(string='Description')
	so_id = fields.Many2one('sale.order', string='Sales Order', required=True)
	product_id = fields.Many2one('product.product', string='Product', required=True)
	partner_id = fields.Many2one('res.partner', string='Customer', required=True)
	tax_ids = fields.Many2many('account.tax', string='Taxes')

	@api.onchange('invoice_for')
	def _onchange_invoice_for(self):
		if self.invoice_for:
			product_mapping = {
				'down_payment': 'property_management_rental_sales.product_property_down_payment',
				'admin_fees': 'property_management_rental_sales.product_property_admin_fees',
				'stamp_duty': 'property_management_rental_sales.product_property_stamp_duty',
				'registration': 'property_management_rental_sales.product_property_registration',
				'mutation': 'property_management_rental_sales.product_property_mutation',
				'installment_before': 'property_management_rental_sales.product_property_installment_before',
				'installment_on': 'property_management_rental_sales.product_property_installment_on',
				'installment_after': 'property_management_rental_sales.product_property_installment_after',
				'others': 'property_management_rental_sales.product_property_other',
			}

			xml_id = product_mapping.get(self.invoice_for)
			if xml_id:
				try:
					self.product_id = self.env.ref(xml_id)
				except ValueError:
					self.product_id = False

	@api.onchange('so_id')
	def _onchange_so_id(self):
		if self.so_id and self.so_id.partner_id:
			self.partner_id = self.so_id.partner_id

	def action_create_invoice(self):
		if not self.product_id:
			raise UserError('Please select a product for the invoice.')
		if not self.partner_id:
			raise UserError('Please select a partner.')

		invoice_lines = [(0, 0, {
			'product_id': self.product_id.id,
			'name': f"For {self.invoice_for}: {self.description or ''}",
			'quantity': 1,
			'price_unit': self.amount,
			'tax_ids': [(6, 0, self.tax_ids.ids)] if self.tax_ids else [],
		})]

		invoice_vals = {
			'partner_id': self.partner_id.id,
			'move_type': 'out_invoice',
			'invoice_date': self.invoice_date,
			'invoice_line_ids': invoice_lines,
			'property_id': self.so_id.property_id.id if self.so_id and hasattr(self.so_id, 'property_id') else False,
			'property_unit_id': self.so_id.unit_id.id if self.so_id and hasattr(self.so_id, 'unit_id') else False,
			'is_rent_invoice': False,
		}

		invoice = self.env['account.move'].create(invoice_vals)

		# Create so.installment.line record linking to this SO and invoice
		installment_vals = {
			'so_id': self.so_id.id,
			'name': self.invoice_for,
			'type': self.invoice_for,
			'invoice_date': self.invoice_date,
			'amount': self.amount,
			'currency_id': self.so_id.currency_id.id if self.so_id and self.so_id.currency_id else self.env.company.currency_id.id,
			'invoice_id': invoice.id,
		}
		self.env['so.installment.line'].create(installment_vals)

		return {
			'type': 'ir.actions.act_window',
			'name': 'Customer Invoice',
			'res_model': 'account.move',
			'view_mode': 'form',
			'res_id': invoice.id,
			'target': 'current',
		}
