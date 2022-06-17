"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
from . import models
import csv
import codecs
from SMIS.data_utils import Utils


class CreateRCM:
    def __init__(self):
        self.file = None

    def get_matrix(self):
        # 解析上传文件，转为csv可读的方式
        reader = csv.reader(codecs.iterdecode(self.file, 'utf-8'), delimiter=',')
        # reader = csv.reader(f)
        # 拿表头
        header = next(reader)
        print(header)


