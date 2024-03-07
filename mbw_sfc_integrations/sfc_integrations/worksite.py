import frappe
from frappe import _
from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log
from mbw_sfc_integrations.sfc_integrations.validators import validate_not_none, validate_choice
from mbw_sfc_integrations.sfc_integrations.constants import STATUS_WORKSITE, LIMIT_WORKSITE 

def create_worksite(payload, request_id=None):
	try:
		# Thiết lập người dùng hiện tại và request_id (nếu có)
		frappe.set_user("Administrator")
		frappe.flags.request_id = request_id

		worksite = create_worksite_from_payload(payload)
		worksite.insert()

	except Exception as e:
		create_sfc_log(status="Error", exception=e, rollback=True)
	else:
		create_sfc_log(status="Success")

def create_worksite_from_payload(payload):
    # Xử lý dữ liệu từ payload và tạo worksite mới
    worksite = frappe.new_doc("SFC Worksite")

    worksite.name_address = validate_not_none(payload.get('name_address'))
    worksite.address = validate_not_none(payload.get('address'))
    worksite.status = validate_choice(STATUS_WORKSITE)(payload.get('status', 'Active'))
    worksite.is_limited = validate_choice(LIMIT_WORKSITE)(payload.get('is_limited', 'Setting Employee'))
    worksite.radius = payload.get('radius')
    worksite.map = payload.get('map')
    worksite.sfc_key = validate_not_none(payload.get('sfc_key'))
    employees = payload.get('employees')
    if employees:
        for em_data in employees:
            worksite.append('employees', {
                'employee_id': validate_not_none(em_data.get('employee_id')),
                'employee_email': em_data.get('employee_email')
            })
	
    ip_intermediate = payload.get('ip_intermediate')
    if ip_intermediate:
        for ip_data in ip_intermediate:
            worksite.append('mac', {
				'mac_name': validate_not_none(ip_data.get('mac_name')),
				'mac_address': validate_not_none(ip_data.get('mac_address'))
            })
		
    wifi_intermediate = payload.get('wifi_intermediate')
    if wifi_intermediate:
        for wifi_data in wifi_intermediate:
            worksite.append('wifi', {
				'wifi_name': validate_not_none(wifi_data.get('wifi_name')),
				'wifi_address': validate_not_none(wifi_data.get('wifi_address'))
            })

    return worksite

def update_worksite(payload, request_id=None):
    try:
        # Thiết lập người dùng hiện tại và request_id (nếu có)
        frappe.set_user("Administrator")
        frappe.flags.request_id = request_id

        # Lấy tên Worksites từ payload
        sfc_key = validate_not_none(payload.get("sfc_key"))

        # Kiểm tra nếu Worksites tồn tại
        if frappe.db.exists("SFC Worksite", {"sfc_key":sfc_key}):
            worksite = frappe.get_doc("SFC Worksite", {"sfc_key":sfc_key})
            # Cập nhật các trường dữ liệu mới từ payload
            for field in ['name_address', 'address', 'status', 'radius', 'map', 'is_limited']:
                value = payload.get(field)
                if value is not None:
                    setattr(worksite, field, value)

            # Cập nhật danh sách nhân viên
            update_employee_data(worksite, payload.get('employees'))

            # Cập nhật danh sách IP intermediate
            update_ip_data(worksite, payload.get('ip_intermediate'))

            # Cập nhật danh sách wifi intermediate
            update_wifi_data(worksite, payload.get('wifi_intermediate'))

            worksite.save()
        else:
            frappe.throw(("Worksite không tồn tại!"))

        create_sfc_log(status="Success")

    except Exception as e:
        create_sfc_log(status="Error", exception=e, rollback=True)

def update_employee_data(worksite, employees):
    if not employees:
        return

    for em_data in employees:
        employee_id = validate_not_none(em_data.get('employee_id'))
        existing_em = next((i for i in worksite.employees if i.employee_id == employee_id), None)
        if existing_em:
            employee_email = em_data.get('employee_email')
            if employee_email:
                existing_em.employee_email = employee_email
        else:
            worksite.append('employees', {
                'employee_id': employee_id,
                'employee_email': em_data.get('employee_email')
            })

def update_ip_data(worksite, ip_intermediate):
    if not ip_intermediate:
        return

    for ip_data in ip_intermediate:
        mac_name = validate_not_none(ip_data.get('mac_name'))
        existing_ip = next((i for i in worksite.mac if i.mac_name == mac_name), None)
        if existing_ip:
            mac_address = ip_data.get('mac_address')
            if mac_address:
                existing_ip.mac_address = mac_address
        else:
            worksite.append('mac', {
                'mac_name': mac_name,
                'mac_address': validate_not_none(ip_data.get('mac_address'))
            })

def update_wifi_data(worksite, wifi_intermediate):
    if not wifi_intermediate:
        return

    for wifi_data in wifi_intermediate:
        wifi_name = validate_not_none(wifi_data.get('wifi_name'))
        existing_wifi = next((i for i in worksite.wifi if i.wifi_name == wifi_name), None)
        if existing_wifi:
            wifi_address = wifi_data.get('wifi_address')
            if wifi_address:
                existing_wifi.wifi_address = wifi_address
        else:
            worksite.append('wifi', {
                'wifi_name': wifi_name,
                'wifi_address': validate_not_none(wifi_data.get('wifi_address'))
            })


def delete_worksite(payload, request_id=None):
	try:
		# Thiết lập người dùng hiện tại và request_id (nếu có)
		frappe.set_user("Administrator")
		frappe.flags.request_id = request_id

		# Lấy tên Worksite cần xóa từ payload
		sfc_key = validate_not_none(payload.get("sfc_key"))
          
		# Kiểm tra Worksite có tồn tại hay không

		if frappe.db.exists("SFC Worksite", {"sfc_key":sfc_key}):
			frappe.db.delete("SFC Worksite", {'sfc_key': sfc_key})
		else:
			frappe.throw(("Worksite không tồn tại!"))

	except Exception as e:
		create_sfc_log(status="Error", exception=e, rollback=True)
	else:
		create_sfc_log(status="Success")