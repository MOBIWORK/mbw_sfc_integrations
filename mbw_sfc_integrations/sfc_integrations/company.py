from typing import Optional

import frappe
from frappe import _, msgprint
from frappe.utils import cint, cstr
from frappe.utils.nestedset import get_root_of
import json
from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log, create_sfc_key
from mbw_sfc_integrations.sfc_integrations.apiclient import FWAPIClient
from mbw_sfc_integrations.sfc_integrations.constants import UPLOAD_ERPNEXT_COMPANY, DELETED_ERPNEXT_COMPANY, INSERT_ERPNEXT_COMPANY
import datetime

def upload_erpnext_company(doc, method=None):

    """This hook is called when updating existing `company`.
    """
    company= doc.as_dict()
    new_company = {}
    action = "Updated"
    for key,value in company.items():
        if not isinstance(value, (datetime.date, datetime.datetime)):
            new_company[key] = value
        elif isinstance(value, datetime.date):
            new_company[key] = datetime.datetime(value.year, value.month, value.day).timestamp()
        elif isinstance(value, datetime.datetime):
            new_company[key] = value.timestamp()
    client = FWAPIClient()
    try:
        if doc.is_new() == None:
            client.update_company(new_company)
            action=action
            write_upload_log(status=True, fwcompany=new_company.get("name"), company=new_company,action=action,method=UPLOAD_ERPNEXT_COMPANY)
    except Exception as e:
        write_upload_log(status=False, fwcompany=new_company.get("name"), company=new_company,action=action,method=UPLOAD_ERPNEXT_COMPANY)       

def insert_erpnext_company(doc, method=None):

    """This hook is called when inserting new or `company`.
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
        new_sfc_key = create_sfc_key()
        new_company['sfc_key'] = new_sfc_key
        doc.sfc_key = new_sfc_key
        action="Created"
        client.create_company(new_company)
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
        write_upload_log(status=True, fwcompany=company.name, company=company,action="Deleted",method=DELETED_ERPNEXT_COMPANY)
    except Exception as e:
        write_upload_log(status=False, fwcompany=e, company=company,action="Deleted",method=DELETED_ERPNEXT_COMPANY)        
		
def write_upload_log(status: bool, fwcompany, company, action="Created",method=INSERT_ERPNEXT_COMPANY) -> None:
	if not status:
		msg = f"Failed to {action} company to sfc" + "<br>"
		# msg += _("sfc reported errors:") + " " + ", ".join(fwcompany.errors.full_messages())
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
			message=f"{action} company: {company.get('name')}",
			method=method,
		)