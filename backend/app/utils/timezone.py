"""
时区工具模块 - 统一使用北京时间(UTC+8)
"""
from datetime import datetime, timezone, timedelta

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_time():
    """
    获取当前北京时间
    
    Returns:
        datetime: 带时区信息的北京时间
    """
    return datetime.now(BEIJING_TZ)

def get_beijing_time_naive():
    """
    获取当前北京时间（不带时区信息，用于存储到数据库）
    
    Returns:
        datetime: 不带时区信息的北京时间
    """
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)

def utc_to_beijing(dt):
    """
    将UTC时间转换为北京时间
    
    Args:
        dt: UTC datetime对象（可以带或不带时区信息）
        
    Returns:
        datetime: 北京时间（不带时区信息）
    """
    if dt is None:
        return None
    
    # 如果datetime没有时区信息，假定它是UTC时间
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # 转换到北京时间
    beijing_dt = dt.astimezone(BEIJING_TZ)
    
    # 返回不带时区信息的datetime（用于存储）
    return beijing_dt.replace(tzinfo=None)

def beijing_to_utc(dt):
    """
    将北京时间转换为UTC时间
    
    Args:
        dt: 北京datetime对象（不带时区信息）
        
    Returns:
        datetime: UTC时间（不带时区信息）
    """
    if dt is None:
        return None
    
    # 添加北京时区信息
    beijing_dt = dt.replace(tzinfo=BEIJING_TZ)
    
    # 转换到UTC
    utc_dt = beijing_dt.astimezone(timezone.utc)
    
    # 返回不带时区信息的datetime
    return utc_dt.replace(tzinfo=None)

def format_datetime_beijing(dt):
    """
    格式化datetime为北京时间字符串（ISO 8601格式 + 时区偏移）
    
    Args:
        dt: datetime对象（如果没有时区信息，假定为北京时间）
        
    Returns:
        str: ISO格式的时间字符串，带有+08:00时区偏移，例如：2025-11-15T13:30:00+08:00
    """
    if dt is None:
        return None
    
    # 如果datetime没有时区信息，添加北京时区
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BEIJING_TZ)
    else:
        # 如果有时区信息，转换为北京时区
        dt = dt.astimezone(BEIJING_TZ)
    
    # 返回ISO格式字符串，包含时区偏移
    return dt.isoformat()

