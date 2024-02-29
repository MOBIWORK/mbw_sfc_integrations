
from typing import List

import frappe
from frappe import _, _dict

from mbw_sfc_integrations.sfc_integrations.doctype.sfc_integration_log.sfc_integration_log import create_log


from mbw_sfc_integrations.sfc_integrations.constants import (
	MODULE_NAME,
	SETTING_DOCTYPE,
)

api_url = "https://sfc.mbw.com/v1/"

def create_sfc_log(**kwargs):
	return create_log(module_def=MODULE_NAME, **kwargs)

