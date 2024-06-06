import frappe
from datetime import (datetime,timedelta)
from frappe import _
from mbw_sfc_integrations.api.validators import (validate_filter)
from mbw_sfc_integrations.api.common import (gen_response,exception_handle)
@frappe.whitelist(method="GET")
def salary_report(**body):
    try:
        month = validate_filter(type_check="require",value=body.get("month"))
        year = validate_filter(type_check="require",value=body.get("year"))
        department = body.get("department")
        employee = body.get("department")
        page_size =  int(body.get('page_size', 20))
        page_number = int(body.get('page_number') ) if body.get('page_number') and int(body.get('page_number')) > 0 else 1
        start_date = datetime(year,month,1,0,0,0)
        end_date = datetime(year,month +1 ,1,0,0,0) - timedelta(seconds=1)

        filters = {
            "start_date": [">=",start_date],
            "end_date": ["<=",end_date]
        }

        if employee:
            filters.update({"employee":employee})
        if employee:
            filters.update({"department":department})
        fieldsget = ["name","employee","employee_name","department","designation","gross_pay","net_pay","grade"]
        list_salary = frappe.db.get_list(doctype="Salary Slip",filter=filters,fields= fieldsget,start=(page_number-1)*page_size,page_length=page_size, pluck='name')
        for salary in list_salary:
            doc_salary = frappe.get_doc("Salary Slip",salary.get("name")).as_dict()
            earnings = doc_salary.earnings
            deductions = doc_salary.deductions
            if len(earnings) > 0 :
                for earning in earnings:
                    list_salary.update({earning.salary_component: earning.year_to_date})
            if len(deductions) > 0 :
                for deduction in deductions:
                    list_salary.update({deduction.salary_component: deduction.year_to_date})
        return gen_response(200,"",list_salary)
    except Exception as e:
        exception_handle(e)