# author: Mr. Ma
# datetime :2022/6/22
import datetime


def enterpriseinfo_key_convert(data):
    """
        外键序列化是会将外键的字段名转化成外键的表名，本方法是将表名再次转化成字段名(自动检测)
        因为在业务的中已经做过空值校验了，所以此处认为data一定是不为空的。
        User因为是主键，在业务中已经删过了，因此这里不转化User
        data: 目标的json数据
        return ：dict
    """
    keys = data.keys()
    target = {'Field': 'field', 'NumberOfStaff': 'staff_size'}
    for i in keys:
        if i in target.keys():
            data[target[i]] = data.pop(i)
    # 加入更新时间
    curr_time = datetime.datetime.now()
    times = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')
    data['update_time'] = times
    return data
