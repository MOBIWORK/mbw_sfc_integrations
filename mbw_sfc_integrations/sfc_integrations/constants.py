MODULE_NAME = "Sfc Integrations"
SETTING_DOCTYPE = "SFC Setting"

WEBHOOK_EVENTS = [

]

EVENT_MAPPER = {
    "shifttype_create": "mbw_sfc_integrations.sfc_integrations.shifttype.create_shift_type",
    "shifttype_update": "mbw_sfc_integrations.sfc_integrations.shifttype.update_shift_type",
    "shifttype_delete": "mbw_sfc_integrations.sfc_integrations.shifttype.delete_shift_type",

    "attendance_create": "mbw_sfc_integrations.sfc_integrations.attendance.create_attendance",
    "attendance_update": "mbw_sfc_integrations.sfc_integrations.attendance.update_attendance",

    "worksite_create": "mbw_sfc_integrations.sfc_integrations.worksite.create_worksite",
    "worksite_update": "mbw_sfc_integrations.sfc_integrations.worksite.update_worksite",
    "worksite_delete": "mbw_sfc_integrations.sfc_integrations.worksite.delete_worksite",
}


STATUS_ATTENDANCE= {
    'Present': 'Present',
    'Absent': 'Absent',
    'On Leave': 'On Leave',
    'Half Day': 'Half Day',
    'Work From Home': 'Work From Home',
}

STATUS_WORKSITE = {
    'Active': 'Active',
    'Lock': 'Lock'
}

LIMIT_WORKSITE = {
    'All employee': 'All employee',
    'Setting Employee': 'Setting Employee'
}

INSERT_ERPNEXT_EMPLOYEE = "mbw_sfc_integrations.sfc_integrations.employee.insert_erpnext_employee"
UPLOAD_ERPNEXT_EMPLOYEE = "mbw_sfc_integrations.sfc_integrations.employee.upload_erpnext_employee"
DELETED_ERPNEXT_EMPLOYEE = "mbw_sfc_integrations.sfc_integrations.employee.deleted_erpnext_employee"

INSERT_ERPNEXT_DEPARTMENT = "mbw_sfc_integrations.sfc_integrations.department.insert_erpnext_employee"
UPLOAD_ERPNEXT_DEPARTMENT = "mbw_sfc_integrations.sfc_integrations.department.upload_erpnext_department"
DELETED_ERPNEXT_DEPARTMENT = "mbw_sfc_integrations.sfc_integrations.department.delete_erpnext_department"

INSERT_ERPNEXT_COMPANY = "mbw_sfc_integrations.sfc_integrations.company.insert_erpnext_employee"
UPLOAD_ERPNEXT_COMPANY = "mbw_sfc_integrations.sfc_integrations.company.upload_erpnext_company"
DELETED_ERPNEXT_COMPANY = "mbw_sfc_integrations.sfc_integrations.company.delete_erpnext_company"