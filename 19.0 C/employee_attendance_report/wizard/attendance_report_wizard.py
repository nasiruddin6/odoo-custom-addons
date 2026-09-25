import io
import base64
import xlsxwriter
from odoo import models, fields
from datetime import datetime, time, timedelta
from odoo.fields import Datetime


class AttendanceReportWizard(models.TransientModel):
    _name = 'attendance.report.wizard'
    _description = 'Attendance Report Wizard'

    employee_ids = fields.Many2one('hr.employee', string='Employee', required=True)
    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)

    def _get_lang_date_format(self):
        lang = self.env['res.lang']._lang_get(self.env.user.lang or 'en_US')
        return lang.date_format or '%m/%d/%Y'

    def _get_lang_time_format(self):
        lang = self.env['res.lang']._lang_get(self.env.user.lang or 'en_US')
        return lang.time_format or '%H:%M:%S'

    def _get_lang_datetime_format(self):
        return f"{self._get_lang_date_format()} {self._get_lang_time_format()}"

    def _format_date(self, date_value):
        if not date_value:
            return ''
        date_format = self._get_lang_date_format()
        if isinstance(date_value, str):
            date_value = fields.Date.from_string(date_value)
        return date_value.strftime(date_format)

    def _format_datetime(self, datetime_value):
        if not datetime_value:
            return ''
        datetime_format = self._get_lang_datetime_format()
        if isinstance(datetime_value, str):
            datetime_value = fields.Datetime.from_string(datetime_value)
        return datetime_value.strftime(datetime_format)

    def _prepare_workbook_styles(self, workbook):
        return {
            'header': workbook.add_format({
                'bold': True, 'border': 1, 'align': 'center',
                'valign': 'vcenter', 'bg_color': '#D9D9D9', 'font_size': 12
            }),
            'normal': workbook.add_format({
                'border': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 11
            }),
            'hours': workbook.add_format({
                'border': 1, 'num_format': '0.00', 'align': 'right',
                'valign': 'vcenter', 'font_size': 11
            }),
            'company_name': workbook.add_format({
                'bold': True, 'font_size': 16, 'align': 'center',
                'valign': 'vcenter', 'border': 1
            }),
            'company_info': workbook.add_format({
                'font_size': 11, 'align': 'center', 'valign': 'vcenter', 'border': 1
            }),
            'title': workbook.add_format({
                'bold': True, 'font_size': 14, 'align': 'center',
                'valign': 'vcenter', 'border': 1
            }),
            'label_bold': workbook.add_format({
                'bold': True, 'border': 1, 'align': 'left',
                'valign': 'vcenter', 'font_size': 11
            }),
            'value': workbook.add_format({
                'border': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 11
            }),
            'employee_title': workbook.add_format({
                'bold': True, 'font_size': 13, 'align': 'left',
                'valign': 'vcenter', 'border': 1
            }),
        }

    def _get_shift_times(self, emp, weekday):
        default_start = time(8, 0)
        default_end = time(17, 0)

        if not emp.resource_calendar_id:
            return default_start, default_end

        for line in emp.resource_calendar_id.attendance_ids:
            if int(line.dayofweek) == weekday:
                return (
                    time(int(line.hour_from), int((line.hour_from % 1) * 60)),
                    time(int(line.hour_to), int((line.hour_to % 1) * 60))
                )
        return default_start, default_end

    def _get_working_weekdays(self, emp):
        if not emp.resource_calendar_id:
            return set()
        return set(int(line.dayofweek) for line in emp.resource_calendar_id.attendance_ids)

    def _calculate_employee_metrics(self, emp, date_from_dt, date_to_dt):
        attendances = self.env['hr.attendance'].search([
            ('employee_id', '=', emp.id),
            ('check_in', '>=', date_from_dt),
            ('check_in', '<=', date_to_dt),
        ])

        attendance_dates = set()
        late_checkin_dates = set()
        early_checkout_dates = set()

        for att in attendances:
            if not att.check_in:
                continue

            check_in_local = self._convert_to_employee_timezone(att.check_in, emp)
            check_in_date = check_in_local.date()
            attendance_dates.add(check_in_date)

            shift_start, shift_end = self._get_shift_times(emp, check_in_local.weekday())

            if check_in_local.time() > shift_start:
                late_checkin_dates.add(check_in_date)

            if att.check_out:
                check_out_local = self._convert_to_employee_timezone(att.check_out, emp)
                if check_out_local.time() < shift_end:
                    early_checkout_dates.add(check_in_date)

        working_weekdays = self._get_working_weekdays(emp)
        leave_dates_set = self._get_leave_dates(emp, working_weekdays)
        public_holiday_dates = self._get_holiday_dates(emp, working_weekdays)
        public_holiday_dates_set = set(public_holiday_dates.keys())

        total_working_days = 0
        current_date = self.date_from

        if working_weekdays:
            while current_date <= self.date_to:
                if current_date.weekday() in working_weekdays and current_date not in public_holiday_dates_set:
                    total_working_days += 1
                current_date += timedelta(days=1)
        else:
            while current_date <= self.date_to:
                if current_date not in public_holiday_dates_set:
                    total_working_days += 1
                current_date += timedelta(days=1)

        actual_present_dates = attendance_dates - leave_dates_set - public_holiday_dates_set
        actual_late_checkin_dates = late_checkin_dates - leave_dates_set - public_holiday_dates_set
        actual_early_checkout_dates = early_checkout_dates - leave_dates_set - public_holiday_dates_set

        present_days = len(actual_present_dates)
        late_checkins = len(actual_late_checkin_dates)
        early_checkouts = len(actual_early_checkout_dates)
        leave_days = len(leave_dates_set)
        public_holidays = len(public_holiday_dates_set)
        absent_days = max(0, total_working_days - present_days - leave_days)

        overtime_hours = round(sum(max(0, a.worked_hours - 8) for a in attendances), 2)

        return {
            'total_working_days': total_working_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_checkins': late_checkins,
            'early_checkouts': early_checkouts,
            'leave_days': leave_days,
            'public_holidays': public_holidays,
            'overtime_hours': overtime_hours,
        }

    def _get_leave_dates(self, emp, working_weekdays):
        leave_dates = set()
        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', emp.id),
            ('state', 'in', ['validate', 'approved']),
            ('date_from', '<=', datetime.combine(self.date_to, time.max)),
            ('date_to', '>=', datetime.combine(self.date_from, time.min)),
        ])

        for leave in leaves:
            leave_start = leave.date_from.date() if leave.date_from else self.date_from
            leave_end = leave.date_to.date() if leave.date_to else self.date_to

            start = max(leave_start, self.date_from)
            end = min(leave_end, self.date_to)
            current = start

            while current <= end:
                if not working_weekdays or current.weekday() in working_weekdays:
                    leave_dates.add(current)
                current += timedelta(days=1)

        return leave_dates

    def _get_holiday_dates(self, emp, working_weekdays):
        holiday_dates = {}

        if emp.resource_calendar_id:
            holidays = self.env['resource.calendar.leaves'].search([
                ('calendar_id', '=', emp.resource_calendar_id.id),
                '|',
                ('resource_id', '=', False),
                ('resource_id', '=', emp.resource_id.id),
                ('date_from', '<=', datetime.combine(self.date_to, time.max)),
                ('date_to', '>=', datetime.combine(self.date_from, time.min)),
            ])
        else:
            holidays = self.env['resource.calendar.leaves'].search([
                ('resource_id', '=', False),
                ('calendar_id', '=', False),
                ('date_from', '<=', datetime.combine(self.date_to, time.max)),
                ('date_to', '>=', datetime.combine(self.date_from, time.min)),
            ])

        for holiday in holidays:
            if holiday.date_from and holiday.date_to:
                holiday_start_local = self._convert_to_employee_timezone(holiday.date_from, emp)
                holiday_end_local = self._convert_to_employee_timezone(holiday.date_to, emp)

                holiday_start = holiday_start_local.date() if holiday_start_local else self.date_from
                holiday_end = holiday_end_local.date() if holiday_end_local else self.date_to
            else:
                holiday_start = self.date_from
                holiday_end = self.date_to

            start = max(holiday_start, self.date_from)
            end = min(holiday_end, self.date_to)
            current = start

            holiday_name = holiday.name or 'Public Holiday'

            while current <= end:
                if not working_weekdays or current.weekday() in working_weekdays:
                    holiday_dates[current] = holiday_name
                current += timedelta(days=1)

        return holiday_dates

    def _write_company_header(self, worksheet, styles):
        company = self.env.company

        company_address = ', '.join(filter(None, [
            company.street,
            company.city,
            company.state_id.name if company.state_id else None,
            company.country_id.name if company.country_id else None,
        ]))

        company_contact = ' | '.join(filter(None, [
            company.email or '',
            company.phone or '',
            company.website or '',
        ]))

        worksheet.merge_range('A1:G1', company.name or '', styles['company_name'])
        worksheet.merge_range('A2:G2', company_address or '', styles['company_info'])
        worksheet.merge_range('A3:G3', company_contact or '', styles['company_info'])
        worksheet.merge_range('A5:G5', 'Employee Attendance Report', styles['title'])

        row_date = 6
        worksheet.write(row_date, 0, 'Date', styles['label_bold'])
        worksheet.write(row_date, 1, self._format_date(self.date_from), styles['value'])
        worksheet.write(row_date, 2, 'To', styles['label_bold'])
        worksheet.write(row_date, 3, self._format_date(self.date_to), styles['value'])
        worksheet.write(row_date, 4, '', styles['value'])
        worksheet.write(row_date, 5, 'Generated On:', styles['label_bold'])
        worksheet.write(row_date, 6, self._format_date(fields.Date.today()), styles['value'])

        return row_date + 1

    def _write_employee_details(self, worksheet, emp, metrics, styles, start_row):
        row = start_row

        worksheet.merge_range(f'A{row + 1}:G{row + 1}', 'Employee Details :', styles['employee_title'])
        row += 1

        details = [
            ('Employee Name', emp.name or '', 'Total Working Days', metrics['total_working_days']),
            ('Employee ID', str(emp.barcode or ''), 'Present Days', metrics['present_days']),
            ('Job Title', emp.job_title or '', 'Absent Days', metrics['absent_days']),
            ('Department', emp.department_id.name if emp.department_id else '', 'Late Check-ins',
             metrics['late_checkins']),
            ('Employee Type', emp.employee_type or '', 'Early Check-outs', metrics['early_checkouts']),
            ('Work Location', emp.work_location_id.name if emp.work_location_id else '', 'Leave Days (Approved)',
             metrics['leave_days']),
            ('Working Hours', emp.resource_calendar_id.name if emp.resource_calendar_id else '', 'Holidays',
             metrics['public_holidays']),
        ]

        for label1, value1, label2, value2 in details:
            worksheet.write(row, 0, label1, styles['label_bold'])
            worksheet.merge_range(row, 1, row, 4, value1, styles['value'])
            worksheet.write(row, 5, label2, styles['label_bold'])
            worksheet.write(row, 6, value2, styles['value'])
            row += 1

        worksheet.write(row, 0, 'Overtime Hours', styles['label_bold'])
        worksheet.merge_range(row, 1, row, 6, metrics['overtime_hours'], styles['value'])

        return row + 2

    def _convert_to_employee_timezone(self, utc_datetime, employee):
        if not utc_datetime:
            return None

        import pytz
        emp_tz = employee.tz or self.env.user.tz or 'UTC'
        emp_timezone = pytz.timezone(emp_tz)

        if isinstance(utc_datetime, str):
            utc_datetime = fields.Datetime.from_string(utc_datetime)

        if not utc_datetime.tzinfo:
            utc_datetime = pytz.UTC.localize(utc_datetime)

        local_datetime = utc_datetime.astimezone(emp_timezone)
        return local_datetime.replace(tzinfo=None)

    def _determine_attendance_status(self, work_date, emp, day_attendance,
                                     emp_public_holiday_dates, emp_leave_dates):
        if work_date in emp_leave_dates:
            return 'Leave'

        if work_date in emp_public_holiday_dates:
            holiday_name = emp_public_holiday_dates.get(work_date, 'Holiday')
            return f'Holiday - {holiday_name}'

        if not day_attendance:
            working_weekdays = self._get_working_weekdays(emp)
            if not working_weekdays or work_date.weekday() in working_weekdays:
                return 'Absent'
            return 'Non-Working Day'

        shift_start, shift_end = self._get_shift_times(emp, work_date.weekday())

        check_in = self._convert_to_employee_timezone(day_attendance.check_in, emp) if day_attendance.check_in else None
        check_out = self._convert_to_employee_timezone(day_attendance.check_out, emp) if day_attendance.check_out else None

        is_late = check_in and check_in.time() > shift_start
        is_early = check_out and check_out.time() < shift_end

        if is_late and is_early:
            return 'Late & Early Checkout'
        if is_late:
            return 'Late'
        if is_early:
            return 'Early Checkout'
        return 'Present'

    def _write_attendance_table(self, worksheet, emp, date_from_dt, date_to_dt, styles, start_row):
        row = start_row

        headers = ['Date', 'Day', 'Check-In', 'Check-Out', 'Working Hours', 'Extra Hours', 'Status']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, styles['header'])
        row += 1

        attendances = self.env['hr.attendance'].search([
            ('employee_id', '=', emp.id),
            ('check_in', '>=', date_from_dt),
            ('check_in', '<=', date_to_dt),
        ])

        working_weekdays = self._get_working_weekdays(emp)
        emp_leave_dates = self._get_leave_dates(emp, working_weekdays)
        emp_public_holiday_dates = self._get_holiday_dates(emp, working_weekdays)

        emp_attendance_dates = {}
        for att in attendances:
            if att.check_in:
                check_in_local = self._convert_to_employee_timezone(att.check_in, emp)
                check_in_date = check_in_local.date()
                emp_attendance_dates[check_in_date] = att

        all_working_dates = []
        current_date = self.date_from
        while current_date <= self.date_to:
            if not working_weekdays or current_date.weekday() in working_weekdays:
                all_working_dates.append(current_date)
            current_date += timedelta(days=1)

        for work_date in all_working_dates:
            day_attendance = emp_attendance_dates.get(work_date)

            if day_attendance:
                check_in = self._convert_to_employee_timezone(day_attendance.check_in, emp)
                check_out = self._convert_to_employee_timezone(day_attendance.check_out, emp)

                worksheet.write(row, 0, self._format_date(check_in.date() if check_in else work_date), styles['normal'])
                worksheet.write(row, 1, (check_in.strftime('%A') if check_in else work_date.strftime('%A')), styles['normal'])
                worksheet.write(row, 2, self._format_datetime(check_in) if check_in else '', styles['normal'])
                worksheet.write(row, 3, self._format_datetime(check_out) if check_out else '', styles['normal'])

                working_hours = day_attendance.worked_hours or 0.0
                extra_hours = max(0.0, working_hours - 8.0)

                worksheet.write(row, 4, working_hours, styles['hours'])
                worksheet.write(row, 5, extra_hours, styles['hours'])
            else:
                worksheet.write(row, 0, self._format_date(work_date), styles['normal'])
                worksheet.write(row, 1, work_date.strftime('%A'), styles['normal'])
                worksheet.write(row, 2, '', styles['normal'])
                worksheet.write(row, 3, '', styles['normal'])
                worksheet.write(row, 4, 0.00, styles['hours'])
                worksheet.write(row, 5, 0.00, styles['hours'])

            status = self._determine_attendance_status(
                work_date, emp, day_attendance,
                emp_public_holiday_dates, emp_leave_dates
            )
            worksheet.write(row, 6, status, styles['normal'])
            row += 1

        return row

    def action_generate_report(self):
        date_from_dt = datetime.combine(self.date_from, time.min)
        date_to_dt = datetime.combine(self.date_to, time.max)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Attendance Report')

        styles = self._prepare_workbook_styles(workbook)

        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 18)
        worksheet.set_column('E:E', 16)
        worksheet.set_column('F:F', 22)
        worksheet.set_column('G:G', 18)

        row = self._write_company_header(worksheet, styles)

        for emp in self.employee_ids:
            metrics = self._calculate_employee_metrics(emp, date_from_dt, date_to_dt)
            row = self._write_employee_details(worksheet, emp, metrics, styles, row)
            row = self._write_attendance_table(worksheet, emp, date_from_dt, date_to_dt, styles, row)

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': 'Employee_Attendance_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': 'attendance.report.wizard',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true&filename=Employee_Attendance_Report.xlsx',
            'target': 'self',
        }
