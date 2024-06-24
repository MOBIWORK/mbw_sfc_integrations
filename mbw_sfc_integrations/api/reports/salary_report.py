import frappe
from datetime import (datetime,timedelta)
from frappe import _
from mbw_sfc_integrations.api.validators import (validate_filter)
from mbw_sfc_integrations.api.common import (gen_response,exception_handle)
import pydash
@frappe.whitelist(methods="GET")
def salary_report(**body):
    try:
        body= dict(body)
        month = int(validate_filter(type_check="require",value=body.get("month")))
        year = int(validate_filter(type_check="require",value=body.get("year")))
        department = body.get("department")
        employee = body.get("employee")
        page_size =  int(body.get('page_size', 20))
        page_number = int(body.get('page_number') ) if body.get('page_number') and int(body.get('page_number')) > 0 else 1
        start_date = datetime(year,month,1,0,0,0)
        end_date = datetime(year,month +1 ,1,0,0,0) - timedelta(seconds=1)

        filters = {
            "start_date": [">=",start_date],
            "end_date": ["<=",end_date]
        }   

        filter_att = {"month": month,"year": year}

        if employee:
            filters.update({"employee":employee})
           
        if employee:
            filters.update({"department":department})
            filter_att.update({"department":department})
        fieldsget = ["name","employee","employee_name","department","designation","gross_pay","net_pay","grade"]
        list_salary = frappe.db.get_list(doctype="Salary Slip",filters=filters,fields= fieldsget,start=(page_number-1)*page_size,page_length=page_size)
        employee_list = pydash.map_(list_salary,lambda x: x.employee)
        filter_att.update({"employee":["in",employee_list]})
        fields_get = [ "broken_shift_hours_monthly","straight_shift_hours_monthly","number_work_explain_absence_monthly","number_of_holiday_monthly","work_hours_straight_holidays_monthly","work_hours_broken_holidays_monthly"]
        fields_get_goldsf = [ "ngay_cong_chuan","cong_bu","phu_cap_xa_nha"]
        list_attendance  = frappe.db.get_list("SFC Attendance Monthly Report",filters = filter_att,fields=fields_get)
        list_attendance_golfsf  = frappe.db.get_list("GoldSF HR Data",filters = filter_att,fields=fields_get_goldsf)
        total = len(frappe.db.get_list(doctype="Salary Slip",filters=filters,pluck='name'))
        for salary in list_salary:
            doc_salary = frappe.get_doc("Salary Slip",salary.get("name")).as_dict()
            earnings = doc_salary.earnings
            deductions = doc_salary.deductions
            attendance_employee = pydash.find(list_attendance,lambda x:x.employee == salary.employee)
            attendance_employee_gold = pydash.find(list_attendance_golfsf,lambda x:x.employee == salary.employee)
            print("employee",salary.employee)
            if attendance_employee : 
                for key,value in attendance_employee.items():
                    salary.update({key: value})
            if attendance_employee_gold : 
                for key,value in attendance_employee_gold.items():
                    salary.update({key: value})
            if len(earnings) > 0 :
                for earning in earnings:
                    salary.update({earning.abbr: earning.year_to_date})
            if len(deductions) > 0 :
                for deduction in deductions:
                    salary.update({deduction.abbr: deduction.year_to_date})
            NCCG = salary.NCCG if salary.NCCG else 0
            number_work_explain_absence_monthly = salary.number_work_explain_absence_monthly if salary.number_work_explain_absence_monthly else 0
            number_of_holiday_monthly = salary.number_of_holiday_monthly if salary.number_of_holiday_monthly else 0
            cong_bu = salary.cong_bu if salary.cong_bu else 0
            work_hours_broken_holidays_monthly = salary.work_hours_broken_holidays_monthly if salary.work_hours_broken_holidays_monthly else 0
            NCCTL = salary.NCCTL if salary.NCCTL else 0
            NCCGL = salary.NCCGL if salary.NCCGL else 0
            
            tong_ngay_cong=  NCCG + number_work_explain_absence_monthly + number_of_holiday_monthly + cong_bu + work_hours_broken_holidays_monthly + NCCTL + NCCGL
            salary.update({"tong_cong":tong_ngay_cong})
        return gen_response(200,"",{
            "data": list_salary,
            "total":total
        })
    except Exception as e:
        exception_handle(e)