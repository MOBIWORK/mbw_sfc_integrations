from typing import Optional

import frappe
from frappe import _, msgprint
from frappe.utils import cint, cstr
from frappe.utils.nestedset import get_root_of
from mbw_sfc_integrations.sfc_integrations.apiclient import FWAPIClient

from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log, create_sfc_key
from mbw_sfc_integrations.sfc_integrations.constants import UPLOAD_ERPNEXT_EMPLOYEE, DELETED_ERPNEXT_EMPLOYEE, INSERT_ERPNEXT_EMPLOYEE
import datetime

def upload_erpnext_employee(doc, method=None):

    """This hook is called when updating existing `Employee`.
    """
    client = FWAPIClient()
    employee= doc.as_dict()
    new_employee = {}
    for key, value in employee.items():
        if not isinstance(value, (datetime.date, datetime.datetime)):
            new_employee[key] = value
        elif isinstance(value, datetime.date):
            new_employee[key] = datetime.datetime(value.year, value.month, value.day).timestamp()
        elif isinstance(value, datetime.datetime):
            new_employee[key] = value.timestamp()
    try:
        if doc.is_new() == False:
            action="Created"
            client.create_employee(new_employee)
        else:
            action="Updated"
            client.update_employee(new_employee)
        write_upload_log(status=True,user= new_employee.get("user_id") if new_employee.get("user_id") else None, employee=new_employee,action=action, method=UPLOAD_ERPNEXT_EMPLOYEE)
    except Exception as e:
        write_upload_log(status=False,user= new_employee.get("user_id") if new_employee.get("user_id") else None, employee=new_employee,action=action, method=UPLOAD_ERPNEXT_EMPLOYEE)

def insert_erpnext_employee(doc, method=None):
    doc.sfc_key = create_sfc_key()


def deleted_erpnext_employee(doc, method=None):

    """This hook is called when delete `Employee`.
    """
    employee = doc.as_dict()
    client = FWAPIClient()    
    try:
        client.delete_employee({
            "sfc_key" : employee['sfc_key']
        })
        write_upload_log(status=True,user= employee.user_id if employee.user_id else None, employee={'sfc_key': employee['sfc_key']},action="Deleted",method=DELETED_ERPNEXT_EMPLOYEE)
    except Exception as e:
        write_upload_log(status=False,user= employee.user_id if employee.user_id else None, employee={'sfc_key': employee['sfc_key']},action="Deleted",method=DELETED_ERPNEXT_EMPLOYEE)

def write_upload_log(status: bool, user: None, employee, action="Created",method=INSERT_ERPNEXT_EMPLOYEE) -> None:
    if not status:
        msg = f"Failed to {action} employee to sfc" + "<br>"
        # msg += _("sfc reported errors:") + " " + ", ".join(user.errors.full_messages())
        msgprint(msg, title="Note", indicator="orange")

        create_sfc_log(
            status="Error",  
            request_data=employee if employee else None, 
            message=msg, 
            method=method,
        )
    else:
        create_sfc_log(
            status="Success",
            request_data=employee if employee else None,
            message=f"{action} Employee: {employee.get('name')}, sfc user: {user}",
            method=method,
        )
