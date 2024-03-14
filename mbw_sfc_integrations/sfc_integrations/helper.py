import frappe
from bs4 import BeautifulSoup
from frappe.utils import cstr

# return definition
def gen_response(status, message, result=[]):
    frappe.response["http_status_code"] = status
    if status == 500:
        frappe.response["message"] = BeautifulSoup(
            str(message), features="lxml").get_text()
    else:
        frappe.response["message"] = message
    frappe.response["result"] = result

def exception_handel(e):
    frappe.log_error(title="DMS Mobile App Error",
                     message=frappe.get_traceback())
    return gen_response(406, cstr(e))


# Lấy ra các field của doctype con
def get_value_child_doctype(master_doctype, master_name, name_field):
	if not master_name:
		return
	from frappe.model import child_table_fields, default_fields

	filed_master = frappe.get_doc(master_doctype, master_name)

	field_child = []
	for i, child in enumerate(filed_master.get(name_field)):
		child = child.as_dict()

        # Xóa các trường không cần thiết
		for fieldname in default_fields + child_table_fields:
			if fieldname in child:
				del child[fieldname]

		field_child.append(child)

	return field_child