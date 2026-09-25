# -*- coding: utf-8 -*-
"""Fund request workflow model."""

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class FundRequest(models.Model):
    _name = 'fund.request'
    _description = 'Fund Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, id desc'
    _rec_name = 'request_number'

    request_number = fields.Char(
        string='Request Number',
        required=True,
        readonly=True,
        copy=False,
        default='New',
        tracking=True,
    )
    employee_id = fields.Many2one(
        comodel_name='res.partner',
        string='Employee Name',
        required=True,
        tracking=True,
        help='Select the employee requesting the fund.',
    )
    employee_name = fields.Char(
        string='Employee Name (Display)',
        compute='_compute_employee_name',
        store=True,
    )
    request_date = fields.Date(
        string='Request Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    amount = fields.Float(
        string='Amount',
        required=True,
        tracking=True,
        help='Amount of fund requested. Must be greater than 0.',
    )
    purpose = fields.Text(
        string='Purpose',
        required=True,
        tracking=True,
    )
    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Status',
        required=True,
        default='draft',
        tracking=True,
    )
    notes = fields.Text(string='Notes')
    created_by = fields.Many2one(
        comodel_name='res.users',
        string='Created By',
        readonly=True,
        default=lambda self: self.env.user,
    )
    last_modified_by = fields.Many2one(
        comodel_name='res.users',
        string='Last Modified By',
        readonly=True,
    )

    @api.depends('employee_id')
    def _compute_employee_name(self):
        for record in self:
            record.employee_name = record.employee_id.name or ''

    @api.depends('request_number', 'employee_name')
    def _compute_display_name(self):
        for record in self:
            if record.employee_name:
                record.display_name = '%s - %s' % (record.request_number, record.employee_name)
            else:
                record.display_name = record.request_number

    @api.constrains('amount')
    def _check_amount_positive(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_('Fund request amount must be greater than 0.'))

    def _check_manager_access(self):
        if not self.env.user.has_group('nn_fund_management.group_fund_manager'):
            raise AccessError(_('Only a Fund Manager can approve, reject, or reset fund requests.'))

    def action_submit(self):
        for record in self:
            if record.status != 'draft':
                raise ValidationError(_('Only draft requests can be submitted.'))
            record.status = 'submitted'
            record.message_post(body=_('<strong>Submitted:</strong> Fund request submitted for review.'))
        return True

    def action_approve(self):
        self._check_manager_access()
        for record in self:
            if record.status != 'submitted':
                raise ValidationError(_('Only submitted requests can be approved.'))
            record.status = 'approved'
            record.message_post(body=_('<strong>Approved:</strong> Fund request approved.'))
        return True

    def action_reject(self):
        self._check_manager_access()
        for record in self:
            if record.status != 'submitted':
                raise ValidationError(_('Only submitted requests can be rejected.'))
            record.status = 'rejected'
            record.message_post(body=_('<strong>Rejected:</strong> Fund request rejected.'))
        return True

    def action_reset_to_draft(self):
        self._check_manager_access()
        for record in self:
            if record.status not in ('submitted', 'rejected'):
                raise ValidationError(_('Only submitted or rejected requests can be reset to draft.'))
            record.status = 'draft'
            record.message_post(body=_('<strong>Reset:</strong> Fund request reset to draft.'))
        return True

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('request_number', 'New') == 'New':
                vals['request_number'] = sequence.next_by_code('fund.request') or 'New'
            vals['created_by'] = self.env.user.id
            vals['last_modified_by'] = self.env.user.id
        return super().create(vals_list)

    def write(self, vals):
        if vals:
            vals = dict(vals, last_modified_by=self.env.user.id)
        return super().write(vals)

    def unlink(self):
        protected = self.filtered(lambda record: record.status in ('approved', 'rejected'))
        if protected:
            raise ValidationError(_('You cannot delete approved or rejected fund requests.'))
        return super().unlink()

    def action_print_report(self):
        return self.env.ref('nn_fund_management.action_report_fund_request').report_action(self)
