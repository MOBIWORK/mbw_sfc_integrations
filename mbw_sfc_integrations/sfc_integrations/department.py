from typing import Optional

import frappe
from frappe import _, msgprint
from frappe.utils import cint, cstr
from frappe.utils.nestedset import get_root_of

from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log, create_sfc_key
from mbw_sfc_integrations.sfc_integrations.apiclient import FWAPIClient
from mbw_sfc_integrations.sfc_integrations.constants import UPLOAD_ERPNEXT_DEPARTMENT, DELETED_ERPNEXT_DEPARTMENT, INSERT_ERPNEXT_DEPARTMENT
import datetime

#after create
def upload_erpnext_department(doc, method=None):
    """This hook is called when updating existing `Department`.
    """
    department= doc.as_dict()
    new_department = {}
    action="Updated"
    for key,value in department.items():
        if not isinstance(value, (datetime.date, datetime.datetime)):
            new_department[key] = value
        elif isinstance(value, datetime.date):
            new_department[key] = datetime.datetime(value.year, value.month, value.day).timestamp()
        elif isinstance(value, datetime.datetime):
            new_department[key] = value.timestamp()
    client = FWAPIClient()
    company = frappe.db.get_value("Company",department.company,["company_name","company_code"], as_dict=1)
    new_department["company_code"] = company.get("company_code")
    
    try:
        if doc.is_new() == None:
            action=action
            client.update_department(new_department)
        write_upload_log(status=True, fwdepartment=new_department.get("name"), department=new_department,action=action, method=UPLOAD_ERPNEXT_DEPARTMENT)
    except Exception as e:
        write_upload_log(status=False, fwdepartment=new_department.get("name"), department=new_department,action=action, method=UPLOAD_ERPNEXT_DEPARTMENT)

def insert_erpnext_department(doc, method=None):
    """This hook is called when inserting new `Department`.
    """
    department= doc.as_dict()
    new_department = {}
    for key,value in department.items():
        if not isinstance(value, (datetime.date, datetime.datetime)):
            new_department[key] = value
        elif isinstance(value, datetime.date):
            new_department[key] = datetime.datetime(value.year, value.month, value.day).timestamp()
        elif isinstance(value, datetime.datetime):
            new_department[key] = value.timestamp()
    client = FWAPIClient()
    company = frappe.db.get_value("Company",department.company,["company_name","company_code"], as_dict=1)
    new_department["company_code"] = company.get("company_code")

    try:
        new_sfc_key = create_sfc_key()
        new_department['sfc_key'] = new_sfc_key
        doc.sfc_key = new_sfc_key
        action="Created"
        client.create_department(new_department)
        
        write_upload_log(status=True, fwdepartment=new_department.get("name"), department=new_department,action=action)
    except Exception as e:
        write_upload_log(status=False, fwdepartment=new_department.get("name"), department=new_department,action=action)

#after delete
def delete_erpnext_department(doc, method=None):

    """This hook is called when delete `Department`.
    """
    department = doc.as_dict()
    client = FWAPIClient()    
    try:
        client.delete_department({
            "name": department.name
        })
        write_upload_log(status=True, fwdepartment=department.name, department=department,action="Deleted",method=DELETED_ERPNEXT_DEPARTMENT)
    except Exception as e:
        write_upload_log(status=False, fwdepartment=department.name, department=department,action="Deleted",method=DELETED_ERPNEXT_DEPARTMENT)

def write_upload_log(status: bool, fwdepartment, department, action="Created",method=INSERT_ERPNEXT_DEPARTMENT) -> None:
	if not status:
		msg = _("Failed to upload department to sfc") + "<br>"
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