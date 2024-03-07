import base64
from typing import Any, Dict, List, Optional, Tuple

import frappe
import requests
from frappe import _
from frappe.utils import cint, cstr, get_datetime
from pytz import timezone

from mbw_sfc_integrations.sfc_integrations.utils import create_sfc_log

from mbw_sfc_integrations.sfc_integrations.constants import (
	MODULE_NAME,
	SETTING_DOCTYPE,
)

JsonDict = Dict[str, Any]

class FWAPIClient:
	"""Wrapper around FW REST API

	API docs: 
	"""

	def __init__(
		self, url: Optional[str] = None, access_token: Optional[str] = None,
	):
		self.settings = frappe.get_doc(SETTING_DOCTYPE)
		self.base_url = self.settings.sfc_site or f"https://65d4044a522627d50109c0b1.mockapi.io/api/v1"
		self.access_token = self.settings.jwttoken
		self.orgid = self.settings.orgid
		self.__initialize_auth()

	def __initialize_auth(self):
		"""Initialize and setup authentication details"""
		#if not self.access_token:
		#	self.settings.renew_tokens()
		#	self.access_token = self.settings.get_password("access_token")

		#self._auth_headers = {"Authorization": f"Bearer {self.access_token}"}
		self._auth_headers = {"X-SFC-JWT": self.access_token, "X-SFC-ORGID":self.orgid}

	def request(
		self,
		endpoint: str,
		method: str = "POST",
		headers: Optional[JsonDict] = None,
		body: Optional[JsonDict] = None,
		params: Optional[JsonDict] = None,
		files: Optional[JsonDict] = None,
		log_error=True,
	) -> Tuple[JsonDict, bool]:
	

		if headers is None:
			headers = {}

		headers.update(self._auth_headers)

		url = self.base_url + endpoint

		try:
			response = requests.request(
				url=url, method=method, headers=headers, json=body, params=params, files=files
			)
			# unicommerce gives useful info in response text, show it in error logs
			#response.reason = cstr(response.reason) + cstr(response.text)
			response.raise_for_status()
		except Exception:
			if log_error:
				create_sfc_log(status="Error", make_new=True)
			return None, False

		if method == "GET" and "application/json" not in response.headers.get("content-type"):
			return response.content, True

		data = frappe._dict(response.json())
		status = data.successful if data.successful is not None else True

		if not status:
			req = response.request
			url = f"URL: {req.url}"
			body = f"body:  {req.body.decode('utf-8')}"
			request_data = "\n\n".join([url, body])
			message = ", ".join(cstr(error["message"]) for error in data.errors)
			create_sfc_log(
				status="Error", response_data=data, request_data=request_data, message=message, make_new=True
			)

		return data, status
	
	# Department
	def create_department(self, department_dict: JsonDict, update=False) -> Tuple[JsonDict, bool]:
		"""Create/update item on unicommerce.

		ref: https://documentation.unicommerce.com/docs/createoredit-itemtype.html
		"""
		endpoint = "/department"
		return self.request(endpoint=endpoint, body=department_dict)
	
	def update_department(self, department_dict: JsonDict, update=False) -> Tuple[JsonDict, bool]:
		"""Create/update item on unicommerce.

		ref: https://documentation.unicommerce.com/docs/createoredit-itemtype.html
		"""
		endpoint = "/department"
		return self.request(endpoint=endpoint, body=department_dict,method="PUT")
	
	def delete_department(self, department_dict: JsonDict, update=False) -> Tuple[JsonDict, bool]:
		"""Create/update item on unicommerce.

		ref: https://documentation.unicommerce.com/docs/createoredit-itemtype.html
		"""

		endpoint = "/department"
		return self.request(endpoint=endpoint, body=department_dict,method="DELETE")
	
	# Company
	def create_company(self, company_dict: JsonDict, update=False) -> Tuple[JsonDict, bool]:
		"""Create/update item on unicommerce.

		ref: https://documentation.unicommerce.com/docs/createoredit-itemtype.html
		"""
		endpoint = "/company"
		return self.request(endpoint=endpoint, body=company_dict)
	
	def update_company(self, company_dict: JsonDict, update=False) -> Tuple[JsonDict, bool]:
		"""Create/update item on unicommerce.

		ref: https://documentation.unicommerce.com/docs/createoredit-itemtype.html
		"""

		endpoint = "/company"
		return self.request(endpoint=endpoint, body=company_dict,method="PUT")
	
	def delete_company(self, company_dict: JsonDict, update=False) -> Tuple[JsonDict, bool]:
		"""Create/update item on unicommerce.

		ref: https://documentation.unicommerce.com/docs/createoredit-itemtype.html
		"""

		endpoint = "/company"
		return self.request(endpoint=endpoint, body=company_dict,method="DELETE")
	
	# Employee 
	def create_employee(self, employee_dict: JsonDict, update=False) -> Tuple[JsonDict, bool]:
		"""Create/update item on unicommerce.

		ref: https://documentation.unicommerce.com/docs/createoredit-itemtype.html
		"""

		endpoint = "/employee"
		return self.request(endpoint=endpoint, body=employee_dict)
	
	def update_employee(self, employee_dict: JsonDict, update=False) -> Tuple[JsonDict, bool]:
		"""Create/update item on unicommerce.

		ref: https://documentation.unicommerce.com/docs/createoredit-itemtype.html
		"""
		endpoint = "/employee"
		return self.request(endpoint=endpoint, body=employee_dict,method="PUT")
	
	def delete_employee(self, employee_dict: JsonDict, update=False) -> Tuple[JsonDict, bool]:
		"""Create/update item on unicommerce.

		ref: https://documentation.unicommerce.com/docs/createoredit-itemtype.html
		"""

		endpoint = "/employee"
		return self.request(endpoint=endpoint, body=employee_dict,method="DELETE")
	