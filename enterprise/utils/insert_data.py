# author: Mr. Ma
# datetime :2022/7/15

import pymysql


"""
本地插入测试数据，前提先断掉Position表中的外键
"""
conn = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='123456',
    db='db_smis',
    charset='utf8')
cur = conn.cursor()

enterprise = 32
pst_class = 2

fullname = '智能智造'
job_content = '1.紧跟市场；2.分析市场走向'
requirement = '1.出差较多；2.善于总结；'
extra_info = '精力充沛，提升氛围感'
create_time = '2021-04-26 09:46:20.862000'
update_time = '2021-04-26 09:46:20.862000'
strSQL = "insert into enterprise_position(enterprise_id,pst_class_id,fullname,job_content,requirement,extra_info,create_time,update_time) values(%s,%s,%s,%s,%s,%s,%s,%s)"
value = []

try:
    for i in range(3000):
        data = [enterprise, pst_class, f'{fullname}{i}', f'{job_content}{i}', f'{requirement}{i}', extra_info,
                create_time, update_time]
        cur.execute(strSQL, data)
        conn.commit()
except Exception as e:
    raise e
strSQL = 'select * from enterprise_position'
cur.execute(strSQL)
rows = cur.fetchall()
for r in rows:
    print(r)
cur.close()
conn.close()
