from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PropertyPayment(models.Model):
    _name = 'property.payment'
    _description = 'Property Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    contract_id = fields.Many2one('property.contract', 'Contract')
    so_id = fields.Many2one('sale.order', 'Sales Order')
    name = fields.Char(string='Payment Reference')
    due_date = fields.Date( string='Due Date', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', 'Currency')
    amount = fields.Float(string='Amount', required=True, tracking=True)
    remarks = fields.Text(string='Remarks')
    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('type', 'in', ('bank', 'cash'))]", tracking=True)
    payment_method_id = fields.Many2one('account.payment.method.line', 'Payment Method', domain="[('payment_type', '=', 'inbound'), ('journal_id', '=', journal_id)]")
    payment_id = fields.Many2one('account.payment', string='Payment', readonly=True, copy=False, tracking=True)
    cheque_number = fields.Char(string='Cheque No')
    partner_bank_id = fields.Many2one('res.bank', string='Bank')
    is_pdc = fields.Boolean(string='Is PDC', default=False)
    payment_status = fields.Selection(related='payment_id.state', string='Payment Status', store=True)
    type = fields.Selection([
        ('rent', 'Rent'),
        ('Lease', 'Lease'),
        ('maintenance', 'Maintenance'),
        ('deposit', 'Deposit'),
        ('penalty', 'Penalty'),
        ('fees', 'Fees'),
        ('other', 'Other')
    ], string='Type')
    type_so = fields.Selection([
        ('down_payment', 'Down Payment'),
        ('admin_fees', 'Admin Fees'),
        ('stamp_duty', 'Stamp Duty Fees'),
        ('registration', 'Registration Fees'),
        ('mutation', 'Mutation Fees'),
        ('installment_before', 'Installment Before Handover'),
        ('installment_on', 'Installment On Handover'),
        ('installment_after', 'Installment After Handover'),
        ('others', 'Others'),
    ], 'Type')


    @api.model_create_multi
    def create(self, vals_list):
        res = super(PropertyPayment, self).create(vals_list)
        if res.so_id:
            res.currency_id = res.so_id.currency_id.id

        elif res.contract_id:
            res.currency_id = res.contract_id.currency_id.id
            
        return res

    def action_create_payment(self):
        for rec in self:
            if not rec.payment_id:
                vals = {
                    'payment_type': 'inbound',
                    'is_rent_payment': True,
                    'is_pdc': rec.is_pdc,
                    'amount': rec.amount,
                    'currency_id': rec.currency_id.id,
                    'date': rec.due_date,
                    'journal_id': rec.journal_id.id,
                    'payment_method_line_id': rec.payment_method_id.id,
                    'partner_bank_id': rec.partner_bank_id.id,
                    'company_id': self.env.company.id,
                }
                if rec.so_id:
                    vals.update({
                        'is_rent_payment': False,
                        'partner_id': rec.so_id.partner_id.id,
                        'property_id': rec.so_id.property_id.id,
                        'property_unit_id': rec.so_id.unit_id.id,
                        'so_id': rec.so_id.id,
                    })
                elif rec.contract_id:
                    vals.update({
                        'partner_id': rec.contract_id.partner_id.id,
                        'contract_id': rec.contract_id.id,
                        'property_id': rec.contract_id.property_id.id,
                        'property_unit_id': rec.contract_id.unit_id.id,
                    })

                payment = self.env['account.payment'].sudo().create(vals)
                rec.write({'payment_id': payment.id})

            # Return form view action
            return {
                'type': 'ir.actions.act_window',
                'name': _('Payment'),
                'res_model': 'account.payment',
                'view_mode': 'form',
                'res_id': rec.payment_id.id,
                'target': 'current',
            }
        
    def action_view_payment(self):
        self.ensure_one()
        if not self.payment_id:
            raise ValidationError('No Payment Found for this record.')

        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'views': [(self.env.ref('account.view_account_payment_form').id, 'form')],
            'target': 'current',
            'res_id': self.payment_id.id,
        }

    @api.model
    def cron_action_create_scheduled_payment(self):
        today = fields.Date.today()
        payments_to_create = self.search([
            ('payment_id', '=', False),
            ('contract_id.state', '=', 'active'),
            ('amount', '>', 0),
            ('due_date', '=', today)
        ])
        if payments_to_create:
            for payment in payments_to_create:
                payment.action_create_payment()