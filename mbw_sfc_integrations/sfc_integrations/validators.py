import re
from datetime import datetime

# Kiểm tra trường date truyền lên
def validate_date(value):
    try:
        value = int(float(value))
        time = datetime.fromtimestamp(value)
        time = time.replace(hour=0, minute=0, second=0, microsecond=0)
        return str(time)
    except ValueError as e:
        raise Exception('Không đúng định dạng timestamp `%s`' % value)
    except:
        raise Exception('Không đúng định dạng timestamp `%s`' % value)
    
# Kiểm tra giá trị truyền lên có nằm trong các giá trị config không
def validate_choice(choice):
    if isinstance(choice, dict):
        choice = tuple(choice.keys())
    elif not isinstance(choice, tuple):
        choice = (choice,)

    def validate(value):
        if value not in choice:
            raise ValueError("Lựa chọn '%s' không hợp lệ. Giá trị hợp lệ: %s" % (value, choice))
        return value
    return validate

# Kiểm tra trường bắt buộc có dữ liệu truyền lên không được để trống (required=True)
def validate_not_none(value):
    if not value:
        raise ValueError('Vui lòng nhập đầy đủ dữ liệu!')
    return value
