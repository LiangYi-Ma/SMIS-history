import codecs
import csv

MOBILE_FIRST_LINE = '最近采集手机号'
MOBILE_SECOND_LINE = '账户绑定手机号'
USER_ID_LINE = '用户ID'
STU_ID_LINE = '学员id'
GRADE_LINE = '得分'


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
    if not ((MOBILE_FIRST_LINE in header) and (MOBILE_SECOND_LINE in header)):
        return -1

    # 设定第一优先级，第二优先级
    first_line = header.index(MOBILE_FIRST_LINE)
    second_line = header.index(MOBILE_SECOND_LINE)
    u_id_line = header.index(USER_ID_LINE)
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
    if GRADE_LINE not in header:
        return -1

    u_id = header.index(STU_ID_LINE)
    grade_line = header.index(GRADE_LINE)
    grade_dic = dict()
    for row in reader:
        grade = float(row[grade_line])
        student_id = row[u_id]
        grade_dic[student_id] = grade

    return grade_dic
