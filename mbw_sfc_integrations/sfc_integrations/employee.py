from typing import Optional

import frappe
from frappe import _, msgprint
from frappe.utils import cint, cstr
from frappe.utils.nestedset import get_root_of
from mbw_sfc_integrations.sfc_integrations.apiclient import FWAPIClient

from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log
import datetime

def upload_erpnext_employee(doc, method=None):

    """This hook is called when inserting new or updating existing `Employee`.
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
        write_upload_log(status=True,user= employee.get("user_id") if employee.get("user_id") else None, employee=new_employee,action=action)
    except Exception as e:
        write_upload_log(status=False,user= employee.get("user_id") if employee.get("user_id") else None, employee=new_employee,action=action)





def deleted_erpnext_employee(doc, method=None):

    """This hook is called when delete `Employee`.
    """
    employee = doc
    client = FWAPIClient()    
    try:
        client.delete_employee({
            "name" : employee.name
        })
        write_upload_log(status=True,user= employee.user_id if employee.user_id else None, employee=employee,action="Deleted",method="mbw_sfc_integrations.sfc_integrations.employee.deleted_erpnext_employee")
    except Exception as e:
        write_upload_log(status=False,user= employee.user_id if employee.user_id else None, employee=employee,action="Deleted",method="mbw_sfc_integrations.sfc_integrations.employee.deleted_erpnext_employee")

def write_upload_log(status: bool, user: None, employee, action="Created",method="mbw_sfc_integrations.sfc_integrations.employee.upload_erpnext_employee") -> None:
    print("")
    if not status:
        msg = _("Failed to upload employee to sfc") + "<br>"
        #     msg += _("sfc reported errors:") + " " + ", ".join(user.errors.full_messages())
        msgprint(msg, title="Note", indicator="orange")

        create_sfc_log(
            status="Error",  request_data=employee if employee else None, message=msg, method=method,
        )

    else:
        create_sfc_log(
            status="Success",
            request_data=employee if employee else None,
            message=f"{action} Employee: {employee.get('name')}, sfc user: {user}",
            method=method,
        )
