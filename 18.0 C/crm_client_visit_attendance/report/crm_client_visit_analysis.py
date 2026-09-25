# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class CrmClientVisitAnalysis(models.Model):
    """
    Client Visit Analysis Report

    This model provides analytical views for client visits with grouping
    and filtering capabilities for graphs, pivots, and list views.
    """
    _name = 'crm.client.visit.analysis'
    _description = 'Client Visit Analysis'
    _auto = False
    _rec_name = 'visit_id'
    _order = 'planned_datetime desc'

    # Visit Information
    visit_id = fields.Many2one('crm.client.visit', string='Visit', readonly=True)
    name = fields.Char(string='Visit Reference', readonly=True)
    client_id = fields.Many2one('res.partner', string='Client', readonly=True)
    lead_id = fields.Many2one('crm.lead', string='Opportunity/Lead', readonly=True)
    leader_employee_id = fields.Many2one('hr.employee', string='Team Leader', readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)

    # Visit Details
    visit_type = fields.Selection([
        ('sales', 'Sales Visit'),
        ('support', 'Support Visit'),
        ('collection', 'Collection Visit'),
        ('relationship', 'Relationship Building'),
        ('inspection', 'Site Inspection'),
    ], string='Visit Type', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', readonly=True)

    outcome = fields.Selection([
        ('successful', 'Successful'),
        ('follow_up_required', 'Follow-up Required'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'Client No-Show'),
    ], string='Outcome', readonly=True)

    # Dates & Duration
    planned_datetime = fields.Datetime(string='Planned Date', readonly=True)
    planned_date = fields.Date(string='Planned Date Only', readonly=True)
    actual_check_in = fields.Datetime(string='Actual Check-In', readonly=True)
    actual_check_out = fields.Datetime(string='Actual Check-Out', readonly=True)

    expected_duration = fields.Float(string='Expected Duration (Hours)', readonly=True, group_operator='avg')
    actual_duration = fields.Float(string='Actual Duration (Hours)', readonly=True, group_operator='avg')
    duration_variance = fields.Float(string='Duration Variance (Hours)', readonly=True, group_operator='avg')

    # Outcome Metrics
    interest_level = fields.Integer(string='Interest Level (%)', readonly=True, group_operator='avg')
    expected_value = fields.Monetary(string='Expected Value', readonly=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    next_action_required = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Next Action Required', readonly=True)

    # Team Information
    team_size = fields.Integer(string='Team Size', readonly=True, help='Number of employees in the visit')
    attendance_count = fields.Integer(string='Attendance Records', readonly=True)

    # Delays & Timeliness
    is_overdue = fields.Boolean(string='Overdue', readonly=True)
    days_to_visit = fields.Integer(string='Days Until Visit', readonly=True, group_operator='avg')

    # Company
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    # Date Grouping Fields
    year = fields.Char(string='Year', readonly=True)
    quarter = fields.Char(string='Quarter', readonly=True)
    month = fields.Char(string='Month', readonly=True)
    week = fields.Char(string='Week', readonly=True)
    day = fields.Char(string='Day', readonly=True)

    def init(self):
        """
        Create the SQL view for visit analysis.

        This view aggregates data from crm.client.visit and related models
        to provide comprehensive reporting capabilities.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)

        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    v.id AS id,
                    v.id AS visit_id,
                    v.name AS name,
                    v.client_id AS client_id,
                    v.lead_id AS lead_id,
                    v.leader_employee_id AS leader_employee_id,
                    v.user_id AS user_id,
                    v.visit_type AS visit_type,
                    v.state AS state,
                    v.outcome AS outcome,
                    
                    -- Dates
                    v.planned_datetime AS planned_datetime,
                    DATE(v.planned_datetime) AS planned_date,
                    v.actual_check_in AS actual_check_in,
                    v.actual_check_out AS actual_check_out,
                    
                    -- Duration
                    v.expected_duration AS expected_duration,
                    CASE
                        WHEN v.actual_check_out IS NOT NULL AND v.actual_check_in IS NOT NULL
                        THEN EXTRACT(EPOCH FROM (v.actual_check_out - v.actual_check_in)) / 3600
                        ELSE 0
                    END AS actual_duration,
                    CASE
                        WHEN v.actual_check_out IS NOT NULL AND v.actual_check_in IS NOT NULL
                        THEN (EXTRACT(EPOCH FROM (v.actual_check_out - v.actual_check_in)) / 3600) - v.expected_duration
                        ELSE 0
                    END AS duration_variance,
                    
                    -- Outcome Metrics
                    v.interest_level AS interest_level,
                    v.expected_value AS expected_value,
                    v.currency_id AS currency_id,
                    v.next_action_required AS next_action_required,
                    
                    -- Team Size
                    1 + (SELECT COUNT(*) FROM crm_visit_employee_rel WHERE visit_id = v.id) AS team_size,
                    (SELECT COUNT(*) FROM crm_client_visit_attendance WHERE visit_id = v.id) AS attendance_count,
                    
                    -- Timeliness
                    CASE
                        WHEN v.state = 'planned' AND v.planned_datetime < NOW()
                        THEN TRUE
                        ELSE FALSE
                    END AS is_overdue,
                    CASE
                        WHEN v.planned_datetime IS NOT NULL
                        THEN DATE_PART('day', v.planned_datetime - NOW())::INTEGER
                        ELSE 0
                    END AS days_to_visit,
                    
                    -- Company
                    v.company_id AS company_id,
                    
                    -- Date Grouping
                    TO_CHAR(v.planned_datetime, 'YYYY') AS year,
                    TO_CHAR(v.planned_datetime, 'YYYY-Q') AS quarter,
                    TO_CHAR(v.planned_datetime, 'YYYY-MM') AS month,
                    TO_CHAR(v.planned_datetime, 'IYYY-IW') AS week,
                    TO_CHAR(v.planned_datetime, 'YYYY-MM-DD') AS day
                    
                FROM crm_client_visit v
                WHERE v.active = TRUE
            )
        """ % self._table

        self.env.cr.execute(query)

