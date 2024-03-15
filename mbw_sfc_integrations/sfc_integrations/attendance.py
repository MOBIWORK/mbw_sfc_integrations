import frappe
from frappe import _
from frappe.utils import get_time
from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log
from mbw_sfc_integrations.sfc_integrations.validators import validate_date, validate_choice, validate_not_none
from mbw_sfc_integrations.sfc_integrations.constants import STATUS_ATTENDANCE
from mbw_sfc_integrations.sfc_integrations.helper import gen_response, exception_handel, get_value_child_doctype
from frappe.utils import nowdate

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

@frappe.whitelist(methods='GET', allow_guest=True)
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

# def exis_attendance_daily()

def update_attendance_monthly(doc, method=None):
	# Lấy ngày tháng để truy xuất dữ liệu
	month = int(nowdate().split('-')[1])
	year = int(nowdate().split('-')[0])
	attendance = doc.as_dict()

	exist_monthly_att = frappe.get_all(
            'SFC Attendance Monthly Report',
            filters={'month': month, 'year': year, 'employee': attendance['employee']},
            fields=['name']
        )
	
	employee_id = frappe.get_value('Employee', {'name': attendance['employee']}, 'user_id')
	if exist_monthly_att:
		monthly_att_doc = frappe.get_doc('SFC Attendance Monthly Report', exist_monthly_att[0]['name'])
		monthly_att_doc.work_hours_monthly += attendance['work_hours']
		
		monthly_att_doc.save(ignore_permissions=True)

	else:
		monthly_att_doc = frappe.get_doc({
			'doctype': 'SFC Attendance Monthly Report',
			'year': year,
			'month': month,
			'employee': attendance['employee'],
			'employee_id': employee_id,
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
			'number_work_shift_monthly': attendance['number_work_shift']
		})
		monthly_att_doc.insert(ignore_permissions=True)