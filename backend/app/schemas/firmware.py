from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class FirmwareBase(BaseModel):
    """固件基础模式"""
    product_code: str = Field(..., description="产品代号")
    version: str = Field(..., description="固件版本号")
    firmware_url: str = Field(..., description="固件下载URL")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    file_hash: Optional[str] = Field(None, description="文件SHA256哈希值")
    description: Optional[str] = Field(None, description="版本描述")
    release_notes: Optional[str] = Field(None, description="发布说明")
    is_active: bool = Field(True, description="是否激活")
    is_latest: bool = Field(False, description="是否为最新版本")

class FirmwareCreate(FirmwareBase):
    """创建固件模式"""
    pass

class FirmwareUpdate(BaseModel):
    """更新固件模式"""
    version: Optional[str] = Field(None, description="固件版本号")
    firmware_url: Optional[str] = Field(None, description="固件下载URL")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    file_hash: Optional[str] = Field(None, description="文件SHA256哈希值")
    description: Optional[str] = Field(None, description="版本描述")
    release_notes: Optional[str] = Field(None, description="发布说明")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_latest: Optional[bool] = Field(None, description="是否为最新版本")

class FirmwareResponse(FirmwareBase):
    """固件响应模式"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OTACheckRequest(BaseModel):
    """OTA检测请求模式"""
    product_code: str = Field(..., description="产品代号")
    product_version: str = Field(..., description="产品版本")
    firmware_version: str = Field(..., description="当前固件版本")

class OTACheckResponse(BaseModel):
    """OTA检测响应模式"""
    has_update: bool = Field(..., description="是否有更新")
    firmware_url: Optional[str] = Field(None, description="固件下载URL")
    latest_version: Optional[str] = Field(None, description="最新版本号")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    file_hash: Optional[str] = Field(None, description="文件SHA256哈希值")
    description: Optional[str] = Field(None, description="版本描述")
    release_notes: Optional[str] = Field(None, description="发布说明")