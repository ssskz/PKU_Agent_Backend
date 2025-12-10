"""
系统常量定义
集中管理所有魔法数字和字符串常量
"""

# ===================================
# Token相关常量
# ===================================
DEFAULT_TOKEN_EXPIRE_MINUTES = 30
MAX_TOKEN_EXPIRE_MINUTES = 1440  # 24小时
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 30  # 密码重置令牌30分钟有效

# ===================================
# 分页相关常量
# ===================================
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000
MIN_PAGE_SIZE = 1

# ===================================
# 密码相关常量
# ===================================
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 100
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'

# ===================================
# 用户相关常量
# ===================================
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50
USERNAME_REGEX = r'^[a-zA-Z0-9_-]+$'
FORBIDDEN_USERNAMES = ['admin', 'root', 'system', 'administrator', 'superuser', 'test']

# ===================================
# 设备状态常量
# ===================================
class DeviceStatus:
    """设备状态枚举"""
    PENDING = "pending"        # 待绑定产品
    BOUND = "bound"           # 已绑定产品
    ACTIVE = "active"         # 激活状态
    OFFLINE = "offline"       # 离线状态
    ERROR = "error"           # 错误状态
    
    @classmethod
    def all(cls):
        """返回所有状态"""
        return [cls.PENDING, cls.BOUND, cls.ACTIVE, cls.OFFLINE, cls.ERROR]
    
    @classmethod
    def is_valid(cls, status: str) -> bool:
        """验证状态是否有效"""
        return status in cls.all()

# ===================================
# 交互日志类型常量
# ===================================
class InteractionType:
    """交互日志类型"""
    DATA = "data"             # 数据上报
    CONTROL = "control"       # 控制指令
    STATUS = "status"         # 状态更新
    ERROR = "error"           # 错误信息
    HEARTBEAT = "heartbeat"   # 心跳
    CONFIG = "config"         # 配置更新
    
    @classmethod
    def all(cls):
        """返回所有类型"""
        return [cls.DATA, cls.CONTROL, cls.STATUS, cls.ERROR, cls.HEARTBEAT, cls.CONFIG]

# ===================================
# 日志级别常量
# ===================================
class LogLevel:
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# ===================================
# HTTP状态码常量
# ===================================
class HTTPStatus:
    """常用HTTP状态码"""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500

# ===================================
# 数据库相关常量
# ===================================
DB_CONNECTION_POOL_SIZE = 20
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30
DB_POOL_RECYCLE = 3600  # 1小时

# ===================================
# MQTT主题模板
# ===================================
class MQTTTopics:
    """MQTT主题模板"""
    DEVICE_DATA = "devices/{device_uuid}/data"
    DEVICE_STATUS = "devices/{device_uuid}/status"
    DEVICE_HEARTBEAT = "devices/{device_uuid}/heartbeat"
    DEVICE_CONTROL = "devices/{device_uuid}/control"
    DEVICE_CONFIG = "devices/{device_uuid}/config"
    
    @staticmethod
    def get_data_topic(device_uuid: str) -> str:
        """获取设备数据主题"""
        return f"devices/{device_uuid}/data"
    
    @staticmethod
    def get_control_topic(device_uuid: str) -> str:
        """获取设备控制主题"""
        return f"devices/{device_uuid}/control"

# ===================================
# 错误消息常量
# ===================================
class ErrorMessages:
    """错误消息模板"""
    # 认证相关
    INVALID_CREDENTIALS = "邮箱或密码错误"
    ACCOUNT_DISABLED = "账户已被禁用"
    TOKEN_EXPIRED = "登录已过期，请重新登录"
    INVALID_TOKEN = "无效的认证凭据"
    
    # 用户相关
    USER_NOT_FOUND = "用户不存在"
    EMAIL_EXISTS = "该邮箱已注册"
    USERNAME_EXISTS = "该用户名已存在"
    WEAK_PASSWORD = "密码强度不足"
    
    # 设备相关
    DEVICE_NOT_FOUND = "设备不存在"
    DEVICE_NAME_EXISTS = "设备名称已存在"
    DEVICE_OFFLINE = "设备离线"
    
    # 产品相关
    PRODUCT_NOT_FOUND = "产品不存在"
    PRODUCT_CODE_EXISTS = "产品编号已存在"
    
    # 通用错误
    INVALID_INPUT = "输入数据无效"
    OPERATION_FAILED = "操作失败"
    PERMISSION_DENIED = "权限不足"
    RESOURCE_NOT_FOUND = "资源不存在"

# ===================================
# 成功消息常量
# ===================================
class SuccessMessages:
    """成功消息模板"""
    LOGIN_SUCCESS = "登录成功"
    REGISTER_SUCCESS = "注册成功"
    PASSWORD_RESET_SUCCESS = "密码重置成功"
    UPDATE_SUCCESS = "更新成功"
    DELETE_SUCCESS = "删除成功"
    CREATE_SUCCESS = "创建成功"
    OPERATION_SUCCESS = "操作成功"

