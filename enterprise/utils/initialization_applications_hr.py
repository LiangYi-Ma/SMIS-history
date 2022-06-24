# author: Mr. Ma
# datetime :2022/6/22
import random

from enterprise.models import Applications, Recruitment, EnterpriseCooperation


def InitializationApplicationsHr():
    """
        初始化Applications中hr数据(公共方法，在其它接口中有多次调用，勿删)
        return : String
    """
    try:
        applications_datas = Applications.objects.all()
        if applications_datas:
            for i in applications_datas:
                # 如果已经存在hr，则跳过
                if i.hr_id:
                    continue
                else:
                    enterprise_id = Recruitment.objects.filter(id=i.recruitment.id).first()
                    hr_id = EnterpriseCooperation.objects.filter(enterprise_id=enterprise_id.enterprise_id).all()
                    # 多hr，随机选择分配，因为Application的hr外键于整个协作表，所以要将整个数据存入hr
                    if hr_id:
                        # 生成随机数，用作随机hr
                        ram = random.randint(1, len(hr_id))
                        i.hr = hr_id[ram - 1]
                        i.save()
                        return "初始化数据完成！"
                    else:
                        return "企业hr为空！"
        else:
            return "无数据！"
    except Exception as e:
        return str(e)
    return "初始化数据完成！"
