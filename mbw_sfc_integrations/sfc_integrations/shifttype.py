import frappe
from frappe import _
from frappe.utils import get_time
from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log
from mbw_sfc_integrations.sfc_integrations.validators import validate_not_none

def create_shift_type(payload, request_id=None):
	try:
		# Thiết lập người dùng hiện tại và request_id (nếu có)
		frappe.set_user("Administrator")
		frappe.flags.request_id = request_id

		shift_type = create_shift_type_from_payload(payload)
		shift_type.insert()

	except Exception as e:
		create_sfc_log(status="Error", exception=e, rollback=True)
		return "ok"
	else:
		create_sfc_log(status="Success")

def create_shift_type_from_payload(payload):
    # Xử lý dữ liệu từ payload và tạo Shift Type mới
    shift_type = frappe.new_doc("Shift Type")

    shift_type.name = validate_not_none(payload.get("name"))
    shift_type.start_time = validate_not_none(get_time(payload.get("start_time")))
    shift_type.end_time = validate_not_none(get_time(payload.get("end_time")))

    return shift_type

def update_shift_type(payload, request_id=None):
	try:
		# Thiết lập người dùng hiện tại và request_id (nếu có)
		frappe.set_user("Administrator")
		frappe.flags.request_id = request_id

        # Lấy Shift Type cần cập nhật từ cơ sở dữ liệu
		shift_type_name = payload.get("name")
		if frappe.db.exists("Shift Type", shift_type_name, cache=True):
			shift_type = frappe.get_doc("Shift Type", shift_type_name)

			# Cập nhật các trường dữ liệu mới từ payload
			for field, value in dict(payload).items():
				setattr(shift_type, field, value)
			shift_type.save()
		else:
			frappe.throw(("Shift type không tồn tại!"))

	except Exception as e:
		create_sfc_log(status="Error", exception=e, rollback=True)
	else:
		create_sfc_log(status="Success")

def delete_shift_type(payload, request_id=None):
	try:
		# Thiết lập người dùng hiện tại và request_id (nếu có)
		frappe.set_user("Administrator")
		frappe.flags.request_id = request_id

		# Lấy tên Shift Type cần xóa từ payload
		shift_type_name = payload.get("name")

		#  Kiểm tra shift type có tồn tại hay không
		if frappe.db.exists("Shift Type", shift_type_name, cache=True):
			frappe.delete_doc('Shift Type', shift_type_name)
		else:
			frappe.throw(("Shift type không tồn tại!"))

	except Exception as e:
		create_sfc_log(status="Error", exception=e, rollback=True)
	else:
		create_sfc_log(status="Success")