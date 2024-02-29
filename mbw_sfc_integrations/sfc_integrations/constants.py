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

