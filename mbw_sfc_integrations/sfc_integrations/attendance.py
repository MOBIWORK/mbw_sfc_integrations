import frappe
from frappe import _
from frappe.utils import get_time
from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log
from mbw_sfc_integrations.sfc_integrations.validators import validate_date, validate_choice, validate_not_none
from mbw_sfc_integrations.sfc_integrations.constants import STATUS_ATTENDANCE
from mbw_sfc_integrations.sfc_integrations.helper import gen_response, exception_handel, get_value_child_doctype

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
