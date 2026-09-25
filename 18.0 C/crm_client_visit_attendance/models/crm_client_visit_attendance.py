# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmClientVisitAttendance(models.Model):
    """
    Model to track employee attendance during client visits.
    Automatically created and linked to HR attendance.
    """
    _name = 'crm.client.visit.attendance'
    _description = 'CRM Client Visit Attendance'
    _order = 'check_in desc, id desc'
    _rec_name = 'visit_id'

    visit_id = fields.Many2one(
        'crm.client.visit',
        string='Visit',
        required=True,
        ondelete='cascade',
        index=True,
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        index=True,
    )

    check_in = fields.Datetime(
        string='Check In',
        required=True,
        index=True,
    )

    check_out = fields.Datetime(
        string='Check Out',
        index=True,
    )

    attendance_type = fields.Selection(
        [
            ('present', 'Present'),
            ('late', 'Late'),
            ('partial', 'Partial'),
            ('absent', 'Absent'),
        ],
        string='Attendance Type',
        compute='_compute_attendance_type',
        store=True,
    )

    latitude = fields.Float(
        string='GPS Latitude',
        digits=(10, 7),
    )

    longitude = fields.Float(
        string='GPS Longitude',
        digits=(10, 7),
    )

    hr_attendance_id = fields.Many2one(
        'hr.attendance',
        string='HR Attendance',
        readonly=True,
        ondelete='cascade',
        index=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    # Computed Fields
    duration = fields.Float(
        string='Duration (Hours)',
        compute='_compute_duration',
        store=True,
    )

    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        related='visit_id.client_id',
        store=True,
        readonly=True,
    )

    visit_type = fields.Selection(
        string='Visit Type',
        related='visit_id.visit_type',
        store=True,
        readonly=True,
    )

    # Constraints
    @api.constrains('check_in', 'check_out')
    def _check_check_out_after_check_in(self):
        """Ensure check-out is after check-in."""
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out <= attendance.check_in:
                    raise ValidationError(
                        _('Check-out time must be after check-in time.')
                    )

    @api.constrains('visit_id', 'employee_id')
    def _check_unique_attendance(self):
        """Ensure only one attendance per visit per employee."""
        for attendance in self:
            domain = [
                ('visit_id', '=', attendance.visit_id.id),
                ('employee_id', '=', attendance.employee_id.id),
                ('id', '!=', attendance.id),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(
                    _('An attendance record already exists for this employee on this visit.')
                )

    # Compute Methods
    @api.depends('check_in', 'check_out')
    def _compute_duration(self):
        """Calculate attendance duration in hours."""
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                delta = attendance.check_out - attendance.check_in
                attendance.duration = delta.total_seconds() / 3600.0
            else:
                attendance.duration = 0.0

    @api.depends('check_in', 'check_out', 'visit_id.planned_datetime', 'visit_id.expected_duration')
    def _compute_attendance_type(self):
        """
        Determine attendance type based on planned time and actual attendance.
        - Present: Checked in on time and completed
        - Late: Checked in late
        - Partial: Checked in but duration less than expected
        - Absent: No check-in
        """
        for attendance in self:
            if not attendance.check_in:
                attendance.attendance_type = 'absent'
                continue

            visit = attendance.visit_id

            # Check if late (more than 15 minutes after planned time)
            if visit.planned_datetime:
                late_threshold = visit.planned_datetime + timedelta(minutes=15)
                if attendance.check_in > late_threshold:
                    attendance.attendance_type = 'late'
                    continue

            # Check if partial (duration less than 80% of expected)
            if attendance.check_out and visit.expected_duration:
                if attendance.duration < (visit.expected_duration * 0.8):
                    attendance.attendance_type = 'partial'
                    continue

            # Default to present if checked in
            if attendance.check_in:
                attendance.attendance_type = 'present'
            else:
                attendance.attendance_type = 'absent'

    # CRUD Override
    def write(self, vals):
        """
        Override write to prevent employees from editing attendance.
        Only managers can adjust with reason tracking.
        """
        # Check if user is manager
        is_manager = self.env.user.has_group(
            'crm_client_visit_attendance.group_crm_visit_manager'
        )

        # Fields that employees cannot edit
        restricted_fields = [
            'check_in', 'check_out', 'latitude', 'longitude',
            'hr_attendance_id', 'attendance_type'
        ]

        if not is_manager:
            for field in restricted_fields:
                if field in vals:
                    raise ValidationError(
                        _('You do not have permission to modify attendance records. '
                          'Please contact your manager.')
                    )

        result = super(CrmClientVisitAttendance, self).write(vals)

        # Log changes in chatter if manager adjusted
        if is_manager and any(f in vals for f in restricted_fields):
            for attendance in self:
                attendance.visit_id.message_post(
                    body=_('Attendance record adjusted by manager: %s') % (
                        self.env.user.name
                    ),
                    message_type='notification',
                )

        return result

    def unlink(self):
        """Prevent deletion of attendance records."""
        if not self.env.user.has_group(
            'crm_client_visit_attendance.group_crm_visit_manager'
        ):
            raise ValidationError(
                _('You do not have permission to delete attendance records.')
            )

        # Delete related HR attendance
        for attendance in self:
            if attendance.hr_attendance_id:
                attendance.hr_attendance_id.sudo().unlink()

        return super(CrmClientVisitAttendance, self).unlink()


from datetime import timedelta

