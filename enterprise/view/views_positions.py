# author: Mr. Ma
# datetime :2022/8/5
from django.db import transaction
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from SMIS.constants import CHECK_TEXT_MSG, POSITIONNEW_STATUS
from cert.models import certificationInfo
from ..models import PositionNew, PositionClass, EnterpriseInfo, Field, JobKeywords, TaggedWhatever, SettingChineseTag, \
    StandardResultSetPagination, PositionPost
from ..serializers import PositionNewMakeSerializer, PositionNewMakeDeleteSerializer, PositionNewMakeGetSerializer, \
    PositionNewSerializer, PositionNewPutSerializer, PositionPostPostSerializer, choice_mate
from SMIS.validation import session_exist
from enterprise import field_list
from ..utils import get_now_time
from ..utils.postion_post import position_post_up, position_post_down
from utils.utils_def import sensitive_word


class PositionMake(APIView):

    @transaction.atomic
    def post(self, request):
        """
        功能：职位发布
        """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        data = request.data
        src = PositionNewMakeSerializer(data=data)
        back_dir = dict(code=200, msg="", data=dict())
        if src.is_valid():
            try:
                p1 = PositionNew(
                    fullname=data['fullname'],
                    job_nature=data['job_nature'],
                    job_content=data['job_content'],
                    pst_class=PositionClass.objects.get(pk=data['pst_class']),
                    education=data['education'],
                    job_experience=data['job_experience'],
                    city=data['city'],
                    salary_min=data['salary_min'],
                    salary_max=data['salary_max'],
                    salary_unit=data['salary_unit'],
                    number_of_employers=data['number_of_employers'],
                    email=data['email'],
                    enterprise=EnterpriseInfo.objects.get(pk=data['enterprise'])
                )

                p1.save()
                for i in range(len(data['field'])):
                    f1 = Field.objects.get(pk=data['field'][i])
                    p1.field.add(f1)
                if 'jobkeywords' in data.keys():
                    for i in range(len(data['jobkeywords'])):
                        jk1 = JobKeywords.objects.get(pk=data['jobkeywords'][i])
                        if jk1.level == 2:
                            p1.jobkeywords.add(jk1)
                        else:
                            raise ValueError('jobkeywords关键词不能为根目录！')

                if 'tag' in data.keys():
                    for i in range(len(data['tag'])):
                        tw1 = SettingChineseTag.objects.get(pk=data['tag'][i])
                        p1.tag.add(tw1)
                if 'certificationInfo_id' in data.keys():
                    ci1 = certificationInfo.objects.using("db_cert").filter(
                        cert_id=data['certificationInfo_id']).exists()
                    if ci1:
                        p1.certificationInfo_id = data['certificationInfo_id']
                    else:
                        raise ValueError('certificationInfo_id不存在！')
                p1.like_str = p1.like_str_default()
                p1.save()
                back_dir['msg'] = '数据新增成功'

            except Exception as e:
                back_dir['msg'] = str(e)
        else:
            back_dir['msg'] = src.errors
        return Response(back_dir)

    @transaction.atomic
    def delete(self, request):
        """ 删除岗位（需要注意：删除的时候要检查一下上线表，如果有数据也要删除） """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        data = request.data
        src = PositionNewMakeDeleteSerializer(data=data)
        back_dir = dict(code=200, msg="", data=dict())
        if src.is_valid():
            try:
                pn1 = PositionNew.objects.get(id=data['id'])
                # 清除所有的标签
                pn1.tag.clear()
                # 清除field m2m
                pn1.field.remove()
                # 清除jobkeywords m2m
                pn1.jobkeywords.remove()
                # 清除上线表数据
                pp1 = PositionPost.objects.filter(position=pn1.id).first()
                if pp1:
                    pp1.delete()
                pn1.delete()
                back_dir['msg'] = '删除成功'
            except Exception as e:
                back_dir['msg'] = str(e)
        else:
            back_dir['msg'] = src.errors
        return Response(back_dir)

    def get(self, request):
        """
        功能：企业内搜索岗位
        条件：企业id/状态/职位名称/发布城市
        """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        data = request.data
        src = PositionNewMakeGetSerializer(data=data)
        back_dir = dict(code=200, msg="", data=dict())
        if src.is_valid():
            data_list = ["enterprise_id",
                         "status",
                         "fullname",
                         "city"]
            src = {}
            for i in data.keys():
                if i in data_list:
                    src[i] = data[i]
            pn = PositionNew.objects.filter(**src).all()
            obj = StandardResultSetPagination()
            page_list = obj.paginate_queryset(pn, request)
            serializer = PositionNewSerializer(instance=page_list, many=True)
            res = obj.get_paginated_response(serializer.data)
            back_dir['data'] = res.data
        else:
            back_dir['msg'] = src.errors
        return Response(back_dir)

    @transaction.atomic
    def put(self, request):
        """
        功能：编辑岗位信息
        """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        data = request.data
        src = PositionNewPutSerializer(data=data)
        back_dir = dict(code=200, msg="", data=dict())
        if src.is_valid():
            if len(data.keys()) > 1:
                try:
                    data = dict(data)
                    id = data['id']
                    data.pop('id')
                    m2m_list = ['field', 'jobkeywords', 'tag']
                    data_list = ['id', 'fullname', 'job_nature', 'job_content', 'pst_class', 'field', 'education',
                                 'job_experience', 'jobkeywords', 'city', 'salary_min', 'salary_max', 'salary_unit',
                                 'tag', 'number_of_employers', 'email', 'certificationInfo_id']
                    res = {}
                    for i in data.keys():
                        if i in data_list:
                            if i == 'pst_class':
                                res['pst_class'] = PositionClass.objects.get(id=data['pst_class'])
                            if i not in m2m_list:
                                res[i] = data[i]

                    PositionNew.objects.filter(id=id).update(**res)
                    pn1 = PositionNew.objects.get(id=id)
                    for i in data.keys():
                        if i == 'field':
                            pn1.field.clear()
                            for j in data[i]:
                                f1 = Field.objects.get(id=j)
                                pn1.field.add(f1)
                        if i == 'jobkeywords':
                            pn1.jobkeywords.clear()
                            for j in data[i]:
                                f1 = JobKeywords.objects.get(id=j)
                                pn1.jobkeywords.add(f1)
                        if i == 'tag':
                            pn1.tag.clear()
                            for j in data[i]:
                                w1 = SettingChineseTag.objects.get(pk=j)
                                pn1.tag.add(w1)
                    pn1.like_str = pn1.like_str_default()
                    pn1.save()
                    back_dir['msg'] = '更新成功'
                except Exception as e:
                    back_dir['msg'] = str(e)
            else:
                back_dir['msg'] = '无更新项！'
        else:
            back_dir['msg'] = src.errors
        return Response(back_dir)


class PositionMakeCopy(APIView):
    def get(self, request):
        """
        功能：职位复制
        条件：职位id
        """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        data = request.data
        src = PositionNewMakeDeleteSerializer(data=data)
        back_dir = dict(code=200, msg="", data=dict())
        if src.is_valid():
            pn = PositionNew.objects.filter(id=data['id']).all()
            obj = StandardResultSetPagination()
            page_list = obj.paginate_queryset(pn, request)
            serializer = PositionNewSerializer(instance=page_list, many=True)
            res = obj.get_paginated_response(serializer.data)
            back_dir['data'] = res.data
        else:
            back_dir['msg'] = src.errors
        return Response(back_dir)


class FieldInsertData(APIView):
    """
    功能：Field表数据填充工具接口
    """

    @transaction.atomic
    def get(self, request):
        try:
            data = field_list.field_list
            for i in data:
                f_rep = Field.objects.filter(
                    name=i['label'].strip(),
                    is_root=0 if int(i['extra']['level']) == 2 else 1,
                    is_enable=1
                ).exists()
                if f_rep:
                    f1 = Field.objects.filter(
                        name=i['label'],
                        is_root=False if int(i['extra']['level']) == 2 else True,
                        is_enable=True
                    ).first()
                else:
                    f1 = Field.objects.create(
                        name=i['label'],
                        is_root=False if int(i['extra']['level']) == 2 else True
                    )
                if len(i['children']) > 0:
                    for j in i['children']:
                        f2_rep = Field.objects.filter(
                            name=j['label'],
                            is_root=False if int(j['extra']['level']) == 2 else True,
                            parent=f1,
                            is_enable=1
                        ).exists()
                        if not f2_rep:
                            f2 = Field.objects.create(
                                name=j['label'],
                                is_root=False if int(j['extra']['level']) == 2 else True,
                                parent=f1
                            )
        except Exception as e:
            raise e
        return Response({})


class PostPosition(APIView):
    def post(self, request):
        """
        功能：职位上线
        """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        data = request.data
        src = PositionPostPostSerializer(data=data)
        back_dir = dict(code=200, msg="", data=dict())
        if src.is_valid():
            try:
                position_post_up(data['id'], data['times'])
                back_dir['msg'] = '岗位上线成功'
            except Exception as e:
                back_dir['msg'] = str(e)
        else:
            back_dir['msg'] = src.errors
        return Response(back_dir)

    def put(self, request):
        """
        功能：职位下线
        """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        data = request.data
        src = PositionNewMakeDeleteSerializer(data=data)
        back_dir = dict(code=200, msg="", data=dict())
        if src.is_valid():
            try:
                position_post_down(data['id'])
                back_dir['msg'] = '岗位下线成功'
            except Exception as e:
                back_dir['msg'] = str(e)
        else:
            back_dir['msg'] = src.errors
        return Response(back_dir)

    def get(self, request):
        """
        功能：上线职位刷新
        """
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        data = request.query_params
        src = PositionNewMakeDeleteSerializer(data=data)
        back_dir = dict(code=200, msg="", data=dict())
        if src.is_valid():
            try:
                # 不用检测是否已经上线，并且也不检测职位是否存在（参数校验会自动校验）
                refresh_time = get_now_time.now_time()
                PositionPost.objects.filter(position=data['id']).update(
                    refresh_time=refresh_time)
                back_dir['msg'] = "职位刷新成功"
            except Exception as e:
                back_dir['msg'] = str(e)
        else:
            back_dir['msg'] = src.errors
        return Response(back_dir)


sw = sensitive_word()


class PositionExamine(APIView):
    def get(self, request):
        """ 发布职位审核 (1:规范，2：不规范，3：疑似)"""
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})
        data = request.query_params
        src = PositionNewMakeDeleteSerializer(data=data)
        back_dir = dict(code=200, msg="", data=dict())
        if src.is_valid():
            try:
                pn = PositionNew.objects.get(id=data['id'])
                if pn.status == 1:
                    msg1, state1 = sw.check_text_msg(text=pn.job_content)
                    state1_msg = choice_mate(CHECK_TEXT_MSG, state1)
                    text1 = sw.check_text_msg_keyword(text=pn.job_content)
                    msg2, state2 = sw.check_text_msg(text=pn.fullname)
                    state2_msg = choice_mate(CHECK_TEXT_MSG, state2)
                    text2 = sw.check_text_msg_keyword(text=pn.fullname)
                    back_dir['data'] = {
                        "job_content": {'state': state1, 'state_mag': state1_msg, 'keyword': text1},
                        "fullname": {'state': state2, 'state_mag': state2_msg, 'keyword': text2}
                    }
                else:
                    back_dir['msg'] = f"职位状态为：{choice_mate(POSITIONNEW_STATUS, pn.status)}，不符合审核条件"
            except Exception as e:
                back_dir['msg'] = str(e)
        else:
            back_dir['msg'] = src.errors
        return Response(back_dir)


class ShowField(APIView):
    def get(self, request):

        def get_child(query_record):
            return Field.objects.filter(parent_id=query_record.id)

        back_dir = dict(code=200, msg="", data=dict())
        res = []
        all_branch = Field.objects.filter(parent_id=1)
        for branch in all_branch:
            if branch.name == 'root':
                continue
            dic_1 = dict()
            dic_1["name"] = branch.name
            dic_1["id"] = branch.id
            dic_1["children"] = []
            children = get_child(branch)
            for child in children:
                if child.name == 'root':
                    continue
                dic_2 = dict()
                dic_2["name"] = child.name
                dic_2["id"] = child.id
                dic_2["children"] = []
                dic_1["children"].append(dic_2)
            res.append(dic_1)
        back_dir['data'] = res
        return Response(back_dir)


class ShowPositionClass(APIView):
    def get(self, request):
        def get_children(p_record):
            return PositionClass.objects.filter(parent=p_record)

        back_dir = dict(code=200, msg="", data=dict())
        data = []
        root = PositionClass.objects.get(name="root")
        l1 = get_children(root)
        for level_one in l1:
            dic_1 = dict()
            dic_1["name"] = level_one.name
            dic_1["id"] = level_one.id
            dic_1["children"] = []
            l2 = get_children(level_one)
            for level_two in l2:
                dic_2 = dict()
                dic_2["name"] = level_two.name
                dic_2["id"] = level_two.id
                dic_2["children"] = []
                l3 = get_children(level_two)
                for level_three in l3:
                    dic_3 = dict()
                    dic_3["name"] = level_three.name
                    dic_3["id"] = level_three.id
                    dic_3["children"] = []
                    dic_2["children"].append(dic_3)
                dic_1["children"].append(dic_2)
            data.append(dic_1)
        back_dir['data'] = data
        return Response(data=back_dir)


class read_csv(APIView):
    @transaction.atomic()
    def get(self, request):
        pc_list = []
        with open('enterprise/enterprise_positionclass_202208151134.csv', 'r', encoding='utf-8') as f:
            data = f.readline()  # 占一下第一行
            data_list = f.readlines()
            print(type(data_list[0]))
            print(data_list[0].replace(r'\n', '').split(','))
            for i in data_list:
                li = i.split(',')
                print(li)
                pc = PositionClass(id=li[0], name=li[1], desc=li[2], is_root=li[3], is_enable=li[4], parent_id=li[5],
                                   level=li[6])
                pc_list.append(pc)
                if li[5] == '':
                    raise ValueError("1")
        PositionClass.objects.bulk_create(pc_list)
        return Response({})


class ShowTag(APIView):
    def get(self, request):
        back_dir = dict(code=200, msg="", data=dict())
        try:
            tags = SettingChineseTag.objects.all().values_list('id', 'name')
            data = {}
            for i in tags:
                data[i[0]] = i[1]
            back_dir['data'] = data
        except Exception as e:
            back_dir['msg'] = str(e)
        return Response(back_dir)


class ShowJobkeywords(APIView):
    def get(self, request):

        def get_child(query_record):
            return JobKeywords.objects.filter(parent_id=query_record.id)

        back_dir = dict(code=200, msg="", data=dict())
        res = []
        try:
            all_branch = JobKeywords.objects.get(name='root')
            l1 = get_child(all_branch)
            for branch in l1:
                if branch.name == 'root':
                    continue
                dic_1 = dict()
                dic_1["name"] = branch.name
                dic_1["id"] = branch.id
                dic_1["children"] = []
                children = get_child(branch)
                for child in children:
                    if child.name == 'root':
                        continue
                    dic_2 = dict()
                    dic_2["name"] = child.name
                    dic_2["id"] = child.id
                    dic_2["children"] = []
                    dic_1["children"].append(dic_2)
                res.append(dic_1)
            back_dir['data'] = res
        except Exception as e:
            back_dir['msg'] = str(e)
        return Response(back_dir)
