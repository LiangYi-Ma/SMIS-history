# author: Mr. Ma
# datetime :2022/8/10
from SMIS.constants import POSITIONNEW_STATUS
from enterprise.models import PositionNew, PositionPost
from enterprise.serializers import choice_mate
from enterprise.utils.get_now_time import now_time


def position_post_up(position_new_id, post_last_days):
    """
    功能：上线岗位公共类（不做上线的上限校验，不做上线的天数上限校验）
    position_new_id：岗位id
    post_last_days：上线天数
    """
    try:
        # 校验状态（只有未上线时才可以上线）
        pn1 = PositionNew.objects.get(id=position_new_id)
        if int(pn1.status) == 3:
            pp1 = PositionPost.objects.filter(position=pn1.id).first()
            if pp1:
                pp1.post_time = now_time()
                pp1.post_last_days = post_last_days
                pp1.save()
            else:
                PositionPost.objects.create(position=pn1, post_last_days=post_last_days)
            pn1.status = 2
            pn1.save()
        else:
            raise ValueError(f'岗位状态为：{choice_mate(POSITIONNEW_STATUS, pn1.status)}，不满足上线操作')
    except Exception as e:
        raise e


def position_post_down(position_new_id):
    """
    功能：下线岗位公共类
    position_new_id：岗位id
    """
    try:
        # 校验状态（只有未上线时才可以上线）
        pn1 = PositionNew.objects.get(id=position_new_id)
        if int(pn1.status) == 2:
            PositionPost.objects.filter(position=pn1.id).delete()
            pn1.status = 3
            pn1.save()
        else:
            raise ValueError(f'岗位状态为：{choice_mate(POSITIONNEW_STATUS, pn1.status)}，不满足下线操作')
    except Exception as e:
        raise e
