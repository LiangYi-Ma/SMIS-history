# author: Mr. Ma
# datetime :2022/8/10
import datetime


def now_time():
    curr_time = datetime.datetime.now()
    times = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')
    return times