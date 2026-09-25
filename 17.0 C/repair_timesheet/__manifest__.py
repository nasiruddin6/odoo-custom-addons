{
    "name": "Repair Timesheet",
    "summary": """
    Repair Timesheet Management, Repair Order Timesheet, Repair Labor Time Tracking, 
    Odoo Repair Timesheet, Repair Job Time Tracking, Technician Timesheet Management, 
    Repair Work Hours Tracking, Repair Service Timesheet, Maintenance Repair Timesheet, 
    Repair Task Time Logger, Odoo Repair Labor Tracking, Field Service Repair Timesheet, 
    Repair Workshop Timesheet, Service Repair Time Management, Multi Technician Repair Timesheet, 
    Repair Order Labor Cost Tracking, Automated Repair Timesheet, Manual Repair Time Entry, 
    Repair Job Costing Timesheet, Repair Time Tracker for Odoo, Repair Activity Timesheet, 
    Repair Service Management Timesheet, Repair Work Log System, Odoo Technician Time Tracker, 
    Repair Labor Productivity Tracking, Repair Task Duration Tracking, Service Center Repair Timesheet, 
    Repair Job Performance Analysis, Planned vs Actual Repair Time, Repair Order Work Log, 
    Repair Workforce Management, Repair Service Scheduling Timesheet, Repair Employee Timesheet, 
    Repair Order Cost Control, Repair Operations Time Tracking, Repair Billing Based on Timesheet, 
    Repair Labor Analytics, Repair Service Efficiency Tracking, Repair Job Time Automation, 
    Workshop Repair Timesheet Software, Repair Order Time Recording, Repair Labor Management System, 
    Repair Job Reporting Timesheet, Repair Service Work Hours, Repair Technician Productivity, 
    Repair Maintenance Labor Tracking, Repair Job Time Calculation, Repair Order Timesheet Automation
    """,
    "description": """
        This module allows you to add technicians to repair orders and track their time using timesheets.
        
        Key Features:
        -------------
        * Assign multiple technicians to a repairs order
        * Track time spent on repairs using timesheets
        * Generate reports on technician performance and time allocation
        * Seamless integration with Odoo's repair and HR modules
        
        Business Benefits:
        ------------------
        * Improved resource management
        * Enhanced visibility into repair processes
        * Better billing and cost tracking for repairs
        * Increased accountability for technicians
    """,
    "version": '17.0.1.1',
    "category": "Repair",
    'author': 'Tectise',
    'website': 'https://www.tectise.com',
    'license': 'OPL-1',
    "depends": ["base_setup", "repair", "hr", "hr_timesheet"],
    "data": [
        "views/repair_order_view.xml",
        'views/res_config_setting_views.xml',
        'report/repair_order_report.xml',
    ],
    'live_test_url': '',
    'demo': [],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 10.00,
    'currency': 'EUR',
}
