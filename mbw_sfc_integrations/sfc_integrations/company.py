from typing import Optional

import frappe
from frappe import _, msgprint
from frappe.utils import cint, cstr
from frappe.utils.nestedset import get_root_of
import json
from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log
from mbw_sfc_integrations.sfc_integrations.apiclient import FWAPIClient
import datetime

def upload_erpnext_company(doc, method=None):

    """This hook is called when inserting new or updating existing `company`.
    """
    company= doc.as_dict()
    new_company = {}
    for key,value in company.items():
        if not isinstance(value, (datetime.date, datetime.datetime)):
            new_company[key] = value
        elif isinstance(value, datetime.date):
            new_company[key] = datetime.datetime(value.year, value.month, value.day).timestamp()
        elif isinstance(value, datetime.datetime):
            new_company[key] = value.timestamp()
    client = FWAPIClient()
    try:
        if doc.is_new() == False:
            action="Created"
            client.create_company(new_company)
        else:
            client.update_company(new_company)
            action="Updated"
        write_upload_log(status=True, fwcompany=new_company.get("name"), company=new_company,action=action)
    except Exception as e:
        write_upload_log(status=False, fwcompany=new_company.get("name"), company=new_company,action=action)        

def delete_erpnext_company(doc, method=None):

    """This hook is called when delete existing `company`.
    """
    company= doc.as_dict()
    client = FWAPIClient()
    try:
        client.delete_company({
             "name": company.name
		})
        write_upload_log(status=True, fwcompany=company.name, company=company,action="Deleted",method="mbw_sfc_integrations.sfc_integrations.company.delete_erpnext_company")
    except Exception as e:
        write_upload_log(status=False, fwcompany=e, company=company,action="Deleted",method="mbw_sfc_integrations.sfc_integrations.company.delete_erpnext_company")        
		
def write_upload_log(status: bool, fwcompany, company, action="Created",method="mbw_sfc_integrations.sfc_integrations.company.upload_erpnext_company") -> None:
	if not status:
		msg = f"Failed to {action} company to sfc" + "<br>"
		msg += _("sfc reported errors:") + " " + ", ".join(fwcompany.errors.full_messages())
		msgprint(msg, title="Note", indicator="orange")

		create_sfc_log(
			status="Error",
            request_data=company, 
            message=msg, 
            method=method,
		)
	else:
		create_sfc_log(
			status="Success",
			request_data= company,
			message=f"{action} company: {company.get('name')}, sfc user: {company.get('name')}",
			method=method,
		)