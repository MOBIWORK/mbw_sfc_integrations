import frappe
from frappe import _
from frappe.utils import get_time
from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log
from mbw_sfc_integrations.sfc_integrations.validators import validate_date, validate_choice
from mbw_sfc_integrations.sfc_integrations.constants import STATUS_ATTENDANCE

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

    return attendance

def update_attendance(payload, request_id=None):
	try:
		# Thiết lập người dùng hiện tại và request_id (nếu có)
		frappe.set_user("Administrator")
		frappe.flags.request_id = request_id

        # Lấy Attendance cần cập nhật từ cơ sở dữ liệu
		attendance_name = payload.get("name")
		if frappe.db.exists("Attendance", attendance_name, cache=True):
			attendance_name = frappe.get_doc("Attendance", attendance_name)

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