# author: Mr. Ma
# datetime :2022/7/21
from models import SensitiveWordFieldClassify, SensitiveWordInfo
import uuid

with open("./mgck2017/贪腐词库.txt") as file:
    res = file.readlines()

s1 = SensitiveWordFieldClassify.objects.filter(id=6).first()
for i in res:
    uid = uuid.uuid4()
    SensitiveWordInfo(name=i, classify=s1, uid=uid).save()



with open("utils/mgck2017/色情词库.txt") as file:
    res = file.readlines()

s1 = SensitiveWordFieldClassify.objects.filter(id=1).first()
for i in res:
    uid = uuid.uuid4()
    SensitiveWordInfo(name=i, classify=s1, uid=uid).save()


with open("utils/mgck2017/民生词库.txt") as file:
    res = file.readlines()

s1 = SensitiveWordFieldClassify.objects.filter(id=5).first()
for i in res:
    uid = uuid.uuid4()
    SensitiveWordInfo(name=i, classify=s1, uid=uid).save()


with open("utils/mgck2017/暴恐词库.txt") as file:
    res = file.readlines()

s1 = SensitiveWordFieldClassify.objects.filter(id=2).first()
for i in res:
    uid = uuid.uuid4()
    SensitiveWordInfo(name=i, classify=s1, uid=uid).save()


with open("utils/mgck2017/key.txt",encoding="utf8") as file:
    res = file.readline()
    res = res.split('|')

s1 = SensitiveWordFieldClassify.objects.filter(id=3).first()
for i in res:
    uid = uuid.uuid4()
    SensitiveWordInfo(name=i, classify=s1, uid=uid).save()