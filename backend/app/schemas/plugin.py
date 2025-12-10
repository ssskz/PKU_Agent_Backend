"""
插件相关的Pydantic模式定义
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class PluginBase(BaseModel):
    """插件基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="插件名称")
    description: Optional[str] = Field(None, description="插件描述")
    openapi_spec: Dict[str, Any] = Field(..., description="OpenAPI 3.0.0 规范（JSON）")


class PluginCreate(PluginBase):
    """创建插件的模式"""
    pass


class PluginUpdate(BaseModel):
    """更新插件的模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="插件名称")
    description: Optional[str] = Field(None, description="插件描述")
    openapi_spec: Optional[Dict[str, Any]] = Field(None, description="OpenAPI 3.0.0 规范（JSON）")
    is_active: Optional[int] = Field(None, description="是否激活（1=激活，0=禁用）")


class PluginResponse(PluginBase):
    """插件响应模式"""
    id: int
    uuid: str = Field(..., description="唯一标识UUID")
    user_id: int
    is_active: int
    is_system: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PluginList(BaseModel):
    """插件列表响应模式"""
    total: int
    items: List[PluginResponse]

