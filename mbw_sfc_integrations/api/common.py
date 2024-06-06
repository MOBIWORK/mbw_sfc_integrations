import json
import io
import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.utils import cstr
from datetime import datetime, timezone, timedelta
import base64
from frappe.core.doctype.file.utils import delete_file
from frappe.utils.file_manager import save_file

from mbw_dms.api.file import create_my_minio
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from frappe.desk.query_report import get_reference_report 
from datetime import datetime
import pytz
import pydash

BASE_URL = frappe.utils.get_request_site_address()

def time_now_utc():
    now_utc = datetime.now(pytz.utc)
    hcm_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
    time_now = now_utc.astimezone(hcm_timezone)
    return time_now

def convert_utc_time(timestamp:float):
    dt = datetime.fromtimestamp(timestamp)

    # Xác định múi giờ của 'Asia/Ho_Chi_Minh'
    hcm_timezone = pytz.timezone('Asia/Ho_Chi_Minh')  # UTC+7 cho múi giờ 'Asia/Ho_Chi_Minh'

    # Áp dụng múi giờ 'Asia/Ho_Chi_Minh' cho đối tượng datetime
    dt_hcm = dt.replace(tzinfo=hcm_timezone)

    return dt_hcm

def this_week() :
    today = datetime.now()
    # Lấy số tuần trong năm
    week_number = int(today.strftime("%U")) +1
    week  = week_number % 5 if week_number % 5 != 0 or week_number % 5 != 1 else 1
    return week


# return definition
def gen_response(status, message, result=[]):
    frappe.response["http_status_code"] = status
    if status == 500:
        frappe.response["message"] = BeautifulSoup(
            str(message), features="lxml").get_text()
    else:
        frappe.response["message"] = message
    frappe.response["result"] = result

# export employee key
def generate_key(user):
    user_details = frappe.get_doc("User", user)
    api_secret = api_key = ""
    if not user_details.api_key and not user_details.api_secret:
        api_secret = frappe.generate_hash(length=15)
        # if api key is not set generate api key
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key
        user_details.api_secret = api_secret
        user_details.save(ignore_permissions=True)
    else:
        api_secret = user_details.get_password("api_secret")
        api_key = user_details.get("api_key")
    return {"api_secret": api_secret, "api_key": api_key}


def get_employee_by_user(user, fields=["name"]):
    if isinstance(fields, str):
        fields = [fields]
    emp_data = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        fields,
        as_dict=1,
    )
    return emp_data


def get_language():
    lang_ = frappe.local.request.headers.get("Language")
    lang = "vi" if not lang_ else lang_

    return lang

def exception_handle(e):
    frappe.log_error(title="DMS Mobile App Error",
                     message=frappe.get_traceback())
    print(frappe.response)
    return gen_response(406, cstr(e),{})

def routers_name_of_customer(router=False, thisWeek = False,view_mode='list',more_filters=False):
    queryFilters = {"is_deleted": 0,"status":"Active"}
    user_id = get_user_id()
    if user_id.name != "Administrator":
        employee = get_employee_by_user(user = user_id.email)
        if not employee:
            return gen_response("404", _("Employee not registered"))
        queryFilters['employee'] = employee.name

    if router:
        queryFilters['channel_code'] = ["in",router]
   
    # lay danh sach theo ngay
    if thisWeek or view_mode=="map":
        from mbw_dms.api.common import weekday
        today= datetime.now()
        thu_trong_tuan, tuan_trong_thang = weekday(today)
        queryFilters.update({"travel_date": ["between",["Không giới hạn",thu_trong_tuan]]})
        queryFilters.update({"frequency": ["like",tuan_trong_thang]})  
    if more_filters:
        queryFilters.update(more_filters)
    list_router = frappe.db.get_all('DMS Router',filters=queryFilters, pluck='name',distinct=True)
    return list_router

def customers_code_router(router=False,routersName=[],thisWeek = False,view_mode='list'):
    
    list_customer = []
    for router_name in routersName:
        detail_router = frappe.get_doc("DMS Router",{"name":router_name}).as_dict()
        customer = detail_router.get('customers')
        if view_mode == "map" or (router and not thisWeek):
            from mbw_dms.api.common import weekday
            today= datetime.now()
            thu_trong_tuan, tuan_trong_thang = weekday(today)
            customer = pydash.filter_(detail_router.get('customers'),lambda value: (value.frequency.find(str(int(tuan_trong_thang))) != -1))
        list_customer += customer
    list_customer_name = []
    for customer in list_customer:
        list_customer_name.append(customer.get('customer_code'))   
    return list_customer_name 


def get_user_id():
    headers = frappe.local.request.headers.get("Authorization")
    usrPass = headers.split(" ")[1]
    str_b64Val = base64.b64decode(usrPass).decode('utf-8')
    list_key = str_b64Val.split(':')
    api_key = list_key[0]
    user_id = frappe.db.get_value('User', {"api_key": api_key},['name','email'],as_dict=1)
    return user_id

def get_employee_id():
    try:
        user_id = get_user_id()
        return get_employee_by_user(user_id.get('name')).get('name')
    except:
        return ""

def get_employee_info():
    try:
        user_id = get_user_id()
        return get_employee_by_user(user_id.get('email'),["name","user_id","fullname"])
    except:
        return ""

def get_employee_by_name(name, fields=["name"]):
    if isinstance(fields, str):
        fields = [fields]
    emp_data = frappe.db.get_value(
        "Employee",
        {"name": name},
        fields,
        as_dict=1,
    )
    return emp_data


def validate_image(user_image):
    if user_image and "http" not in user_image:
        user_image = BASE_URL + user_image
    return user_image
    
def get_datetime_now():
    return datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).replace(tzinfo=None)

# Get employee reports
def get_report_doc(report_name):
    doc = frappe.get_doc("Report", report_name)
    doc.custom_columns = []
    doc.custom_filters = []

    if doc.report_type == "Custom Report":
        custom_report_doc = doc
        doc = get_reference_report(doc)
        doc.custom_report = report_name
        if custom_report_doc.json:
            data = json.loads(custom_report_doc.json)
            if data:
                doc.custom_columns = data.get("columns")
                doc.custom_filters = data.get("filters")
        doc.is_custom_report = True

    if not doc.is_permitted():
        gen_response(403, "You don't have access to Report " + report_name, [])

    if not frappe.has_permission(doc.ref_doctype, "report"):
        gen_response(403, "You don't have permission", [])
    return doc


def null_location(location):
    if location == "" or not bool(location):
        location = None
    else:
        if not json.loads(location).get("long") or not json.loads(location).get("lat"):
            location = None
    return location


def create_address(new_address,link_cs_address) :
    current_address_cs = frappe.db.get_value("Address",{"address_title":new_address.get("address_title")},["name","address_location"],as_dict=1)
    if current_address_cs:
        current_address_cs = frappe.get_doc("Address",current_address_cs.get("name"))
        current_address_cs.address_location = new_address.get("address_location")
        if link_cs_address:
            links = current_address_cs.links
            find_cs = pydash.filter_(links, lambda cs: cs.get("link_doctype") ==  link_cs_address.get("link_doctype") and cs.get("link_name") != link_cs_address.get("link_name"))
            find_cs.append(link_cs_address)
            current_address_cs.set("links",find_cs)        
        current_address_cs.save()
    else:
        new_address_doc = frappe.new_doc("Address")
        for key,value in new_address.items():
            setattr(new_address_doc,key,value)
        if link_cs_address:
            new_address_doc.append("links",link_cs_address)
        new_address_doc.save()
        current_address_cs = new_address_doc
    return current_address_cs


def create_address_current(address_title,new_location,link_cs_address) :
    current_address = frappe.db.get_value("Address",address_title,["name","address_location"],as_dict=1)
    if current_address:
        current_address_cs = frappe.get_doc("Address",current_address.get("name"))
        current_address_cs.address_location =new_location
        if link_cs_address:
            links = current_address_cs.links
            find_cs = pydash.filter_(links, lambda cs: cs.get("link_doctype") ==  link_cs_address.get("link_doctype") and cs.get("link_name") != link_cs_address.get("link_name"))
            find_cs.append(link_cs_address)
            current_address_cs.set("links",find_cs)        
        current_address_cs.save()
    else:
        new_address_doc = frappe.new_doc("Address")
        new_address = handle_address(address_title)
        if new_address:
            for key,value in new_address.items():
                setattr(new_address_doc,key,value)
            if link_cs_address:
                new_address_doc.append("links",link_cs_address)
            new_address_doc.save()
            current_address_cs = new_address_doc
        else :
            current_address_cs = False
    return current_address_cs

def handle_address(address_title) : 
    address_oop =  {"address_title": address_title}
    arr_address = address_title.split(",")
    arr_address = pydash.map_(arr_address,lambda x : x.strip())
    lenAdd = len(arr_address)
    if len ==1:
        return False
    elif len ==2:
        address_oop.update({               
                        "address_line1":arr_address[0], 
                        "city": arr_address[1],  
                    })
    elif len ==3:
        address_oop.update({               
                        "address_line1":arr_address[0], 
                        "county": arr_address[1],
                        "city": arr_address[2],  
                    })
    elif len ==4:
        address_oop.update({               
                        "address_line1":arr_address[0], 
                        "state": arr_address[1],
                        "county": arr_address[2],
                        "city": arr_address[3],  
                    })
    else :
        address_oop.update({               
                        "state": arr_address[len-3],
                        "county": arr_address[len-2],
                        "city": arr_address[len-1],  
                    })
        address_line1 = ",".join(arr_address[:-3])
        address_oop.update({
            "address_line1":address_line1,
        })
    city_info = frappe.db.get_value(doctype="DMS Province", filters={"ten_tinh": ["like", f"%{address_oop.city}%"]}, fieldname=["ma_tinh"])
    if not city_info:
        return False
    else:
        address_oop.update({               
                        "city":city_info,  
                    })
    if address_oop.county:
        district_info = frappe.db.get_value(doctype="DMS District", filters={"ten_huyen": ["like", f"%{address_oop.county}%"]}, fieldname=["ma_huyen"])
        if district_info :
             address_oop.update({               
                         "county": district_info,
                    })
        else:
            del address_oop["county"]                   
     
    if address_oop.state:
        ward_info = frappe.db.get_value(doctype="DMS Ward", filters={"ten_xa": ["like", f"%{address_oop.state}%"]}, fieldname=["ma_xa"])
        if ward_info:
            address_oop.update({
            "state": ward_info,
            })
        else:
            del address_oop["state"]
    return address_oop
def post_image(name_image, faceimage, doc_type, doc_name):
    # save file and insert Doctype File
    file_name = name_image + "_"+ str(datetime.now().timestamp()) + "_.png"
    imgdata = base64.b64decode(faceimage)
    doc_file = save_file(file_name, imgdata, doc_type, doc_name,
                         folder=None, decode=False, is_private=0, df=None)

    # delete image copy
    path_file = "/files/" + file_name
    delete_file(path_file)
    file_url = BASE_URL + doc_file.get('file_url')
    return file_url

def add_text_to_image(file_name, imgdata, description):
    ## add text to image
    # save image
    doc_file = save_file(file_name, imgdata, "", "",
                     folder=None, decode=False, is_private=0, df=None)
    # Open an Image
    path_file = frappe.get_site_path('public') + doc_file.file_url                
    img = Image.open(path_file)
    # Call draw Method to add 2D graphics in an image
    I1 = ImageDraw.Draw(img)
    # Custom font style and font size
    font_size = 15
    myFont = ImageFont.truetype('FreeMono.ttf', font_size)
    # Add Text to an image
    lines = []
    position = (10, 10)
    x, y = position
    image_width, image_height = img.size
    max_width = img.width - 2 * (x + y)
    font_color = (255, 0, 0)
    for line in description.split("\\n"):
        # Split line into words
        words = line.split()
        current_line = words[0]
        for word in words[1:]:
            # Check if adding the next word exceeds max_width
            if I1.textbbox(xy=(x,y),text=current_line + " " + word, font=myFont)[0] <= max_width:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word
        
        lines.append(current_line)
    for line in lines:
        I1.text((x, y), line, font=myFont, fill=font_color)
        y += font_size
    # get image base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    image_base64_new = base64.b64decode(base64.b64encode(buffered.getvalue()))
    
    # delete file
    frappe.delete_doc('File', doc_file.name)
    path_file = "/files/" + file_name
    delete_file(path_file)
    ##
    return image_base64_new

def upload_image_s3(image,description):
    settings = frappe.get_doc("DMS Settings").as_dict()
    bucket_name_s3 = settings.get('bucket_name_s3')
    # bucket_name_s3 = "mbw-dms"
    endpoint_s3 = settings.get('endpoint_s3')
    imgdata = base64.b64decode(image)
    bucket_domain =frappe.local.site.replace('.','-')
    file_name = "checkin_" + \
        "_" + str(datetime.now()).replace(" ","_") + ".png"
    if description:
        imgdata_new = add_text_to_image(file_name, imgdata, description)
    else:
        imgdata_new = imgdata
    
    # save file image s3
    object_name = f"{bucket_name_s3}/{bucket_domain}/{file_name}"
    # if not my_minio.bucket_exists(bucket_domain):
    #     my_minio.make_bucket(bucket_domain)
    try:    
        create_my_minio('DMS Settings').put_object(bucket_name=bucket_name_s3, object_name=f"{bucket_domain}/{file_name}", data=io.BytesIO(imgdata_new))
    except Exception as e:
        print(e)
    # data response
    data = {}
    data["file_url"] = f"https://{endpoint_s3}/{object_name}"
    data['status'] = True
    return data

# Lấy ra các field của doctype con
def get_value_child_doctype(master_doctype, master_name, name_field):
	if not master_name:
		return
	from frappe.model import child_table_fields, default_fields

	filed_master = frappe.get_doc(master_doctype, master_name)

	field_child = []
	for i, child in enumerate(filed_master.get(name_field)):
		child = child.as_dict()

        # Xóa các trường không cần thiết
		for fieldname in default_fields + child_table_fields:
			if fieldname in child:
				del child[fieldname]

		field_child.append(child)

	return field_child


class ArrayMethod():
    def __init__(self, data=[]):
      self.main = data
    
    def find(self,callback):
        for value in self.main :
            if callback(value):
                return value
    def filter(self, callback):
        array = []
        for value in self.main :
            if callback(value):
                array.append(value)
        return array
    
    def toMap(self, callback):
        array = []
        for value in self.main:
            value = callback(value)
            array.append(value)
        return array
    
def weekday(time:datetime):
    # print(time.strftime("%A"),time)
    first_week_month = time.replace(day=1)
    W_first = float(first_week_month.strftime("%W"))
    listngay = ('Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7')
    anh_xa_ngay_sang_so = {
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
    "Sunday": 0
}
    thu_trong_tuan = listngay[anh_xa_ngay_sang_so[time.strftime("%A")]]
    w = float(time.strftime("%W"))
    tuan =(w - W_first) + 1 if (w - W_first) + 1 <5 else 1
    return thu_trong_tuan, tuan


# Tính tuần hiện tại của tháng
def current_month_week():
    today = datetime.today()
    # Lấy ngày đầu tiên của tháng
    first_day_of_month = today.replace(day=1)
    # Tính toán số ngày đã trôi qua từ đầu tháng
    passed_days = (today - first_day_of_month).days
    # Tính toán tuần hiện tại của tháng
    current_week = passed_days // 7 + 1
    return current_week
    

def get_child_values_doc(doctype, master_name, fields_to_get, chil_name):
    if not master_name:
        return
    master_doc = frappe.get_doc(doctype, master_name)

    chil_values = master_doc.get(chil_name)

    result = []

    for item in chil_values:
        item_dict = {}
        for fieldname in fields_to_get:
            item_dict[fieldname] = item.get(fieldname)
        result.append(item_dict)

    return result


# Lấy sales person cha từ sales person con
def get_all_parent_sales_persons(sales_person):
    parent_sales_persons = []
    parent = frappe.get_value("Sales Person", sales_person, "parent_sales_person")

    while parent:
        is_group = frappe.get_value("Sales Person", parent, "is_group")
        if is_group == 1:
            parent_sales_persons.append(parent)
        parent = frappe.get_value("Sales Person", parent, "parent_sales_person")

    return parent_sales_persons
