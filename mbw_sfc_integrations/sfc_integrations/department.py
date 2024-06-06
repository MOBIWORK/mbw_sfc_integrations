from typing import Optional

import frappe
from frappe import _, msgprint
from frappe.utils import cint, cstr
from frappe.utils.nestedset import get_root_of

from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log, create_sfc_key
from mbw_sfc_integrations.sfc_integrations.apiclient import FWAPIClient
from mbw_sfc_integrations.sfc_integrations.constants import UPLOAD_ERPNEXT_DEPARTMENT, DELETED_ERPNEXT_DEPARTMENT, INSERT_ERPNEXT_DEPARTMENT
import datetime

def convert_datetime_to_timestamp(obj):
    """
    Chuyển đổi datetime thành timestamp.
    """
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.timestamp()
    return obj

def convert_dict_datetime_to_timestamp(data):
    """
    Chuyển đổi tất cả các trường datetime trong dict thành timestamp.
    """
    return {
        key: convert_datetime_to_timestamp(value)
        if isinstance(value, (datetime.date, datetime.datetime))
        else value
        for key, value in data.items()
    }

# after create
def upload_erpnext_department(doc, method=None):
    """This hook is called when updating existing `Department`.
    """
    department= doc.as_dict()
    new_department = convert_dict_datetime_to_timestamp(department)
    
    for approver_type in ['shift_request_approver', 'leave_approvers', 'expense_approvers']:
        if approver_type in new_department:
            for approver in new_department[approver_type]:
                approver['creation'] = convert_datetime_to_timestamp(approver.get('creation'))
                approver['modified'] = convert_datetime_to_timestamp(approver.get('modified'))
    client = FWAPIClient()
    company = frappe.db.get_value("Company",department.company,["company_name","company_code"], as_dict=1)
    new_department["company_code"] = company.get("company_code")
    
    try:
        if doc.is_new() == False:
            action="Created"
            client.create_department(new_department)
        else:
            action="Updated"
            client.update_department(new_department)
        write_upload_log(status=True, fwdepartment=new_department.get("name"), department=new_department,action=action, method=UPLOAD_ERPNEXT_DEPARTMENT)
    except Exception as e:
        write_upload_log(status=False, fwdepartment=new_department.get("name"), department=new_department,action=action, method=UPLOAD_ERPNEXT_DEPARTMENT)

def insert_erpnext_department(doc, method=None):
    doc.sfc_key = create_sfc_key()

#after delete
def delete_erpnext_department(doc, method=None):

    """This hook is called when delete `Department`.
    """
    department = doc.as_dict()
    client = FWAPIClient()    
    try:
        client.delete_department({
            "sfc_key": department['sfc_key']
        })
        write_upload_log(status=True, fwdepartment=department.name, department={'sfc_key': department['sfc_key']},action="Deleted",method=DELETED_ERPNEXT_DEPARTMENT)
    except Exception as e:
        write_upload_log(status=False, fwdepartment=department.name, department={'sfc_key': department['sfc_key']},action="Deleted",method=DELETED_ERPNEXT_DEPARTMENT)

def write_upload_log(status: bool, fwdepartment, department, action="Created",method=INSERT_ERPNEXT_DEPARTMENT) -> None:
	if not status:
		msg = f"Failed to {action} department to sfc" + "<br>"
		# msg += _("sfc reported errors:") + " " + ", ".join(fwdepartment.errors.full_messages())
		msgprint(msg, title="Note", indicator="orange")

		create_sfc_log(
			status="Error", 
            request_data=department, 
            message=msg, 
            method=method,
		)
	else:
		create_sfc_log(
			status="Success",
			request_data=department,
			message=f"{action} department: {department.get('name')}",
			method=method,
		)