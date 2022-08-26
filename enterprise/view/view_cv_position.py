# author: Mr. Ma
# datetime :2022/8/18
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.sessions.models import Session

from SMIS.constants import EDUCATION_LEVELS, YEAR_CHOICES, PROVINCES_CHOICES, YEAR_CHOICES_REPLACE
from SMIS.validation import session_exist
from cv.models import CV
from enterprise import serializers
from enterprise.models import EnterpriseCooperation, JobHuntersCollection, StandardResultSetPagination, PositionNew
from enterprise.serializers import PositionCollectionDeleteSerializer, PositionCollectionReturnSerializer, \
    PositionNewMakeDeleteSerializer, choice_mate
from enterprise.utils.PositionNewCvRetrieval_child import age_utiles, educationexperience_utiles, jobexperience_utils, \
    personalinfo_utils_active, personalinfo_utils_sex, personalinfo_utils_education, \
    cv_positionclass_utils_position_class, cv_positionclass_utils_salary, cv_positionclass_utils_city


class PositionCollectionList(APIView):
    """ 企业端：人才信息（人才收藏） """

    def get(self, request):
        """
        逻辑：
            1：根据session获取hr的id
            2：根据写作表查出企业id
            3：然后在人才收藏表查出数据
        数据字段来源：
            姓名：user
            年龄：personinfo
            工作年限，工作经历（岗位+公司）：JobExperience
            学校|学历：EducationExperience
            沟通状态：TODO
            收藏时间：JobHuntersCollection
        条件：
            1：开始时间 | 结束时间  （可全为空不可单侧为空）
            2：状态：TODO
            3：关键词查询：待定，先不做
        """
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')  # 该用户是hr
        back_dir = dict(code=200, msg="", data=dict())
        data = request.query_params
        data_time_list = ['start_time', 'end_time']
        try:
            # 通过hr查找企业id
            this_coop = EnterpriseCooperation.objects.get(user_id=uid)
            # 通过企业id查找收藏的人才(去重)
            num = set(data_time_list).intersection(set(data.keys()))
            num = len(num)
            if num == 2:
                collections_queryset = JobHuntersCollection.objects.filter(enterprise_id=this_coop.enterprise_id,
                                                                           join_date__gte=data['start_time'],
                                                                           join_date__lte=data['end_time']). \
                    order_by("-join_date").distinct()
            elif num == 0:
                collections_queryset = JobHuntersCollection.objects.filter(enterprise_id=this_coop.enterprise_id). \
                    order_by("-join_date").distinct()
            else:
                raise ValueError("start_time 和 end_time不能只存在其一")
            obj = StandardResultSetPagination()
            page_list = obj.paginate_queryset(collections_queryset, request)
            # 序列化（在序列化中填充其它字段）
            serializers_collection_list = serializers.PositionCollectionListsSerializer(instance=page_list, many=True)
            res = obj.get_paginated_response(serializers_collection_list.data)
            back_dir['data'] = res.data
        except Exception as e:
            back_dir['code'] = 1001
            back_dir['msg'] = str(e)
        return Response(back_dir)

    def delete(self, request):
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        data = request.data
        src = PositionCollectionDeleteSerializer(data=data)
        back_dir = dict(code=200, msg="", data=dict())
        if src.is_valid:
            try:
                src = JobHuntersCollection.objects.filter(id=data['id'])
                if src.exists():
                    src.delete()
                    back_dir['msg'] = '删除成功'
                else:
                    back_dir['code'] = 1003
                    back_dir['msg'] = '删除的目标不存在'

            except Exception as e:
                back_dir['code'] = 1002
                back_dir['msg'] = str(e)
        else:
            back_dir['code'] = 1001
            back_dir['msg'] = src.errors
        return Response(back_dir)


class PositionNewCvRetrieval(APIView):

    def post(self, request):
        """
        人才检索（新V2.0原型企业端：涉及5个表，12个筛选条件）：
            条件（如果条件全无，则直接倒叙获取全部数据）：
                01：快捷搜索：企业中的岗位（查出岗位的要求写入下边的条件然后查询）  --非必须--
                    方案：
                        1：快捷搜索不做在此处
                        2：单独做，查询企业发布的列表
                        3：查询该岗位中的以下条件
                        4：如果要做检索则直接用查到的条件来调用本接口，获得检索结果
                02：学历要求：可多选 【list】  --非必须--   PersonalInfo
                    方案：
                        直接匹配而不是去条件以下
                03：院校要求：不限/统招/985....  --非必须--   EducationExperience
                    方案：
                        暂且先不做985/211，只做不限/统招/非统招
                04：年龄要求：范围 【list】  --非必须--  CV  - age()
                    方案：
                        不可单侧为空，在设置序列化器时直接要求list中元素为2个
                05：期望职位：岗位类型（positionclass）【list】  --非必须--   CV_PositionClass
                    方案：
                        1：多选匹配
                        2：只可叶子节点
                06：工作年限：范围  --非必须--   JobExperience -work_year_make()
                    方案：
                        不可单侧为空，在设置序列化器时直接要求list中元素为2个
                07：工作状态：在职，不在职...  --非必须--     CV
                08：薪资要求：范围  --非必须--      CV_PositionClass
                    方案：
                        不可单侧为空，在设置序列化器时直接要求list中元素为2个
                09：活跃日期：活跃状态  --非必须--  PersonalInfo
                10：性别 ： --非必须--   PersonalInfo
                11：期望城市 ： --非必须--     CV_PositionClass
                12：筛选：（状态：已查看/已聊过/不限制）  --非必须--
                    方案：
                        TODO 筛选之后开发
                13：关键词搜索  ：--非必须--
                    方案：
                        只在cv中模糊检索
        """
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        data = request.data
        back_dir = dict(code=200, msg="", data=dict())
        try:
            if len(data.keys()) == 0:
                """如果传的参数为空则，直接查找所有数据，然后分页"""
                cv = CV.objects.all().order_by('-create_time')
                obj = StandardResultSetPagination()
                page_list = obj.paginate_queryset(cv, request)
                # 序列化（在序列化中填充其它字段）
                serializers_collection_list = serializers. \
                    PositionCollectionReturnSerializer(instance=page_list,
                                                       many=True,
                                                       context={
                                                           'position_class': '',
                                                           'city': ''
                                                       })
                res = obj.get_paginated_response(serializers_collection_list.data)
                back_dir['data'] = res.data
            else:
                """有条件则按照条件查询"""
                src = serializers.PositionNewCvRetrievalSerializers(data=data)
                if src.is_valid():
                    keys = list(data.keys())
                    if 'candidate_status' in keys:
                        cvs = CV.objects.filter(status=data['candidate_status'], like_str__icontains=data[
                            'search_term'] if 'search_term' in keys else '').order_by('create_time').all()
                        keys.remove('candidate_status')
                    else:
                        cvs = CV.objects.filter(
                            like_str__icontains=data['search_term'] if 'search_term' in keys else '').order_by(
                            'create_time').all()
                    if 'search_term' in keys:
                        keys.remove('search_term')
                    data_list = ["education", "is_unified_recruit", "age", "work_years", "active", "sex", "city",
                                 "salary", "position_class"]
                    for j in keys:
                        """ 剔除非要求的条件防止下方switch报错"""
                        if j not in data_list:
                            keys.remove(j)

                    # 对检索逻辑进行了封装
                    switch = {
                        "education": lambda cvs, data: personalinfo_utils_education(cvs, data),
                        "is_unified_recruit": lambda cvs, data: educationexperience_utiles(cvs, data),
                        "age": lambda cvs, data: age_utiles(cvs, data),
                        "work_years": lambda cvs, data: jobexperience_utils(cvs, data),
                        "active": lambda cvs, data: personalinfo_utils_active(cvs, data),
                        "sex": lambda cvs, data: personalinfo_utils_sex(cvs, data),
                        "city": lambda cvs, data: cv_positionclass_utils_city(cvs, data),
                        "salary": lambda cvs, data: cv_positionclass_utils_salary(cvs, data),
                        "position_class": lambda cvs, data: cv_positionclass_utils_position_class(cvs, data),
                    }
                    for i in keys:
                        cvs = switch[i](cvs, data[i])
                    obj = StandardResultSetPagination()
                    page_list = obj.paginate_queryset(cvs, request)
                    # 序列化（在序列化中填充其它字段）
                    serializers_collection_list = PositionCollectionReturnSerializer(
                        instance=page_list,
                        many=True,
                        context={
                            "position_class": data['position_class'] if 'position_class' in keys else ''
                        }
                    )
                    res = obj.get_paginated_response(serializers_collection_list.data)
                    back_dir['data'] = res.data
                else:
                    raise ValueError(src.errors)
        except Exception as e:
            back_dir['code'] = 1001
            back_dir['msg'] = str(e)
            back_dir['data'] = {}
        return Response(back_dir)


class PositionNewCvRetrievalQuickSearch(APIView):

    def get(self, request):
        """ 获取企业发布的岗位具体信息填充到条件列表中 """
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        data = request.query_params
        back_dir = dict(code=200, msg="", data={})
        src = PositionNewMakeDeleteSerializer(data=data)
        if src.is_valid:
            try:
                pn = PositionNew.objects.get(id=data["id"])
                data = {
                    "pst_class": {
                        'id': pn.pst_class.id,
                        "name": pn.pst_class.name
                    },
                    "education": {
                        'id': pn.education,
                        "name": choice_mate(EDUCATION_LEVELS, pn.education)
                    },
                    "job_experience": {
                        'id': pn.job_experience,
                        "name": choice_mate(YEAR_CHOICES, pn.job_experience),
                        "replace_name": choice_mate(YEAR_CHOICES_REPLACE, pn.job_experience)
                    },
                    "city": {
                        'id': pn.city,
                        "name": choice_mate(PROVINCES_CHOICES, pn.city)
                    },
                    "salary": [pn.salary_min, pn.salary_max]
                }
                back_dir['data'] = data
            except Exception as e:
                back_dir['code'] = 1002
                back_dir['msg'] = str(e)
        else:
            back_dir['code'] = 1001
            back_dir['msg'] = src.errors
        return Response(back_dir)


class EnterprisePosition(APIView):

    def get(self, request):
        """ 获取企业发布的岗位列表 """
        session_dict = session_exist(request)
        if session_dict["code"] != 1000:
            return JsonResponse(session_dict)
        session_key = request.META.get("HTTP_AUTHORIZATION")
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get('_auth_user_id')  # 该用户是hr
        back_dir = dict(code=200, msg="", data=[])
        try:
            # 通过hr查找企业id
            this_coop = EnterpriseCooperation.objects.get(user_id=uid).enterprise_id
            pn = PositionNew.objects.filter(enterprise=this_coop)
            if pn.exists():
                for i in pn:
                    back_dir['data'].append(
                        {
                            "id": i.id,
                            "name": i.fullname
                        }
                    )
            else:
                raise ValueError('数据为空！')
        except Exception as e:
            back_dir['code'] = 1001
            back_dir['msg'] = str(e)
            back_dir['data'] = {}
        return Response(back_dir)
