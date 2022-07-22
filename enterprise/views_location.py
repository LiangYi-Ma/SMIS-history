"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
from concurrent.futures import ThreadPoolExecutor

import cond as cond
import uuid as uuid
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic.base import View
from django.contrib.sessions.models import Session
from django.contrib.auth.hashers import make_password
import multiprocessing
from .serializers import PersonnelRetrievalDataSerializer, PositionDataSerializer, CvSerializer
from .utils.candidatesrecommendation import screen_education, screen_experience, screen_salary, screen_position_class

from rest_framework.views import APIView
from rest_framework.response import Response
import csv
from ast import literal_eval
from .utils.location_server import *

'''models'''
from enterprise.models import Metro, EnterpriseLocation, EnterpriseInfo
from enterprise.models import StandardResultSetPagination
'''serializers'''
from enterprise.serializers import EnterpriseInfoSerializer, MetroSerializer


# 省份地铁线路信息
class MetroList(APIView):
    def get(self, request):
        data = request.query_params
        if "province" not in data.keys():
            return Response(status=211, data={"msg": "invalid"})
        this_province = data["province"]
        if this_province.isdigit():
            with open("enterprise/outer_data/adcode_data.csv", "r") as read_file:
                reader = csv.reader(read_file)
                for row in reader:
                    if row[0] == this_province:
                        ch = literal_eval(row[1])
                        this_province = ch[0] if ch[0] != "" else ch[1]

        query_data = Metro.objects.filter(province=this_province)
        obj = StandardResultSetPagination()
        # query_set:传入数据；request:获取URL请求
        page_list = obj.paginate_queryset(query_data, request)
        serializer = MetroSerializer(instance=page_list, many=True)
        res = obj.get_paginated_response(serializer.data)

        return Response(data=dict(province=this_province, metro=res.data))


# 附近的企业
class NearbyEnterprise(APIView):
    def get(self, request):
        data = request.query_params
        if "loc_array" not in data.keys():
            return Response(status=211, data={"msg": "invalid"})
        loc_array = literal_eval(data["loc_array"])
        lat = loc_array[0]
        lng = loc_array[1]
        location = str(lat) + "," + str(lng)
        # 筛选经纬度差值较小的
        lat_range = [lat - 0.0354, lat + 0.0354]
        lng_range = [lng - 0.0354, lng + 0.0354]
        enterprise_query = EnterpriseLocation.objects.filter(lat__range=(lat_range[0], lat_range[1]),
                                                             lng__range=(lng_range[0], lng_range[1]))

        # 挨个儿计算距离
        enterprise_list = []
        for enterprise in enterprise_query:
            this_enterprise = enterprise.id
            to_str = str(enterprise.lat) + "," + str(enterprise.lng)
            res = distanceCalculate(from_str=location, to_str=to_str)
            if res != -1:
                distance = res["distance"]
                enterprise_list.append([this_enterprise.id_id, distance])

        # 距离排序，得到enterprise的id序列
        enterprise_list.sort(key=lambda x: x[1])
        print("!!!!", enterprise_list)
        if enterprise_list[0][1] == 0:
            enterprise_list.pop(0)
        print("????", enterprise_list)

        # 拼接enterpriseinfo
        res_query = []
        for enter in enterprise_list:
            this_info = EnterpriseInfo.objects.filter(id_id=enter[0])
            res_query.extend(this_info)
            # 实例化分页器
            obj = StandardResultSetPagination()
            # query_set:传入数据；request:获取URL请求
            page_list = obj.paginate_queryset(res_query, request)
            serializer = EnterpriseInfoSerializer(instance=page_list, many=True)
            res = obj.get_paginated_response(serializer.data)

        return Response(data=dict(res=res.data))


# 初始化地铁信息表
class InitialMetroInfo(APIView):
    def get(self, request):
        FILE_PATH = "enterprise/outer_data/metro_data.csv"
        with open(FILE_PATH, "r") as metro_data_file:
            reader = csv.reader(metro_data_file)
            for row in reader:
                # row = ['石家庄站', "['轨道交通2号线', '轨道交通3号线']", '[38.010087, 114.485747]', '130104', '河北省']
                station_name = row[0]
                line = literal_eval(row[1])
                loc = literal_eval(row[2])
                ascode = row[3]
                province = row[4]
                # print(station_name, line, loc, ascode, province)
                # exp = ["鲗鱼涌", ['将军澳线', '将军澳支线', '港岛线'], [22.284996, 114.214691], 810102, "香港特别行政区"]
                for l in line:
                    is_exist = Metro.objects.filter(title=station_name, line=l, province=province)
                    if not is_exist.exists():
                        new_station = Metro.objects.create(title=station_name, line=l, province=province, lat=loc[0],
                                                           lng=loc[1], ascode=int(ascode))
                        print(l + ":" + station_name + ", created.")
            metro_data_file.close()
        return Response({})


# 初始化企业坐标
class InitialEnterpriseLocation(APIView):
    def get(self, request):
        """
        初始化企业地址信息。
        """
        # enterprise_list = EnterpriseInfo.objects.all()
        with open("enterprise/outer_data/enterprise_address_2.csv", "r") as enterprise_file:
            reader = csv.reader(enterprise_file)
            for enter in reader:
                id = int(enter[0])
                loc = literal_eval(enter[2])
                this_enterprise = EnterpriseInfo.objects.get(id_id=id)
                is_exist = EnterpriseLocation.objects.filter(id_id=id)
                if not is_exist:
                    new_location = EnterpriseLocation.objects.create(id=this_enterprise, lat=loc[0], lng=loc[1])
                else:
                    new_location = is_exist.first()
                    new_location.lat = loc[0]
                    new_location.lng = loc[1]
                    new_location.save()

        return Response({})
