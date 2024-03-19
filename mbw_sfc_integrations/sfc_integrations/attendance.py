import frappe
from frappe import _
from frappe.utils import get_time
from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log
from mbw_sfc_integrations.sfc_integrations.validators import validate_date, validate_choice, validate_not_none
from mbw_sfc_integrations.sfc_integrations.constants import STATUS_ATTENDANCE
from mbw_sfc_integrations.sfc_integrations.helper import gen_response, exception_handel, get_value_child_doctype
from frappe.utils import nowdate, getdate
import calendar

def create_attendance(payload, request_id=None):
	try:
		# Thiết lập người dùng hiện tại và request_id (nếu có)
		frappe.set_user("Administrator")
		frappe.flags.request_id = request_id

		attendance = create_attendance_from_payload(payload)
		attendance.insert()
		attendance.submit()

	except Exception as e:
		create_sfc_log(status="Error", exception=e, rollback=True)
	else:
		create_sfc_log(status="Success")

def create_attendance_from_payload(payload):
    # Xử lý dữ liệu từ payload và tạo Attendance mới
    attendance = frappe.new_doc("Attendance")

    fields = ["employee", "company", "shift", "working_hours", "late_entry", "early_exit", "late_check_in", "early_check_out", "custom_number_of_late_days", "custom_late_working_hours"]
    for key, value in payload.items():
        if key in fields:
           attendance.set(key, value)
    attendance.status = validate_choice(STATUS_ATTENDANCE)(payload.get("status", "Present"))
    attendance.attendance_date = validate_date(payload.get("attendance_date")/1000)
    attendance.sfc_key = validate_not_none(payload.get('sfc_key'))

    return attendance

def update_attendance(payload, request_id=None):
	try:
		# Thiết lập người dùng hiện tại và request_id (nếu có)
		frappe.set_user("Administrator")
		frappe.flags.request_id = request_id

        # Lấy Attendance cần cập nhật từ cơ sở dữ liệu
		sfc_key = validate_not_none(payload.get('sfc_key'))
		if frappe.db.exists("Attendance", {"sfc_key":sfc_key}):
			attendance_name = frappe.get_doc("Attendance", {"sfc_key":sfc_key})

			# Cập nhật các trường dữ liệu mới từ payload
			for field, value in dict(payload).items():
				setattr(attendance_name, field, value)
			attendance_name.save()
		else:
			frappe.throw(("Attendance không tồn tại!"))

	except Exception as e:
		create_sfc_log(status="Error", exception=e, rollback=True)
	else:
		create_sfc_log(status="Success")

@frappe.whitelist( allow_guest=True)
def get_attendance(**kwargs):
	try:
		filters = {}
		month = kwargs.get('month')
		year = kwargs.get('year')
		employee = kwargs.get('employee')
		department = kwargs.get('department')
		page_number = int(kwargs.get('page_number')) if kwargs.get('page_number') and int(kwargs.get('page_number')) >= 1 else 1
		page_size =  int(kwargs.get('page_size', 20))
		if month:
			filters['month'] = month
		if year:
			filters['year'] = year
		if employee:
			filters['employee'] = employee
		if department:
			filters['department'] = department

		data = frappe.db.get_list('SFC Attendance Monthly Report', filters=filters, start=page_size*(page_number-1), page_length=page_size, fields=['*'])
		for i in data:
			i['attendance_daily'] = get_value_child_doctype('SFC Attendance Monthly Report', i['name'], 'attendance_daily')

		data_count = len(frappe.db.get_list('SFC Attendance Monthly Report', filters=filters,fields=['*']))
		return gen_response(200, 'Thành công', {
			"data": data,
			"totals": data_count,
			"page_number": page_number,
			"page_size": page_size
		})

	except Exception as e:
		return exception_handel(e)


def list_attendance(employee, start_date, end_date):
        list_attendances = frappe.get_all(
            'Attendance',
            filters={"creation": (">=", start_date), 
                     "creation": ("<=", end_date), 
                     "employee": employee, 
					 "docstatus": 1
                	},
            fields=['*']
        )
        return list_attendances


def update_attendance_monthly(doc, method=None):
	# Lấy ngày tháng để truy xuất dữ liệu
	month = int(nowdate().split('-')[1])
	year = int(nowdate().split('-')[0])
	start_date_str = f'{year:04d}-{month:02d}-01'
	last_day_of_month = calendar.monthrange(year, month)[1]
	end_date_str = f'{year:04d}-{month:02d}-{last_day_of_month:02d}'
	start_date = getdate(start_date_str)
	end_date = getdate(end_date_str)
	attendance = doc.as_dict()
	list_attendances = list_attendance(employee=attendance['employee'], start_date=start_date, end_date=end_date)

	exist_monthly_att = frappe.get_all(
            'SFC Attendance Monthly Report',
            filters={'month': month, 'year': year, 'employee': attendance['employee']},
            fields=['name'],
        )
	
	if exist_monthly_att:
		frappe.delete_doc('SFC Attendance Monthly Report', exist_monthly_att[0]['name'])
		monthly_att_doc = frappe.new_doc('SFC Attendance Monthly Report')
		monthly_att_doc.year = year
		monthly_att_doc.month = month
		monthly_att_doc.employee = attendance['employee']
		monthly_att_doc.employee_name = attendance['employee_name']
		monthly_att_doc.department = attendance['department']
		monthly_att_doc.work_hours_monthly = 0
		monthly_att_doc.number_of_hours_monthly = 0
		monthly_att_doc.late_arrival_time_monthly = 0
		monthly_att_doc.late_arrival_time = 0
		monthly_att_doc.number_of_late_arrival = 0
		monthly_att_doc.early_arrival_time_monthly = 0
		monthly_att_doc.early_arrival_work_monthly = 0
		monthly_att_doc.number_of_early_arrival = 0
		monthly_att_doc.number_work_absent_monthly = 0
		monthly_att_doc.number_hour_absent_monthly = 0
		monthly_att_doc.number_of_breaktime = 0
		monthly_att_doc.number_work_unexplain_absence_monthly = 0
		monthly_att_doc.number_work_explain_absence_monthly = 0
		monthly_att_doc.number_hour_explain_absence_monthly = 0
		monthly_att_doc.number_work_shift_monthly = 0
		monthly_att_doc.number_of_holiday_monthly = 0
		monthly_att_doc.work_of_mission_monthly = 0
		monthly_att_doc.extra_hour_day_monthly = 0
		monthly_att_doc.extra_hour_night_monthly = 0
		monthly_att_doc.extra_hour_monthly = 0
		monthly_att_doc.extra_hour_off_day_monthly = 0
		monthly_att_doc.extra_hour_off_monthly = 0
		monthly_att_doc.extra_hour_off_night_monthly = 0
		monthly_att_doc.extra_hour_holiday_day_monthly = 0
		monthly_att_doc.extra_hour_holiday_night_monthly = 0
		monthly_att_doc.extra_hour_holiday_monthly = 0
		monthly_att_doc.extra_hours_monthly = 0
		monthly_att_doc.number_of_extra_hour = 0
		monthly_att_doc.overtime_hour_off_monthly = 0
		monthly_att_doc.overtime_hour_holiday_monthly = 0
		monthly_att_doc.overtime_hours_monthly = 0
		monthly_att_doc.overtime_hour_total = 0
		monthly_att_doc.overtime_work_off_monthly = 0
		monthly_att_doc.overtime_work_holiday_monthly = 0
		monthly_att_doc.overtime_works_monthly = 0
		monthly_att_doc.overtime_works_total = 0
		monthly_att_doc.overtime_works_extract = 0
		monthly_att_doc.number_of_overtime = 0
		monthly_att_doc.throughout_hour_monthly = 0
		monthly_att_doc.throughout_work_monthly = 0
		monthly_att_doc.throughout_work_extract_monthly = 0
		monthly_att_doc.throughout_hour_extract_monthly = 0
		monthly_att_doc.hc_work_monthly = 0
		monthly_att_doc.hc_hour_monthly = 0
		monthly_att_doc.hc_work_extract_monthly = 0
		monthly_att_doc.hc_hour_extract_monthly = 0
		monthly_att_doc.hc_number = 0
		monthly_att_doc.number_work_holiday_monthly = 0
		monthly_att_doc.number_hour_holiday_monthly = 0
		monthly_att_doc.number_of_day_work = 0
		monthly_att_doc.number_work_shift_monthly = 0

		sign = ''
		for i in list_attendances:
			monthly_att_doc.work_hours_monthly += i['work_hours']
			monthly_att_doc.number_of_hours_monthly += i['number_of_hours']
			monthly_att_doc.late_arrival_time_monthly += i['late_arrival_time']
			monthly_att_doc.late_arrival_time += i['late_arrival_work']
			if i['late_arrival_time'] > 0:
				monthly_att_doc.number_of_late_arrival += 1
			monthly_att_doc.early_arrival_time_monthly += i['early_arrival_time']
			monthly_att_doc.early_arrival_work_monthly += i['early_arrival_work']
			if i['early_arrival_time'] > 0:
				monthly_att_doc.number_of_early_arrival += 1
			monthly_att_doc.number_work_absent_monthly += i['number_work_absent']
			monthly_att_doc.number_hour_absent_monthly += i['number_hour_absent']
			if i['is_breaktime'] == True:
				monthly_att_doc.number_of_breaktime += 1
			monthly_att_doc.number_work_unexplain_absence_monthly += i['number_work_unexplain_absence']
			if i['is_absence_letter'] == True:
				monthly_att_doc.number_work_explain_absence_monthly += i['work_hours']
				monthly_att_doc.number_hour_explain_absence_monthly += i['number_of_hours']
			monthly_att_doc.number_work_shift_monthly += i['number_work_shift']
			monthly_att_doc.number_of_holiday_monthly += i['number_of_holiday']
			monthly_att_doc.work_of_mission_monthly += i['work_of_mission']
			monthly_att_doc.extra_hour_day_monthly += i['extra_hour_day']
			monthly_att_doc.extra_hour_night_monthly += i['extra_hour_night']
			monthly_att_doc.extra_hour_monthly += (i['extra_hour_day']+ i['extra_hour_night'])
			monthly_att_doc.extra_hour_off_day_monthly += i['extra_hour_off_day']
			monthly_att_doc.extra_hour_off_night_monthly += i['extra_hour_off_night']
			monthly_att_doc.extra_hour_off_monthly += (i['extra_hour_off_day'] + i['extra_hour_off_night'])
			monthly_att_doc.extra_hour_holiday_day_monthly += i['extra_hour_holiday_day']
			monthly_att_doc.extra_hour_holiday_night_monthly += i['extra_hour_holiday_night']
			monthly_att_doc.extra_hour_holiday_monthly += (i['extra_hour_holiday_day'] + i['extra_hour_holiday_night'])
			monthly_att_doc.extra_hours_monthly += i['extra_hours']
			if i['is_extra_letter'] == True:
				monthly_att_doc.number_of_extra_hour += 1
			monthly_att_doc.overtime_hour_off_monthly += i['overtime_hour_off']
			monthly_att_doc.overtime_hour_holiday_monthly += i['overtime_hour_holiday']
			monthly_att_doc.overtime_hours_monthly += i['overtime_hours']
			monthly_att_doc.overtime_hour_total += (i['overtime_hour_off'] + i['overtime_hour_holiday'] + i['overtime_hours'])
			monthly_att_doc.overtime_work_off_monthly += i['overtime_work_off']
			monthly_att_doc.overtime_work_holiday_monthly += i['overtime_work_holiday']
			monthly_att_doc.overtime_works_monthly += i['overtime_works']
			monthly_att_doc.overtime_works_total += (i['overtime_works'] + i['overtime_work_holiday'] + i['overtime_work_off'])
			monthly_att_doc.overtime_works_extract += i['overtime_works_extract']
			if i['is_overtime_letter'] == True:
				monthly_att_doc.number_of_overtime += 1
			monthly_att_doc.throughout_hour_monthly += i['throughout_hour']
			monthly_att_doc.throughout_work_monthly += i['throughout_work']
			monthly_att_doc.throughout_work_extract_monthly += i['throughout_work_extract']
			monthly_att_doc.throughout_hour_extract_monthly += i['throughout_hour_extract']
			monthly_att_doc.hc_work_monthly += i['hc_work']
			monthly_att_doc.hc_hour_monthly += i['hc_hour']
			monthly_att_doc.hc_work_extract_monthly += i['hc_work_extract']
			monthly_att_doc.hc_hour_extract_monthly == i['hc_hour_extract']
			monthly_att_doc.hc_number += 0
			monthly_att_doc.number_work_holiday_monthly += i['number_work_holiday']
			monthly_att_doc.number_hour_holiday_monthly += i['number_hour_holiday']
			if i['is_checkin'] == True:
				monthly_att_doc.number_of_day_work += 1
			monthly_att_doc.number_work_shift_monthly += i['number_work_shift']

			if i['is_off'] == True:
				sign = 'OFF'
			if i['is_breaktime'] == True:
				sign = 'QC'
			if i['is_holiday'] == True:
				sign = 'L'
			if i['late_arrival_time'] > 0 or i['early_arrival_time'] > 0:
				sign = 'HE'
			if i['is_faceid'] == True:
				sign = 'FID'
			if i['is_over_day'] == True:
				sign = 'ON'
			if i['has_change'] == True:
				sign = 'EA'
			if i['is_absence_letter'] == True:
				sign = 'P'
			if i['is_absence_letter'] == True and i['work_hours'] == 0:
				sign = 'KL'
			if i['is_later_letter']:
				sign = 'VM'
			if i['is_overtime_letter'] == True:
				sign = '+'
			if i['is_extra_letter'] == True:
				sign = 'OT'
			if i['is_misson_letter'] == True:
				sign = 'CT'
			if i['is_worktime_letter'] == True:
				sign = 'CD'
			if i['is_shiftchange_letter'] == True:
				sign = 'DC'
			if i['is_checkin_letter'] == True:
				sign = 'GT'
			monthly_att_doc.append('attendance_daily', {
				'att_day': i['attendance_date'],
				'work_hours': i['work_hours'],
				'sign': sign
			})

		monthly_att_doc.insert(ignore_permissions=True)

	else:
		sign = ''
		if attendance['is_off'] == True:
			sign = 'OFF'
		if attendance['is_breaktime'] == True:
			sign = 'QC'
		if attendance['is_holiday'] == True:
			sign = 'L'
		if attendance['late_arrival_time'] > 0 or attendance['early_arrival_time'] > 0:
			sign = 'HE'
		if attendance['is_faceid'] == True:
			sign = 'FID'
		if attendance['is_over_day'] == True:
			sign = 'ON'
		if attendance['has_change'] == True:
			sign = 'EA'
		if attendance['is_absence_letter'] == True:
			sign = 'P'
		if attendance['is_absence_letter'] == True and attendance['work_hours'] == 0:
			sign = 'KL'
		if attendance['is_later_letter']:
			sign = 'VM'
		if attendance['is_overtime_letter'] == True:
			sign = '+'
		if attendance['is_extra_letter'] == True:
			sign = 'OT'
		if attendance['is_misson_letter'] == True:
			sign = 'CT'
		if attendance['is_worktime_letter'] == True:
			sign = 'CD'
		if attendance['is_shiftchange_letter'] == True:
			sign = 'DC'
		if attendance['is_checkin_letter'] == True:
			sign = 'GT'
		monthly_att_doc = frappe.get_doc({
			'doctype': 'SFC Attendance Monthly Report',
			'year': year,
			'month': month,
			'employee': attendance['employee'],
			'employee_name': attendance['employee_name'],
			'department': attendance['department'],
			'work_hours_monthly': attendance['work_hours'],
			'number_of_hours_monthly': attendance['number_of_hours'],
			'late_arrival_time_monthly': attendance['late_arrival_time'],
			'late_arrival_work_monthly': attendance['late_arrival_work'],
			'number_of_late_arrival': 1 if attendance['late_arrival_time'] > 0 else 0,
			'early_arrival_time_monthly': attendance['early_arrival_time'],
			'early_arrival_work_monthly': attendance['early_arrival_work'],
			'number_of_early_arrival': 1 if attendance['early_arrival_time'] > 0 else 0,
			'number_work_absent_monthly': attendance['number_work_absent'],
			'number_hour_absent_monthly': attendance['number_hour_absent'],
			'number_absent': 1 if attendance['number_hour_absent'] > 0 else 0,
			'number_of_breaktime': 1 if attendance['is_breaktime'] == True else 0,
			'number_work_unexplain_absence_monthly': attendance['number_work_unexplain_absence'],
			'number_work_explain_absence_monthly': attendance['work_hours'] if attendance['is_absence_letter'] == True else 0,
			'number_hour_explain_absence_monthly': attendance['number_of_hours'] if attendance['is_absence_letter'] == True else 0,
			'number_work_shift_monthly': attendance['number_work_shift'],
			'number_of_holiday_monthly': attendance['number_of_holiday'],
			'work_of_mission_monthly': attendance['work_of_mission'],
			'extra_hour_day_monthly': attendance['extra_hour_day'],
			'extra_hour_night_monthly': attendance['extra_hour_night'],
			'extra_hour_monthly': attendance['extra_hour_day'] + attendance['extra_hour_night'],
			'extra_hour_off_day_monthly': attendance['extra_hour_off_day'],
			'extra_hour_off_night_monthly': attendance['extra_hour_off_night'],
			'extra_hour_off_monthly': attendance['extra_hour_off_day'] + attendance['extra_hour_off_night'],
			'extra_hour_holiday_day_monthly': attendance['extra_hour_holiday_day'],
			'extra_hour_holiday_night_monthly': attendance['extra_hour_holiday_night'],
			'extra_hour_holiday_monthly': attendance['extra_hour_holiday_day'] + attendance['extra_hour_holiday_night'],
			'extra_hours_monthly': attendance['extra_hours'],
			'number_of_extra_hour': 1 if attendance['is_extra_letter'] == True else 0,
			'overtime_hour_off_monthly': attendance['overtime_hour_off'],
			'overtime_hour_holiday_monthly': attendance['overtime_hour_holiday'],
			'overtime_hours_monthly': attendance['overtime_hours'],
			'overtime_hour_total': attendance['overtime_hour_off'] +  attendance['overtime_hour_holiday'] + attendance['overtime_hours'],
			'overtime_work_off_monthly': attendance['overtime_work_off'],
			'overtime_work_holiday_monthly': attendance['overtime_work_holiday'],
			'overtime_works_monthly': attendance['overtime_works'],
			'overtime_works_total': attendance['overtime_works'] + attendance['overtime_work_off'] + attendance['overtime_work_holiday'],
			'overtime_works_extract': attendance['overtime_works_extract'],
			'number_of_overtime': 1 if attendance['is_overtime_letter'] == True else 0,
			'throughout_hour_monthly': attendance['throughout_hour'],
			'throughout_work_monthly': attendance['throughout_work'],
			'throughout_work_extract_monthly': attendance['throughout_work_extract'],
			'throughout_hour_extract_monthly': attendance['throughout_hour_extract'],
			'hc_work_monthly': attendance['hc_work'],
			'hc_hour_monthly': attendance['hc_hour'],
			'hc_work_extract_monthly': attendance['hc_work_extract'],
			'hc_hour_extract_monthly': attendance['hc_hour_extract'],
			'hc_number': 0,
			'number_work_holiday_monthly': attendance['number_work_holiday'],
			'number_hour_holiday_monthly': attendance['number_hour_holiday'],
			'number_of_day_work': 1 if attendance['is_checkin'] == True else 0,
			'number_work_shift_monthly': attendance['number_work_shift'],
			'attendance_daily': [{
				'att_day': attendance['attendance_date'],
				'work_hours': attendance['work_hours'],
				'sign': sign
			}]
		})
		monthly_att_doc.insert(ignore_permissions=True)