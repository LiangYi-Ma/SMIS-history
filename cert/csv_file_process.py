import codecs
import csv
from SMIS.data_utils import Utils


def find_mobile_within_str(s):
    length = len(s)
    left = 0
    if not length < 11:
        while left + 11 <= length:
            sub_s = s[left: left + 11]
            if sub_s.isdigit():
                return sub_s
            left += 1
    return None


def process_student_file(f):
    # 解析上传文件，转为csv可读的方式
    reader = csv.reader(codecs.iterdecode(f, 'utf-8'), delimiter=',')
    # reader = csv.reader(f)
    # 拿表头
    header = next(reader)
    print(header)

    '''文件格式不合法时的方法出口'''
    if not ((Utils.MOBILE_FIRST_LINE in header) and (Utils.MOBILE_SECOND_LINE in header)):
        return -1

    # 设定第一优先级，第二优先级
    first_line = header.index(Utils.MOBILE_FIRST_LINE)
    second_line = header.index(Utils.MOBILE_SECOND_LINE)
    u_id_line = header.index(Utils.USER_ID_LINE)
    # print(first_line, second_line)
    # print(header)
    valid_mobiles = dict()
    mobile = None
    for row in reader:
        mobile = find_mobile_within_str(row[first_line])
        u_id = row[u_id_line]
        if not mobile:
            mobile = find_mobile_within_str(row[second_line])
        if mobile:
            valid_mobiles[mobile] = u_id

        # print(row)
    # print(valid_mobiles)
    return valid_mobiles


def process_exam_file(f):
    # 解析上传文件，转为csv可读的方式
    reader = csv.reader(codecs.iterdecode(f, 'utf-8'), delimiter=',')
    # reader = csv.reader(f)
    # 拿表头
    header = next(reader)
    print(header)

    '''文件格式不合法时的方法出口'''
    if Utils.GRADE_LINE not in header:
        return -1

    u_id = header.index(Utils.STU_ID_LINE)
    Utils.GRADE_LINE = header.index(Utils.GRADE_LINE)
    grade_dic = dict()
    for row in reader:
        grade = float(row[Utils.GRADE_LINE])
        student_id = row[u_id]
        grade_dic[student_id] = grade

    return grade_dic
