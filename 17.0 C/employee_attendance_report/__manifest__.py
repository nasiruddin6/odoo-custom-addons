{
    'name': 'Employee Attendance Report',
    'version': '17.0.1.0.0',
    'summary': 'Employee Attendance Excel Report',
    'description': """
        Employee Attendance Report (Excel)
        - Date wise attendance
        - Employee wise attendance
        - Worked hours summary
        - HR Reporting menu integration
    """,
    'category': 'Human Resources',
    'author': 'Tectise',
    'website': 'https://www.tectise.com',
    'depends': [
        'hr',
        'hr_attendance',
        'hr_holidays',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/attendance_report_wizard_view.xml',
        'views/attendance_report_menu.xml',

    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'license': 'OPL-1',
    'price': 10.00,
    'currency': 'USD',
}
