import datetime
import os

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, Http404, FileResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table
from reportlab.pdfgen import canvas

from cv.models import CV, CV_PositionClass
from user.models import User, PersonalInfo

from SMIS.search import *

from SMIS.constants import EDUCATION_LEVELS, JOB_NATURE_CHOICES, NATURE_CHOICES, FINANCING_STATUS_CHOICES, \
    PROVINCES_CHOICES, TIME_UNIT_CHOICES, YEAR_CHOICES, PROGRESS_CHOICES, SEX_CHOICE, NATIONS, MARTIAL_CHOICES, \
    SKILL_CHOICES
from SMIS.mapper import PositionClassMapper, UserMapper, PersonalInfoMapper, EvaMapper, CvMapper, JobExMapper, \
    EduExMapper, TraExMapper, FieldMapper, RecruitmentMapper, EnterpriseInfoMapper, ApplicationsMapper, PositionMapper
from SMIS.validation import is_null

from django.views.generic.base import View
from django.contrib.sessions.models import Session


# Create your views here.

def session_exist(request):
    # session_key = request.session.session_key
    session_key = request.META.get("HTTP_AUTHORIZATION")
    print("*****", request.META.get("HTTP_AUTHORIZATION"))
    back_dir = dict(code=1000, msg="", data=dict())
    try:
        is_existed = Session.objects.get(session_key__exact=session_key)
        if is_existed and is_existed.expire_date <= datetime.datetime.now():
            back_dir["code"] = 0
            back_dir["msg"] = "session[" + is_existed.session_key + "]已失效"
            request.session.flush()
    except:
        if session_key:
            back_dir["code"] = 0
            back_dir["msg"] = "session[" + session_key + "]未被检测到"
        else:
            back_dir["code"] = 0
            back_dir["msg"] = "接收到的session_key为空"

    # 判断 session_key是否存在
    # if not is_existed:
    #     back_dir["code"] = 0
    #     back_dir["msg"] = "未检测到session或session已失效"
    #     request.session.flush()
    return back_dir


def calculate_age(date):
    today_d = datetime.datetime.now().date()
    try:
        birth_t = date.replace(year=today_d.year)
        if today_d > birth_t:
            age = today_d.year - date.year
        else:
            age = today_d.year - date.year - 1
        return age
    except:
        return None


def split_q(q):
    length = len(q)
    splited_list = []
    for i in range(length):
        splited_list.append(q[0: i + 1])
        if q[i + 1:] != '':
            splited_list.append(q[i + 1:])
    return splited_list


def show_cv(request, user_id, cv_id):
    session_exist(request)
    back_dir = dict(code=1000, msg="", data=dict())
    data = dict()

    sex_choices = []
    for idx, label in SEX_CHOICE:
        sex_choices.append(dict(idx=idx, label=label))
    nations_choices = []
    for idx, label in NATIONS:
        nations_choices.append(dict(idx=idx, label=label))
    province_choices = []
    for idx, label in PROVINCES_CHOICES:
        province_choices.append(dict(idx=idx, label=label))
    martial_choices = []
    for idx, label in MARTIAL_CHOICES:
        martial_choices.append(dict(idx=idx, label=label))
    education_choices = []
    for idx, label in EDUCATION_LEVELS:
        education_choices.append(dict(idx=idx, label=label))
    skill_levels = []
    for idx, label in SKILL_CHOICES:
        skill_levels.append(dict(idx=idx, label=label))
    data["skill_levels"] = skill_levels
    data["sex_choices"] = sex_choices
    data["nations_choices"] = nations_choices
    data["province_choices"] = province_choices
    data["martial_choices"] = martial_choices
    data["education_choices"] = education_choices

    user = get_object_or_404(User, pk=user_id)
    personal = get_object_or_404(PersonalInfo, pk=user_id)
    if not (user and personal):
        data["cv_owner"] = None
        data["personal"] = None
    else:
        data["cv_owner"] = UserMapper(user).as_dict()
        data["personal"] = PersonalInfoMapper(personal).as_dict()

    job_info_set = []
    job = personal.jobexperience_set.order_by('-start_date')
    for j in job:
        job_info_set.append(JobExMapper(j).as_dict())
    tra_info_set = []
    tra = personal.trainingexperience_set.order_by('-start_date')
    for t in tra:
        tra_info_set.append(TraExMapper(t).as_dict())
    edu_info_set = []
    edu = personal.educationexperience_set.order_by('-start_date')
    for e in edu:
        edu_info_set.append(EduExMapper(e).as_dict())
    data["job_info_set"] = job_info_set
    data["edu_info_set"] = edu_info_set
    data["tra_info_set"] = tra_info_set

    # evaluation = get_object_or_404(Evaluation, pk=personal.id)
    # cv = get_object_or_404(CV, pk=user_id)

    cv = CV.objects.get(id=cv_id, user_id=user_id)
    data["cv"] = CvMapper(cv).as_dict()
    cv_pstClass = CV_PositionClass.objects.get(cv_id=cv_id)
    data["cv_positionClass"] = cv_pstClass.position_class_id.name

    introduction = personal.evaluation
    data["evaluation"] = EvaMapper(introduction).as_dict()

    if user.personalinfo.date_of_birth:
        age = calculate_age(user.personalinfo.date_of_birth)
    else:
        age = '**'

    # template = loader.get_template('cv/show-cv.html')
    cv_comment = give_comment(cv)
    data["cv_comment"] = cv_comment
    comment_is_none = True
    for k, v in cv_comment.items():
        if v:
            comment_is_none = False
            break
    data["comment_is_none"] = comment_is_none

    print(cv_comment)

    back_dir["data"] = data
    return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})

    # return render(request, 'cv/show-cv.html', locals())


def give_comment(cv_obj):
    comment = {'basic': [], 'education': [], 'job': [], 'training': [], 'other': [], 'important': []}
    user_id = cv_obj.user_id_id
    user_obj = User.objects.get(id=user_id)
    personal_obj = user_obj.personalinfo
    cv_pstClass_this = CV_PositionClass.objects.get(cv_id=cv_obj.id)
    dict_important = {
        '期望薪资': cv_obj.expected_salary,
        '求职意向': cv_pstClass_this.position_class_id.name,
    }

    for key, value in dict_important.items():
        if not value:
            tip = "简历中重要信息缺失，请务必填写" + key
            comment['important'].append(tip)
        else:
            pass

    dict_basic = {
        '性别': personal_obj.sex,
        '国籍': personal_obj.nation,
        '生日': personal_obj.date_of_birth,
        '身高': personal_obj.height,
        '体重': personal_obj.weight,
        '特长/爱好': cv_obj.talent,
        '手机号': personal_obj.phone_number,
        '邮箱': user_obj.email,
    }
    for key, value in dict_basic.items():
        if value is None:
            tip = "简历中基本信息缺失，请填写" + key
            comment['basic'].append(tip)
        else:
            pass

    dict_other = {
        '英语水平': cv_obj.english_skill,
        '计算机水平': cv_obj.computer_skill,
        '技能描述': cv_obj.professional_skill,
        '荣誉与奖项': cv_obj.award,
    }

    for key, value in dict_other.items():
        if not value:
            tip = "信息缺失，请填写" + key
            comment['other'].append(tip)
        else:
            pass

    try:
        edu = personal_obj.educationexperience_set.order_by('start_date')
        if len(edu) == 0:
            comment['education'].append("你还没有填写教育经历，请注意")
    except:
        comment['education'].append("你还没有填写教育经历，请注意")

    try:
        tra = personal_obj.trainingexperience_set.order_by('start_date')
        if len(tra) == 0:
            comment['training'].append("你还没有填写培训经历，如果你曾经有过培训经历，请注意填写")
    except:
        comment['training'].append("你还没有填写培训经历，如果你曾经有过培训经历，请注意填写")

    try:
        job = personal_obj.jobexperience_set.order_by('start_date')
        if len(job) == 0:
            comment['job'].append("工作经历应当是简历的主体内容，请填写工作经历")
    except:
        comment['job'].append("工作经历应当是简历的主体内容，请填写工作经历")

    return comment


def save_as_pdf(request, user_id, cv_id):
    sex_choices = SEX_CHOICE
    birth_provinces = PROVINCES_CHOICES
    nations = NATIONS
    education_levels = EDUCATION_LEVELS
    skill_levels = SKILL_CHOICES
    martials = MARTIAL_CHOICES

    def sig(var):
        if len(var):
            return 1
        else:
            return 0

    FONTSIZE = 13
    FONTSIZE_TITLE = 26
    FONT_NAME = 'fs'
    FONT_NAME_TITLE = 'cfs'

    pdfmetrics.registerFont(TTFont('yahei', '微软雅黑.ttf'))
    pdfmetrics.registerFont(TTFont('fs', '方正仿宋_GB18030.ttf'))
    pdfmetrics.registerFont(TTFont('cfs', '汉仪粗仿宋简.ttf'))

    user = get_object_or_404(User, pk=user_id)
    personal = get_object_or_404(PersonalInfo, pk=user_id)
    job_info_set = personal.jobexperience_set.order_by('-start_date')
    tra_info_set = personal.trainingexperience_set.order_by('-start_date')
    edu_info_set = personal.educationexperience_set.order_by('-start_date')
    # evaluation = get_object_or_404(Evaluation, pk=personal.id)
    # cv = get_object_or_404(CV, pk=user_id)
    cv = user.cv_set.filter(user_id=user_id, id=cv_id).first()
    elements = []

    # 标题样式
    styleSheet = getSampleStyleSheet()
    style_title = styleSheet['BodyText']
    # 字体、字号、自动换行、行间距、居中
    style_title.fontName = FONT_NAME
    style_title.fontSize = FONTSIZE_TITLE
    style_title.wordWrap = 'CJK'
    style_title.leading = 16
    style_title.alignment = 1

    p_title = Paragraph('个人简历', style_title)

    # 左对齐正文
    styleSheet = getSampleStyleSheet()
    style_left = styleSheet['BodyText']
    # 字体、字号、自动换行、行间距、居中
    style_left.fontName = FONT_NAME
    style_left.fontSize = FONTSIZE
    style_left.wordWrap = 'CJK'
    style_left.leading = 16
    style_left.alignment = 0

    items = {
        'name': str(user.last_name + user.first_name),
        'sex': user.personalinfo.sex,
        'nation': user.personalinfo.nation,
        # 'image': Image(user.personalinfo.image, width=1.33 * inch, height=1.9 * inch),
        'phone': user.personalinfo.phone_number,
        'email': user.email,
        'birth_place': user.personalinfo.birth_address,
        'education': user.personalinfo.education,
        'martial': user.personalinfo.martial_status,
        'birth_date': user.personalinfo.date_of_birth,
        'height': user.personalinfo.height,
        'weight': user.personalinfo.weight,
        'english': cv.english_skill,
        'computer': cv.computer_skill,
        'talent': cv.talent,
        'intention': CV_PositionClass.objects.get(cv_id=cv.id).position_class_id.name,
        'salary': cv.expected_salary,

    }

    for idx, opt in sex_choices:
        if items["sex"] == idx:
            items["sex"] = opt
    for idx, opt in nations:
        if items["nation"] == idx:
            items["nation"] = opt
    for idx, opt in birth_provinces:
        if items["birth_place"] == idx:
            items["birth_place"] = opt
    for idx, opt in education_levels:
        if items["education"] == idx:
            items["education"] = opt
    for idx, opt in martials:
        if items["martial"] == idx:
            items["martial"] = opt
    for idx, opt in skill_levels:
        if items["english"] == idx:
            items["english"] = opt
        if items["computer"] == idx:
            items["computer"] = opt

    if not user.personalinfo.image:
        items['image'] = '照片'
    else:
        items['image'] = Image(user.personalinfo.image, width=1.33 * inch, height=1.9 * inch)

    # 段落样式
    styleSheet = getSampleStyleSheet()
    style = styleSheet['BodyText']
    # 字体、字号、自动换行、行间距、居中
    style.fontName = FONT_NAME
    style.fontSize = FONTSIZE
    style.wordWrap = 'CJK'
    style.leading = 18
    style.alignment = 1

    # 小标题样式
    styleSheet = getSampleStyleSheet()
    style_little_title = styleSheet['BodyText']
    style_little_title.fontName = FONT_NAME_TITLE
    style_little_title.fontSize = FONTSIZE
    style_little_title.leading = 18
    style_little_title.alignment = 1

    p_talent = Paragraph(items['talent'], style)
    p_intention = Paragraph(items['intention'], style)

    data = [
        [p_title, '', '', '', '', '', '', '', '', '', '', ''],
        ['姓名', items['name'], '', '性别', items['sex'], '', '民族', items['nation'], '', items['image'], '', ''],
        ['籍贯', items['birth_place'], '', '学历', items['education'], '', '婚否', items['martial'], '', '', '', ''],
        ['生日', items['birth_date'], '', '身高', items['height'], '', '体重', items['weight'], '', '', '', ''],
        ['英语', items['english'], '', '计算机', items['computer'], '', '特长', p_talent, '', '', '', ''],
        ['手机', items['phone'], '', '', '邮箱', items['email'], '', '', '', '', '', ''],
        ['求职意向', '', p_intention, '', '', '', '', '期望薪资', '', str(items['salary']) + '+', '', '']
    ]

    if edu_info_set:
        data.append(
            [Paragraph('<strong>教育经历</strong>', style_little_title), '', '', '', '', '', '', '', '', '', '', ''])

        for edu in edu_info_set:
            edu_items = {'date': str(str(edu.start_date.year) + '.' + str(edu.start_date.month) + '-'
                                     + str(edu.end_date.year) + '.' + str(edu.end_date.month)),
                         'school': edu.school + '-' + edu.department + '-' + edu.major, 'content': edu.education}
            for idx, opt in education_levels:
                if edu_items["content"] == idx:
                    edu_items["content"] = opt

            e_set = [edu_items['date'], '', '', edu_items['school'], '', '', '', '', '', '', edu_items['content'], '']
            data.append(e_set)

    if tra_info_set:
        data.append(
            [Paragraph('<strong>培训经历</strong>', style_little_title), '', '', '', '', '', '', '', '', '', '', ''])

        for tra in tra_info_set:
            tra_items = {
                'date': str(str(tra.start_date.year) + '.' + str(tra.start_date.month) + '-'
                            + str(tra.end_date.year) + '.' + str(tra.end_date.month)),
                'team': Paragraph(tra.training_team, style),
                'content': Paragraph(tra.training_name, style)
            }
            t_set = [tra_items['date'], '', '', tra_items['team'], '', '', tra_items['content'], '', '', '', '', '']
            data.append(t_set)

    if job_info_set:
        data.append(
            [Paragraph('<strong>工作经历</strong>', style_little_title), '', '', '', '', '', '', '', '', '', '', ''])

        for job in job_info_set:
            job_items = {
                'date': str(str(job.start_date.year) + '.' + str(job.start_date.month) + '-'
                            + str(job.end_date.year) + '.' + str(job.end_date.month)),
                'enterprise': Paragraph(job.enterprise, style),
                'position': job.position,
                'content': Paragraph(job.job_content, style)
            }
            # date = str(job.start_date.year + '~' + job.end_date.year)
            # date = 'date'
            j_set = [job_items['date'], '', '', job_items['enterprise'], '', '', job_items['position'], '',
                     job_items['content'], '', '', '']
            data.append(j_set)

    data.append([Paragraph('<strong>专业与技能</strong>', style_little_title), '', '', '', '', '', '', '', '', '', '', ''])

    skill_items = {
        'courses': Paragraph(cv.courses, style_left),
        'skills': Paragraph(cv.professional_skill, style_left),
        'award': Paragraph(cv.award, style_left),
        'teacher': None,
        'self': None
    }
    # if user.personalinfo. '] = user.personalinfo.evaluation.self_evaluation

    try:
        skill_items['teacher'] = user.personalinfo.evaluation.teacher_evaluation
        skill_items['self'] = user.personalinfo.evaluation.self_evaluation
    except:
        pass

    skill_length = 0

    if skill_items['courses']:
        data.append(
            [Paragraph('所修课程', style_little_title), '', skill_items['courses'], '', '', '', '', '', '', '', '', ''])
        skill_length += 1
    if skill_items['skills']:
        data.append(
            [Paragraph('掌握技能', style_little_title), '', skill_items['skills'], '', '', '', '', '', '', '', '', ''])
        skill_length += 1
    if skill_items['award']:
        data.append(
            [Paragraph('荣誉/证书', style_little_title), '', skill_items['award'], '', '', '', '', '', '', '', '', ''])
        skill_length += 1
    if skill_items['teacher'] or skill_items['self']:
        evaluation_flag = 1
        if skill_items['teacher']:
            data.append(
                [Paragraph('<strong>教师评价</strong>', style_little_title), '', '', '', '', '', '', '', '', '', '', ''])
            data.append([Paragraph(skill_items['teacher'], style_left), '', '', '', '', '', '', '', '', '', '', ''])
        else:
            data.append(
                [Paragraph('<strong>自我评价</strong>', style_little_title), '', '', '', '', '', '', '', '', '', '', ''])
            data.append([Paragraph(skill_items['self'], style_left), '', '', '', '', '', '', '', '', '', '', ''])
    else:
        evaluation_flag = 0

    # # pdfmetrics.registerFont(TTFont('puhui', 'Alibaba-PuHuiTi-Bold.ttf'))
    # # pdfmetrics.registerFont(TTFont('yaheilight', '微软雅黑Light.ttc'))
    #
    # # styles = getSampleStyleSheet()
    # # styles.add(ParagraphStyle(fontName='puhui', name='ph', leading=20, fontSize=12))
    #
    ts = [  # 字体
        ('FONT', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), FONTSIZE),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),

        # 网格
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.black),
        ('BOX', (0, 1), (-1, -1), 0.5, colors.black),

        # 内容字体
        # ('FONT', (1, 0), (3, 0), 'fs'),
        # ('FONT', (5, 0), (5, 0), 'fs'),
        ('SPAN', (0, 0), (11, 0)),
        # ('BOTTOMPADDING', (0, 0), (11, 0), 8),

        ('SPAN', (9, 1), (11, 5)),
        ('SPAN', (1, 1), (2, 1)),
        ('SPAN', (4, 1), (5, 1)),
        ('SPAN', (7, 1), (8, 1)),

        ('SPAN', (1, 2), (2, 2)),
        ('SPAN', (4, 2), (5, 2)),
        ('SPAN', (7, 2), (8, 2)),

        ('SPAN', (1, 3), (2, 3)),
        ('SPAN', (4, 3), (5, 3)),
        ('SPAN', (7, 3), (8, 3)),

        ('SPAN', (1, 4), (2, 4)),
        ('SPAN', (4, 4), (5, 4)),
        ('SPAN', (7, 4), (8, 4)),

        ('SPAN', (1, 5), (3, 5)),
        ('SPAN', (5, 5), (8, 5)),

        ('SPAN', (0, 6), (1, 6)),
        ('SPAN', (2, 6), (6, 6)),
        ('SPAN', (7, 6), (8, 6)),
        ('SPAN', (9, 6), (11, 6)),

        ('FONT', (0, 1), (0, 1), FONT_NAME_TITLE),
        ('FONT', (0, 2), (0, 2), FONT_NAME_TITLE),
        ('FONT', (0, 3), (0, 3), FONT_NAME_TITLE),
        ('FONT', (0, 4), (0, 4), FONT_NAME_TITLE),
        ('FONT', (0, 5), (0, 5), FONT_NAME_TITLE),

        ('FONT', (3, 1), (3, 1), FONT_NAME_TITLE),
        ('FONT', (3, 2), (3, 2), FONT_NAME_TITLE),
        ('FONT', (3, 3), (3, 3), FONT_NAME_TITLE),
        ('FONT', (3, 4), (3, 4), FONT_NAME_TITLE),

        ('FONT', (6, 1), (6, 1), FONT_NAME_TITLE),
        ('FONT', (6, 2), (6, 2), FONT_NAME_TITLE),
        ('FONT', (6, 3), (6, 3), FONT_NAME_TITLE),
        ('FONT', (6, 4), (6, 4), FONT_NAME_TITLE),

        ('FONT', (4, 5), (4, 5), FONT_NAME_TITLE),
        ('FONT', (0, 6), (1, 6), FONT_NAME_TITLE),
        ('FONT', (7, 6), (8, 6), FONT_NAME_TITLE),

        # ('SPAN', (0, 7), (11, 7)),
    ]

    dealed_lines = 7
    fixed_lines = 7
    extra_lines = len(edu_info_set) + len(tra_info_set) + len(job_info_set)

    if edu_info_set:
        ts.append(('SPAN', (0, dealed_lines), (11, dealed_lines)))
        ts.append(('FONT', (0, dealed_lines), (11, dealed_lines), FONT_NAME_TITLE))
        dealed_lines += 1
        extra_lines += 1

    for i in range(len(edu_info_set)):
        ts.append(('SPAN', (0, dealed_lines), (2, dealed_lines)))
        ts.append(('SPAN', (3, dealed_lines), (9, dealed_lines)))
        ts.append(('SPAN', (10, dealed_lines), (11, dealed_lines)))
        dealed_lines += 1

    if tra_info_set:
        ts.append(('SPAN', (0, dealed_lines), (11, dealed_lines)))
        dealed_lines += 1
        extra_lines += 1

    for i in range(len(tra_info_set)):
        ts.append(('SPAN', (0, dealed_lines), (2, dealed_lines)))
        ts.append(('SPAN', (3, dealed_lines), (5, dealed_lines)))
        ts.append(('SPAN', (6, dealed_lines), (11, dealed_lines)))
        dealed_lines += 1

    if job_info_set:
        ts.append(('SPAN', (0, dealed_lines), (11, dealed_lines)))
        dealed_lines += 1
        extra_lines += 1

    for i in range(len(job_info_set)):
        ts.append(('SPAN', (0, dealed_lines), (2, dealed_lines)))
        ts.append(('SPAN', (3, dealed_lines), (5, dealed_lines)))
        ts.append(('SPAN', (6, dealed_lines), (7, dealed_lines)))
        ts.append(('SPAN', (8, dealed_lines), (11, dealed_lines)))
        dealed_lines += 1

    if skill_length:
        ts.append(('SPAN', (0, dealed_lines), (11, dealed_lines)))
        dealed_lines += 1
        extra_lines += 1

    for i in range(skill_length):
        ts.append(('SPAN', (0, dealed_lines), (1, dealed_lines)))
        ts.append(('SPAN', (2, dealed_lines), (11, dealed_lines)))
        dealed_lines += 1

    if evaluation_flag:
        ts.append(('SPAN', (0, dealed_lines), (11, dealed_lines)))
        dealed_lines += 1
        # ts.append(('SPAN', (0, dealed_lines), (1, dealed_lines)))
        ts.append(('SPAN', (0, dealed_lines), (11, dealed_lines)))
        dealed_lines += 1

    t = Table(data, 12 * [0.6 * inch], 0.5 * inch, ts)

    title_height = 0.8 * inch
    block_title_height = 0.3 * inch
    exist_flag = 0

    t._argH[0] = title_height

    line_edu = 0
    line_job = 0
    line_tra = 0
    line_skill = 0
    line_eva = 0
    lines = [line_edu, line_tra, line_job, line_skill, line_eva]

    if edu_info_set:
        exist_flag += 1
        lines[0] = fixed_lines - 1 + exist_flag

    if tra_info_set:
        exist_flag += 1
        lines[1] = fixed_lines - 1 + len(edu_info_set) + exist_flag

    if job_info_set:
        exist_flag += 1
        lines[2] = fixed_lines - 1 + len(edu_info_set) + len(tra_info_set) + exist_flag

    if skill_length:
        exist_flag += 1
        lines[3] = fixed_lines - 1 + len(edu_info_set) + len(job_info_set) + len(tra_info_set) + exist_flag

    if evaluation_flag:
        exist_flag += 1
        lines[4] = fixed_lines - 1 + len(edu_info_set) + len(job_info_set) + len(tra_info_set) \
                   + skill_length + exist_flag

    for i in lines:
        if i:
            t._argH[i] = block_title_height

    # # Paragraph(t, styles['ph'])

    file_name = 'CV_%s_%s.pdf' % (user.id, cv.id)
    print(file_name)
    print("oook")
    # t = Table(data, 12 * [0.6 * inch], 0.5 * inch, ts)
    elements.append(t)
    doc = SimpleDocTemplate(file_name)
    print("ook")

    doc.build(elements)

    print("ok")
    from django.utils.encoding import escape_uri_path
    # def hello(c):
    #     c.drawString(100, 100, "hello")
    # file_path = "hello.pdf"
    # c = canvas.Canvas("hello.pdf")
    # hello(doc)
    # doc.showPage()
    # doc.save()
    # try:
    #     response = FileResponse(open(file_name, 'rb'))
    #     response['content_type'] = "application/octet-stream"
    #     response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_name)
    #     print("ok")
    #     return response
    # except Exception:
    #     raise Http404
    try:
        response = StreamingHttpResponse(open(file_name, 'rb'), content_type="application/pdf", )
        response['content_type'] = "application/octet-stream"
        response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_name)
        return response
    except Exception:
        raise Http404
    # return render(request, "cv/download-cv.html", locals())


class SearchCv(View):
    def get(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dir = dict(code=1000, msg="", data=dict())
        data = dict()

        education_levels = []
        for idx, label in EDUCATION_LEVELS:
            education_levels.append(dict(idx=idx, label=label))
        data["education_levels"] = education_levels

        skill_levels = []
        for idx, label in SKILL_CHOICES:
            skill_levels.append(dict(idx=idx, label=label))
        data["skill_levels"] = skill_levels

        post_list = CV.objects.order_by('-update_time')
        if len(post_list) >= 7:
            post_list = post_list[:7]

        cv_list = []
        for post in post_list:
            cv_list.append(CvMapper(post).as_dict())
        data["post_list"] = cv_list

        data["has_q"] = False

        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args, **kwargs):
        session_dict = session_exist(request)
        if session_dict["code"] is 0:
            return JsonResponse(session_dict, safe=False, json_dumps_params={'ensure_ascii': False})

        back_dir = dict(code=1000, msg="", data=dict())
        data = dict()

        education_levels = []
        for idx, label in EDUCATION_LEVELS:
            education_levels.append(dict(idx=idx, label=label))
        data["education_levels"] = education_levels

        skill_levels = []
        for idx, label in SKILL_CHOICES:
            skill_levels.append(dict(idx=idx, label=label))
        data["skill_levels"] = skill_levels

        q = request.GET.get('q')
        if is_null(q):
            q = request.POST.get("q")
        print(q)
        # 当q不为空时
        print(is_null(q))
        if not is_null(q):
            lst = split_q(q)
            post_list = CV.objects.filter(
                Q(user_id__personalinfo__phone_number__icontains=q)
                | Q(user_id__username__icontains=q)
                | Q(user_id__first_name__in=lst)
                | Q(user_id__last_name__in=lst))
            if post_list:
                cv_list = []
                for post in post_list:
                    cv_list.append(CvMapper(post).as_dict())
                data["post_list"] = cv_list
                data["search_result_is_none"] = False

                data["has_q"] = True
            else:
                post_list = CV.objects.order_by('-update_time')
                if len(post_list) >= 7:
                    post_list = post_list[:7]

                cv_list = []
                for post in post_list:
                    cv_list.append(CvMapper(post).as_dict())
                data["post_list"] = cv_list

                data["search_result_is_none"] = True

                data["has_q"] = True
        else:
            post_list = CV.objects.order_by('-update_time')
            if len(post_list) >= 7:
                post_list = post_list[:7]

            cv_list = []
            for post in post_list:
                cv_list.append(CvMapper(post).as_dict())
            data["post_list"] = cv_list
            data["search_result_is_none"] = None

            data["has_q"] = False
        back_dir["data"] = data
        return JsonResponse(back_dir, safe=False, json_dumps_params={'ensure_ascii': False})

#
# @login_required
# def search_cv_page(request):
#     has_q = 0
#     try:
#         q = request.GET.get('q')
#     except:
#         q = None
#     if not q:
#         post_list = CV.objects.order_by('-update_time')
#         if len(post_list) >= 7:
#             post_list = post_list[:7]
#     else:
#         lst = split_q(q)
#         post_list = CV.objects.filter(
#             Q(user_id__personalinfo__phone_number__icontains=q)
#             | Q(user_id__username__icontains=q)
#             | Q(user_id__first_name__in=lst)
#             | Q(user_id__last_name__in=lst))
#         has_q = 1
#
#     return render(request, 'cv/search-cv.html', locals())
