from odoo import api, models, fields, _


class CRMPropertyVisitExpense(models.Model):
    _name = 'crm.property.visit.expense.line'
    _description = 'CRM Property Visit Expense'


    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id, required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=lambda self: self.env.company.currency_id)
    visit_id = fields.Many2one('crm.property.visit', 'Meeting')
    date = fields.Date('Date', required=True, default=fields.Date.today())
    expense_type = fields.Selection([
        ('fuel', 'Fuel'),
        ('transport', 'Transport'),
        ('parking', 'Parking'),
        ('miscellaneous', 'Miscellaneous'),
    ], 'Expense Type', required=True)
    amount = fields.Monetary('Amount', currency_field="currency_id", required=True)
