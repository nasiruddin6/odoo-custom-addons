# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class CrmClientVisit(models.Model):
    _name = 'crm.client.visit'
    _description = 'CRM Client Visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'planned_datetime desc, id desc'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Visit Reference',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True,
    )

    client_id = fields.Many2one(
        'res.partner',
        string='Client / Company',
        required=True,
        tracking=True,
        index=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    # Client Information
    contact_person = fields.Char(
        string='Contact Person',
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Name of the person to meet during the visit',
    )

    contact_designation = fields.Char(
        string='Designation',
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Job title or position of the contact person',
    )

    contact_phone = fields.Char(
        string='Phone',
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Contact phone number',
    )

    contact_email = fields.Char(
        string='Email',
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Contact email address',
    )

    client_address = fields.Text(
        string='Client Address',
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Full address where the visit will take place',
    )

    client_gps_latitude = fields.Float(
        string='GPS Latitude',
        digits=(10, 7),
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='GPS latitude of client location (optional)',
    )

    client_gps_longitude = fields.Float(
        string='GPS Longitude',
        digits=(10, 7),
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='GPS longitude of client location (optional)',
    )

    lead_id = fields.Many2one(
        'crm.lead',
        string='Opportunity/Lead',
        tracking=True,
        domain="[('partner_id', '=', client_id)]",
        index=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    leader_employee_id = fields.Many2one(
        'hr.employee',
        string='Team Leader',
        required=True,
        default=lambda self: self.env.user.employee_id,
        tracking=True,
        index=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        related='leader_employee_id.user_id',
        store=True,
        readonly=True,
    )

    visit_employee_ids = fields.Many2many(
        'hr.employee',
        'crm_visit_employee_rel',
        'visit_id',
        'employee_id',
        string='Team Members',
        tracking=True,
        help='Additional employees participating in this visit',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    # Visit Details
    visit_type = fields.Selection(
        [
            ('sales', 'Sales Visit'),
            ('support', 'Support Visit'),
            ('collection', 'Collection Visit'),
            ('relationship', 'Relationship Building'),
            ('inspection', 'Site Inspection'),
        ],
        string='Visit Type',
        required=True,
        default='sales',
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    purpose = fields.Text(
        string='Purpose',
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    # Planning
    planned_datetime = fields.Datetime(
        string='Planned Date & Time',
        tracking=True,
        index=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    expected_duration = fields.Float(
        string='Expected Duration (Hours)',
        default=1.0,
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    # Check-in/Check-out
    actual_check_in = fields.Datetime(
        string='Actual Check-In',
        readonly=True,
        tracking=True,
        copy=False,
    )

    actual_check_out = fields.Datetime(
        string='Actual Check-Out',
        readonly=True,
        tracking=True,
        copy=False,
    )

    check_in_latitude = fields.Float(
        string='Check-In Latitude',
        digits=(10, 7),
        readonly=True,
        copy=False,
    )

    check_in_longitude = fields.Float(
        string='Check-In Longitude',
        digits=(10, 7),
        readonly=True,
        copy=False,
    )

    check_out_latitude = fields.Float(
        string='Check-Out Latitude',
        digits=(10, 7),
        readonly=True,
        copy=False,
    )

    check_out_longitude = fields.Float(
        string='Check-Out Longitude',
        digits=(10, 7),
        readonly=True,
        copy=False,
    )

    # State & Outcome
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('planned', 'Planned'),
            ('in_progress', 'In Progress'),
            ('review', 'Under Review'),
            ('completed', 'Completed'),
            ('missed', 'Missed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        index=True,
    )

    outcome = fields.Selection(
        [
            ('successful', 'Successful'),
            ('follow_up_required', 'Follow-up Required'),
            ('rescheduled', 'Rescheduled'),
            ('no_show', 'Client No-Show'),
        ],
        string='Outcome',
        tracking=True,
    )

    interest_level = fields.Integer(
        string='Interest Level (%)',
        tracking=True,
        help='Client interest level in percentage (0-100)',
    )

    expected_value = fields.Monetary(
        string='Expected Value',
        currency_field='currency_id',
        tracking=True,
        help='Expected sales value from this visit (for sales-related visits)',
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    next_action_required = fields.Selection(
        [
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        string='Next Action Required',
        tracking=True,
        help='Is there a follow-up action required?',
    )

    notes = fields.Text(
        string='Visit Notes',
        tracking=True,
    )

    next_action = fields.Text(
        string='Next Action',
        tracking=True,
    )

    internal_notes = fields.Text(
        string='Internal Notes',
        tracking=True,
        help='Internal notes visible only to company employees',
    )

    client_remarks = fields.Text(
        string='Client Remarks',
        tracking=True,
        help='Remarks or feedback from the client',
    )

    followup_activity_id = fields.Many2one(
        'mail.activity',
        string='Follow-up Activity',
        readonly=True,
        copy=False,
    )

    # Attachments
    photo_ids = fields.Many2many(
        'ir.attachment',
        'visit_photo_rel',
        'visit_id',
        'attachment_id',
        string='Photos',
        help='Upload photos from the visit',
    )

    document_ids = fields.Many2many(
        'ir.attachment',
        'visit_document_rel',
        'visit_id',
        'attachment_id',
        string='Documents',
        help='Upload documents related to the visit',
    )

    signed_form_ids = fields.Many2many(
        'ir.attachment',
        'visit_signed_form_rel',
        'visit_id',
        'attachment_id',
        string='Signed Forms',
        help='Upload signed forms or agreements from the visit',
    )

    visiting_card_ids = fields.Many2many(
        'ir.attachment',
        'visit_visiting_card_rel',
        'visit_id',
        'attachment_id',
        string='Visiting Cards',
        help='Upload photos of visiting cards received during the visit',
    )

    photo_count = fields.Integer(
        string='Photos Count',
        compute='_compute_attachment_counts',
    )

    document_count = fields.Integer(
        string='Documents Count',
        compute='_compute_attachment_counts',
    )

    signed_form_count = fields.Integer(
        string='Signed Forms Count',
        compute='_compute_attachment_counts',
    )

    visiting_card_count = fields.Integer(
        string='Visiting Cards Count',
        compute='_compute_attachment_counts',
    )

    total_attachment_count = fields.Integer(
        string='Total Attachments',
        compute='_compute_attachment_counts',
    )

    # Company & Active
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    active = fields.Boolean(
        string='Active',
        default=True,
    )

    # Computed Fields
    actual_duration = fields.Float(
        string='Actual Duration (Hours)',
        compute='_compute_actual_duration',
        store=True,
    )

    attendance_ids = fields.One2many(
        'crm.client.visit.attendance',
        'visit_id',
        string='Attendance Records',
    )

    attendance_count = fields.Integer(
        string='Attendance Count',
        compute='_compute_attendance_count',
    )

    activity_count = fields.Integer(
        string='Activity Count',
        compute='_compute_activity_count',
    )

    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_is_overdue',
        store=True,
    )

    # Constraints & Validation
    @api.onchange('client_id')
    def _onchange_client_id(self):
        if self.client_id:
            # Build full address from partner fields
            address_parts = []
            if self.client_id.street:
                address_parts.append(self.client_id.street)
            if self.client_id.street2:
                address_parts.append(self.client_id.street2)
            if self.client_id.city:
                address_parts.append(self.client_id.city)
            if self.client_id.state_id:
                address_parts.append(self.client_id.state_id.name)
            if self.client_id.zip:
                address_parts.append(self.client_id.zip)
            if self.client_id.country_id:
                address_parts.append(self.client_id.country_id.name)

            self.client_address = ', '.join(address_parts) if address_parts else ''
            self.contact_phone = self.client_id.phone or self.client_id.mobile or ''
            self.contact_email = self.client_id.email or ''

            # Try to get contact person from parent/child relationship
            if self.client_id.parent_id:
                # If this is a contact, use contact name and get info from parent
                self.contact_person = self.client_id.name
                self.contact_designation = self.client_id.function or ''
            else:
                # If this is a company, leave contact person empty for manual entry
                self.contact_person = ''
                self.contact_designation = ''

    @api.constrains('leader_employee_id', 'visit_employee_ids')
    def _check_leader_not_in_team_members(self):
        for visit in self:
            if visit.leader_employee_id and visit.leader_employee_id in visit.visit_employee_ids:
                raise ValidationError(
                    _('The team leader cannot be added as a team member. Team members are additional employees.')
                )

    @api.constrains('actual_check_in', 'actual_check_out')
    def _check_check_out_after_check_in(self):
        for visit in self:
            if visit.actual_check_in and visit.actual_check_out:
                if visit.actual_check_out <= visit.actual_check_in:
                    raise ValidationError(
                        _('Check-out time must be after check-in time.')
                    )

    @api.constrains('expected_duration')
    def _check_expected_duration(self):
        for visit in self:
            if visit.expected_duration <= 0:
                raise ValidationError(
                    _('Expected duration must be greater than 0.')
                )

    @api.constrains('interest_level')
    def _check_interest_level(self):
        for visit in self:
            if visit.interest_level and (visit.interest_level < 0 or visit.interest_level > 100):
                raise ValidationError(
                    _('Interest level must be between 0 and 100.')
                )

    # Compute Methods
    @api.depends('actual_check_in', 'actual_check_out')
    def _compute_actual_duration(self):
        for visit in self:
            if visit.actual_check_in and visit.actual_check_out:
                delta = visit.actual_check_out - visit.actual_check_in
                visit.actual_duration = delta.total_seconds() / 3600.0
            else:
                visit.actual_duration = 0.0

    @api.depends('attendance_ids')
    def _compute_attendance_count(self):
        for visit in self:
            visit.attendance_count = len(visit.attendance_ids)

    @api.depends('photo_ids', 'document_ids', 'signed_form_ids', 'visiting_card_ids')
    def _compute_attachment_counts(self):
        for visit in self:
            visit.photo_count = len(visit.photo_ids)
            visit.document_count = len(visit.document_ids)
            visit.signed_form_count = len(visit.signed_form_ids)
            visit.visiting_card_count = len(visit.visiting_card_ids)
            visit.total_attachment_count = (
                visit.photo_count +
                visit.document_count +
                visit.signed_form_count +
                visit.visiting_card_count
            )

    def _compute_activity_count(self):
        for visit in self:
            activity_count = 0
            if visit.client_id:
                activity_count += self.env['mail.activity'].search_count([
                    ('res_model', '=', 'res.partner'),
                    ('res_id', '=', visit.client_id.id),
                ])
            if visit.lead_id:
                activity_count += self.env['mail.activity'].search_count([
                    ('res_model', '=', 'crm.lead'),
                    ('res_id', '=', visit.lead_id.id),
                ])
            visit.activity_count = activity_count

    @api.depends('planned_datetime', 'state')
    def _compute_is_overdue(self):
        """Check if visit is overdue."""
        now = fields.Datetime.now()
        for visit in self:
            visit.is_overdue = (
                visit.state == 'planned' and
                visit.planned_datetime and
                visit.planned_datetime < now
            )

    # CRUD Methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'crm.client.visit'
                ) or _('New')

        visits = super(CrmClientVisit, self).create(vals_list)

        # Log CRM activity for each visit (only if planned_datetime is set)
        for visit in visits:
            if visit.planned_datetime:
                visit._create_crm_activity()

        return visits

    def write(self, vals):
        result = super(CrmClientVisit, self).write(vals)

        # Create or update CRM activity
        for visit in self:
            # If planned_datetime is being set and activity doesn't exist, create it
            if 'planned_datetime' in vals and visit.planned_datetime:
                if not visit.followup_activity_id:
                    visit._create_crm_activity()
                else:
                    visit._update_crm_activity()

        return result

    def unlink(self):
        for visit in self:
            if visit.state in ['in_progress', 'completed']:
                raise UserError(
                    _('Cannot delete visits that are in progress or completed. '
                      'Please cancel them instead.')
                )
        return super(CrmClientVisit, self).unlink()

    # Action Methods
    def action_confirm(self):
        self.ensure_one()

        if self.state != 'draft':
            raise UserError(
                _('Only draft visits can be confirmed.')
            )

        # Validate required fields
        if not self.planned_datetime:
            raise UserError(
                _('Please set a planned date and time before confirming the visit.')
            )

        # Update state to planned
        self.write({'state': 'planned'})

        # Send emails to employees and client
        self._send_visit_confirmation_emails()

        # Create CRM activity
        if self.planned_datetime:
            self._create_crm_activity()

        # Log in chatter
        self.message_post(
            body=_('Visit confirmed and scheduled for %s. Notifications sent to team members and client.') % (
                self.planned_datetime.strftime('%Y-%m-%d %H:%M:%S')
            ),
            message_type='notification',
        )

        return True

    def action_check_in(self):
        self.ensure_one()

        if self.state != 'planned':
            raise UserError(
                _('Only planned visits can be checked in.')
            )

        # Get GPS coordinates from context (would come from mobile app)
        latitude = self.env.context.get('latitude', 0.0)
        longitude = self.env.context.get('longitude', 0.0)

        # Update visit to in_progress state
        self.write({
            'state': 'in_progress',
            'actual_check_in': fields.Datetime.now(),
            'check_in_latitude': latitude,
            'check_in_longitude': longitude,
        })

        # Create visit attendance (WITHOUT HR attendance - will be created on approval)
        self._create_visit_attendance_without_hr(latitude, longitude)

        # Log in chatter
        self.message_post(
            body=_('Visit check-in completed at %s. Awaiting manager approval for attendance creation.') % (
                fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ),
            message_type='notification',
        )

        return True

    def action_check_out(self):
        self.ensure_one()

        if self.state != 'in_progress':
            raise UserError(
                _('Only visits in progress can be checked out.')
            )

        # Get GPS coordinates from context
        latitude = self.env.context.get('latitude', 0.0)
        longitude = self.env.context.get('longitude', 0.0)

        # Update visit to review state
        self.write({
            'state': 'review',
            'actual_check_out': fields.Datetime.now(),
            'check_out_latitude': latitude,
            'check_out_longitude': longitude,
        })

        # Update visit attendance check-out time (HR attendance not created yet)
        self._update_visit_attendance_without_hr(latitude, longitude)

        # Log in chatter
        self.message_post(
            body=_('Visit check-out completed at %s. Duration: %.2f hours. Pending manager review and approval.') % (
                fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                self.actual_duration
            ),
            message_type='notification',
        )

        return True

    def action_approve(self):
        self.ensure_one()

        if self.state != 'review':
            raise UserError(
                _('Only visits under review can be approved.')
            )

        # Create HR attendance records for all employees
        self._create_hr_attendance_records()

        # Mark related CRM activity as done
        if self.followup_activity_id:
            self.followup_activity_id.action_done()

        # Update state to completed
        self.write({'state': 'completed'})

        # Log in chatter
        self.message_post(
            body=_('Visit approved by %s. HR attendance records created for all team members. Related activity marked as done.') % (
                self.env.user.name
            ),
            message_type='notification',
        )

        return True

    def action_reject(self):
        self.ensure_one()

        if self.state != 'review':
            raise UserError(
                _('Only visits under review can be rejected.')
            )

        # Delete visit attendance records (no HR attendance to delete as not created yet)
        self.attendance_ids.unlink()

        # Update state to cancelled
        self.write({'state': 'cancelled'})

        # Log in chatter
        self.message_post(
            body=_('Visit rejected by %s. Attendance records removed.') % (
                self.env.user.name
            ),
            message_type='notification',
        )

        return True

    def action_cancel(self):
        """Cancel the visit."""
        self.ensure_one()

        if self.state == 'completed':
            raise UserError(
                _('Cannot cancel a completed visit.')
            )

        self.write({'state': 'cancelled'})

        # Cancel related attendance if exists
        for attendance in self.attendance_ids:
            if attendance.hr_attendance_id and not attendance.check_out:
                attendance.hr_attendance_id.sudo().unlink()

        self.message_post(
            body=_('Visit cancelled'),
            message_type='notification',
        )

        return True

    def action_mark_missed(self):
        """Mark visit as missed."""
        self.ensure_one()

        if self.state != 'planned':
            raise UserError(
                _('Only planned visits can be marked as missed.')
            )

        self.write({'state': 'missed'})

        self.message_post(
            body=_('Visit marked as missed'),
            message_type='notification',
        )

        return True

    def action_set_to_draft(self):
        self.ensure_one()

        if self.state == 'completed':
            raise UserError(
                _('Cannot reset a completed visit.')
            )

        # Delete all HR attendance records first (if they exist)
        for attendance in self.attendance_ids:
            if attendance.hr_attendance_id:
                # Delete the HR attendance record
                attendance.hr_attendance_id.sudo().unlink()

        # Delete all visit attendance records
        self.attendance_ids.unlink()

        # Reset visit fields
        self.write({
            'state': 'draft',
            'actual_check_in': False,
            'actual_check_out': False,
            'check_in_latitude': 0.0,
            'check_in_longitude': 0.0,
            'check_out_latitude': 0.0,
            'check_out_longitude': 0.0,
        })

        # Log in chatter
        self.message_post(
            body=_('Visit reset to draft. All attendance records removed.'),
            message_type='notification',
        )

        return True

    # Smart Button Actions
    def action_view_attendance(self):
        """Open attendance records."""
        self.ensure_one()

        return {
            'name': _('Visit Attendance'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.client.visit.attendance',
            'view_mode': 'tree,form',
            'domain': [('visit_id', '=', self.id)],
            'context': {'default_visit_id': self.id},
        }

    def action_view_activities(self):
        """Open related CRM activities."""
        self.ensure_one()

        domain = ['|',
            '&', ('res_model', '=', 'res.partner'), ('res_id', '=', self.client_id.id),
            '&', ('res_model', '=', 'crm.lead'), ('res_id', '=', self.lead_id.id)
        ]

        return {
            'name': _('CRM Activities'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.activity',
            'view_mode': 'tree,form',
            'domain': domain,
        }

    def action_view_attachments(self):
        """Open all attachments for this visit."""
        self.ensure_one()

        # Collect all attachment IDs from all categories
        all_attachment_ids = (
            self.photo_ids.ids +
            self.document_ids.ids +
            self.signed_form_ids.ids +
            self.visiting_card_ids.ids
        )

        return {
            'name': _('Visit Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', all_attachment_ids)],
            'context': {
                'default_res_model': 'crm.client.visit',
                'default_res_id': self.id,
            },
        }

    def action_send_email(self):
        """Open email composer to send visit confirmation email."""
        self.ensure_one()

        # Get the email template
        template = self.env.ref('crm_client_visit_attendance.email_template_visit_confirmation', raise_if_not_found=False)

        # Prepare context with template
        ctx = {
            'default_model': 'crm.client.visit',
            'default_res_ids': [self.id],
            'default_template_id': template.id if template else False,
            'default_composition_mode': 'comment',
            'force_email': True,
        }

        return {
            'name': _('Send Visit Confirmation'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    # Private Methods
    def _create_visit_attendance_without_hr(self, latitude, longitude):
        """Create visit attendance records WITHOUT HR attendance (for review workflow)."""
        self.ensure_one()

        # Get all employees: leader + team members
        all_employees = self.leader_employee_id | self.visit_employee_ids

        # Create attendance for each employee (WITHOUT HR attendance)
        for employee in all_employees:
            attendance_vals = {
                'visit_id': self.id,
                'employee_id': employee.id,
                'check_in': self.actual_check_in,
                'latitude': latitude,
                'longitude': longitude,
                'company_id': self.company_id.id,
                # hr_attendance_id left empty - will be created on approval
            }

            self.env['crm.client.visit.attendance'].create(attendance_vals)

        return True

    def _update_visit_attendance_without_hr(self, latitude, longitude):
        """Update visit attendance check-out WITHOUT updating HR attendance (not created yet)."""
        self.ensure_one()

        # Get all employees: leader + team members
        all_employees = self.leader_employee_id | self.visit_employee_ids

        # Update attendance for each employee
        for employee in all_employees:
            attendance = self.attendance_ids.filtered(
                lambda a: a.employee_id == employee and not a.check_out
            )

            if attendance:
                attendance = attendance[0]

                # Update visit attendance (no HR attendance to update yet)
                attendance.write({
                    'check_out': self.actual_check_out,
                })

                # Calculate attendance type
                attendance._compute_attendance_type()

        return True

    def _create_hr_attendance_records(self):
        """Create HR attendance records for all employees after manager approval."""
        self.ensure_one()

        # Get all visit attendance records
        for visit_attendance in self.attendance_ids:
            if not visit_attendance.hr_attendance_id:
                # Create HR attendance
                hr_attendance_vals = {
                    'employee_id': visit_attendance.employee_id.id,
                    'check_in': visit_attendance.check_in,
                }

                # Add check_out if exists
                if visit_attendance.check_out:
                    hr_attendance_vals['check_out'] = visit_attendance.check_out

                hr_attendance = self.env['hr.attendance'].sudo().create(hr_attendance_vals)

                # Link HR attendance to visit attendance
                visit_attendance.write({
                    'hr_attendance_id': hr_attendance.id,
                })

        return True

    def _create_visit_attendance(self, latitude, longitude):
        """Create visit attendance and HR attendance records for leader and team members."""
        self.ensure_one()

        # Get all employees: leader + team members
        all_employees = self.leader_employee_id | self.visit_employee_ids

        # Create attendance for each employee
        for employee in all_employees:
            # Create HR attendance
            hr_attendance = self.env['hr.attendance'].sudo().create({
                'employee_id': employee.id,
                'check_in': self.actual_check_in,
            })

            # Create visit attendance
            attendance_vals = {
                'visit_id': self.id,
                'employee_id': employee.id,
                'check_in': self.actual_check_in,
                'latitude': latitude,
                'longitude': longitude,
                'hr_attendance_id': hr_attendance.id,
                'company_id': self.company_id.id,
            }

            self.env['crm.client.visit.attendance'].create(attendance_vals)

        return True

    def _update_visit_attendance(self, latitude, longitude):
        """Update visit attendance and HR attendance records for all team members."""
        self.ensure_one()

        # Get all employees: leader + team members
        all_employees = self.leader_employee_id | self.visit_employee_ids

        # Update attendance for each employee
        for employee in all_employees:
            attendance = self.attendance_ids.filtered(
                lambda a: a.employee_id == employee and not a.check_out
            )

            if attendance:
                attendance = attendance[0]

                # Update HR attendance
                if attendance.hr_attendance_id:
                    attendance.hr_attendance_id.sudo().write({
                        'check_out': self.actual_check_out,
                    })

                # Update visit attendance
                attendance.write({
                    'check_out': self.actual_check_out,
                })

                # Calculate attendance type
                attendance._compute_attendance_type()

        return True

    def _create_crm_activity(self):
        """Create CRM activity for the visit."""
        self.ensure_one()

        if not self.planned_datetime:
            return

        # Skip if activity already exists
        if self.followup_activity_id:
            return

        # Determine the model and record for activity
        res_model = False
        res_id = False

        if self.lead_id:
            res_model = 'crm.lead'
            res_id = self.lead_id.id
        elif self.client_id:
            res_model = 'res.partner'
            res_id = self.client_id.id

        # Only create activity if we have both model and a valid res_id
        if not res_model or not res_id:
            return

        # Check that res_id is a real integer (not NewId) and greater than 0
        try:
            res_id = int(res_id)
        except (ValueError, TypeError):
            return

        # Only create if we have a valid database ID
        if res_id <= 0:
            return

        # Verify the record actually exists
        try:
            record = self.env[res_model].browse(res_id)
            if not record.exists():
                return
        except Exception:
            return

        # Get activity type for visit
        activity_type = self.env.ref(
            'mail.mail_activity_data_todo',
            raise_if_not_found=False
        )

        summary = _('Client Visit: %s') % (
            dict(self._fields['visit_type'].selection).get(self.visit_type)
        )

        try:
            res_model_id = self.env['ir.model']._get_id(res_model)
            activity = self.env['mail.activity'].sudo().create({
                'res_model_id': res_model_id,
                'res_id': res_id,
                'activity_type_id': activity_type.id if activity_type else False,
                'summary': summary,
                'note': self.purpose or '',
                'date_deadline': self.planned_datetime.date(),
                'user_id': self.user_id.id or self.env.user.id,
            })

            self.followup_activity_id = activity.id
        except Exception as e:
            # Log the error but don't fail the visit creation
            _logger.warning('Failed to create activity for visit %s: %s', self.name, str(e))


    def _update_crm_activity(self):
        """Update related CRM activity when visit is rescheduled."""
        self.ensure_one()

        if self.followup_activity_id and self.planned_datetime:
            self.followup_activity_id.sudo().write({
                'date_deadline': self.planned_datetime.date(),
            })

    def _send_visit_confirmation_emails(self):
        """Send email notifications to employees and client about confirmed visit."""
        self.ensure_one()

        # Get email template
        template = self.env.ref(
            'crm_client_visit_attendance.email_template_visit_confirmation',
            raise_if_not_found=False
        )

        if not template:
            _logger.warning('Visit confirmation email template not found')
            return

        # Collect all employees (leader + team members)
        all_employees = self.leader_employee_id | self.visit_employee_ids

        # Send email to each employee
        for employee in all_employees:
            if employee.work_email or (employee.user_id and employee.user_id.email):
                try:
                    # Set employee context for personalized email
                    template.with_context(
                        employee_name=employee.name,
                        is_leader=(employee == self.leader_employee_id),
                    ).send_mail(
                        self.id,
                        force_send=False,
                        email_values={
                            'email_to': employee.work_email or employee.user_id.email,
                            'subject': _('Visit Scheduled: %s on %s') % (
                                self.client_id.name,
                                self.planned_datetime.strftime('%Y-%m-%d %H:%M')
                            ),
                        }
                    )
                    _logger.info('Visit confirmation email sent to employee: %s', employee.name)
                except Exception as e:
                    _logger.error('Failed to send email to employee %s: %s', employee.name, str(e))

        # Send email to client
        if self.client_id and self.client_id.email:
            try:
                template.with_context(
                    is_client=True,
                    client_name=self.client_id.name,
                ).send_mail(
                    self.id,
                    force_send=False,
                    email_values={
                        'email_to': self.client_id.email,
                        'subject': _('Upcoming Visit Scheduled - %s') % (
                            self.planned_datetime.strftime('%Y-%m-%d %H:%M')
                        ),
                    }
                )
                _logger.info('Visit confirmation email sent to client: %s', self.client_id.name)
            except Exception as e:
                _logger.error('Failed to send email to client %s: %s', self.client_id.name, str(e))


