# -*- coding: utf-8 -*-
{
    'name': 'CRM Client Visit & Employee Attendance Management',
    'version': '18.0.1.0.2',
    'category': 'CRM',
    'summary': '''
    CRM client visit management, client visit tracking software, employee attendance management system, field staff visit tracking, sales visit management CRM, 
    customer visit reporting system, employee field attendance app, CRM visit scheduling software, client meeting tracking CRM, sales representative visit tracking, 
    mobile CRM visit management, employee GPS attendance tracking, on-site visit attendance system, CRM activity visit management, sales force visit monitoring, 
    customer visit history CRM, employee visit check-in check-out, field employee attendance tracker, CRM customer visit planner, 
    sales visit attendance management, client visit approval workflow, CRM visit reporting dashboard, employee location-based attendance, 
    field visit management system, CRM visit follow-up tracking, client visit log management, sales visit productivity tracking, 
    employee visit timesheet system, CRM client interaction tracking, mobile employee attendance CRM, field sales attendance solution, 
    customer visit scheduling tool, CRM visit performance analytics, employee visit route tracking, sales visit automation software, 
    CRM client engagement tracking, employee visit compliance tracking, field visit attendance reporting, CRM visit activity automation, 
    customer visit workflow management, employee attendance for field work, CRM sales visit planner, client visit expense tracking, 
    employee visit approval system, CRM visit lifecycle management, sales visit KPI tracking, customer visit documentation system, 
    employee field visit management, CRM visit management platform
    ''',
    'description': """
        CRM Client Visit & Employee Attendance Management
        ==================================================
        This module enables comprehensive management of client visits performed by employees
        with automatic attendance capture based on GPS-validated check-in/check-out.
        
        Key Features:
        -------------
        * Plan and track client visits
        * GPS-based check-in/check-out
        * Automatic attendance recording
        * CRM activity integration
        * Visit outcome tracking
        * Multi-company support
        * Mobile-ready design
        
        Business Benefits:
        ------------------
        * Improved visit accountability
        * Accurate attendance tracking
        * Better client relationship management
        * Real-time visit monitoring
        * Comprehensive reporting
    """,
    'author': 'Tectise',
    'website': 'https://www.tectise.com',
    'license': 'OPL-1',
    'depends': [
        'base',
        'crm',
        'hr',
        'hr_attendance',
        'mail',
        'web',
        'contacts',
    ],
    'data': [
        # Security
        'security/crm_visit_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/crm_visit_sequence.xml',
        'data/mail_template_visit_confirmation.xml',

        # Views
        'views/crm_client_visit_views.xml',
        'views/crm_client_visit_attendance_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/hr_employee_views.xml',
        'views/crm_visit_menus.xml',

        # Reports
        'report/crm_client_visit_analysis_views.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 30.00,
    'currency': 'EUR',
}

