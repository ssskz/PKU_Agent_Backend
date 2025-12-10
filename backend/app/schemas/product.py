"""
产品相关的Pydantic模式定义
简化的两层架构：产品直接关联设备
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class ProductBase(BaseModel):
    """
    产品基础模式
    
    **产品编码（product_code）说明：**
    - 类型：字符串，最长64字符
    - 格式：建议使用 硬件型号-功能-版本（如：ESP32-S3-TempSensor-01）
    - 唯一性：在系统中必须全局唯一
    - ⚠️ 重要：必须与固件端 DEVICE_CONFIG.h 中的 DEVICE_PRODUCT_ID 完全一致
    - 用途：用于设备注册、配置获取、固件OTA匹配
    """
    product_code: str  # 产品编码/产品标识符（如：ESP32-S3-Dev-01），最长64字符，与固件端product_id一致
    name: str
    description: Optional[str] = None
    category: Optional[str] = None  # 已废弃，保留用于兼容性
    sensor_types: Optional[Dict[str, Any]] = {}  # JSON格式的传感器配置（可选，默认为空）
    control_ports: Optional[Dict[str, Any]] = {}  # JSON格式的控制端口配置（可选，默认为空）
    communication_protocols: Optional[List[str]] = None
    power_requirements: Optional[Dict[str, Any]] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    is_active: Optional[bool] = True
    version: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturer_code: Optional[str] = None
    is_system: Optional[bool] = False  # 是否为系统内置产品（只有管理员可以设置）
    is_shared: Optional[bool] = False  # 是否共享（只对用户创建的产品有效）


class ProductCreate(ProductBase):
    """创建产品的模式"""
    pass


class ProductUpdate(BaseModel):
    """更新产品的模式"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    sensor_types: Optional[Dict[str, Any]] = None
    control_ports: Optional[Dict[str, Any]] = None
    communication_protocols: Optional[List[str]] = None
    power_requirements: Optional[Dict[str, Any]] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturer_code: Optional[str] = None
    is_system: Optional[bool] = None  # 只有管理员可以修改
    is_shared: Optional[bool] = None


class ProductResponse(ProductBase):
    """产品响应模式"""
    id: int
    total_devices: Optional[int] = 0
    is_system: Optional[bool] = False
    is_shared: Optional[bool] = False
    creator_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductList(BaseModel):
    """产品列表模式"""
    id: int
    product_code: str
    name: str
    description: Optional[str] = None  # 产品描述
    category: Optional[str] = None  # 已废弃，保留用于兼容性
    is_active: bool
    version: Optional[str] = None
    manufacturer: Optional[str] = None
    total_devices: Optional[int] = 0
    is_system: Optional[bool] = False
    is_shared: Optional[bool] = False
    creator_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None  # 更新时间
    sensor_types: Optional[Dict[str, Any]] = None  # 传感器配置
    control_ports: Optional[Dict[str, Any]] = None  # 控制端口配置

    class Config:
        from_attributes = True


class ProductSummary(BaseModel):
    """产品摘要模式（用于下拉选择等）"""
    id: int
    product_code: str
    name: str
    category: Optional[str] = None  # 已废弃，保留用于兼容性
    is_active: bool
    is_system: Optional[bool] = False
    is_shared: Optional[bool] = False
    creator_id: Optional[int] = None

    class Config:
        from_attributes = True