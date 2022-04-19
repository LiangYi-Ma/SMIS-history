"""
    统一参数处理，将整个项目所有涉及到的公共的参数统一的封装
    参数格式：
        1：字母全大写
        2：如果由多含义组成名称，则之间用（_：下划线）连接
    eg: SKILL_LIST

"""


class Utils:
    EDU_LIST = ['小学', '初中', '高中', '中专', '职校', '中技', '专科', '本科', '硕士研究生', '博士研究生', '-', '']
    DEGREE_LIST = ['学士', '硕士', '博士', '-', '']
    SKILL_LIST = ['一般', '了解', '中等', '熟悉', '精通', '-']
    INDUSTRY_LIST = ['矿业', '能源', '电讯', '服装', '航空航天', '化学', '建筑业', '金属冶炼', '造纸', '机械制造', '其他', '']
    PORT_HEAD = "https://inolink.com/ws/BatchSend2.aspx?"
    USERNAME = "tclkj03236"
    PASSWORD = "123456@"
    MSG_HEAD = "您的验证码为"
    SIGN = "，该验证码有效期为10分钟。【智能智造科技】"
    BASE_URL = 'https://api.xiaoe-tech.com'
    TOKEN_PATH = '/token'
    TOKEN_CACHE_PATH = 'access_token.json'
    CONTENT_TYPE = 'application/json'
    MOBILE_FIRST_LINE = '最近采集手机号'
    MOBILE_SECOND_LINE = '账户绑定手机号'
    USER_ID_LINE = '用户ID'
    STU_ID_LINE = '学员id'
    GRADE_LINE = '得分'
    CUSTOMER_SERVICE_USER_NAME = 'service@shiyenet.com.cn'
    CUSTOMER_SERVICE_MAIL_TO = 'talent@shiyenet.com.cn'
    AUTHORIZATION_CODE = 'Hrjd332211'
    # 北京办公地点信息
    CONTACT_US_BJ_LOCATION = "北京"
    CONTACT_US_BJ_PHONE = "18610218901"
    CONTACT_US_BJ_ADDRESS = "北京市海淀区东升科技园B2-103"
    CONTACT_US_URL = "www.zhinengzhizaoedu.com"
    CONTACT_US_BJ_COORDINATES = [116.362698, 40.051569]
