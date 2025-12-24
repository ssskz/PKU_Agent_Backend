"""
工作流相关的 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class WorkflowStatusEnum(str, Enum):
    """工作流状态枚举"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class ExecutionStatusEnum(str, Enum):
    """执行状态枚举"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class NodeTypeEnum(str, Enum):
    """节点类型枚举"""
    START = "start"
    END = "end"
    LLM = "llm"
    HTTP = "http"
    KNOWLEDGE = "knowledge"
    INTENT = "intent"
    STRING = "string"
    CONDITION = "condition"
    CODE = "code"


# ==================== 工作流定义相关 ====================

class NodePosition(BaseModel):
    """节点位置"""
    x: float
    y: float


class NodeData(BaseModel):
    """节点数据"""
    label: Optional[str] = None
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WorkflowNode(BaseModel):
    """工作流节点"""
    id: str
    type: NodeTypeEnum
    position: NodePosition
    data: NodeData


class WorkflowEdge(BaseModel):
    """工作流边（连接）"""
    id: str
    source: str
    target: str
    label: Optional[str] = None


class WorkflowDefinition(BaseModel):
    """工作流定义"""
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)


# ==================== 工作流 CRUD Schema ====================

class WorkflowCreate(BaseModel):
    """创建工作流"""
    name: str = Field(..., min_length=1, max_length=255, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    agent_id: Optional[int] = Field(None, description="关联的智能体ID")
    definition: Optional[WorkflowDefinition] = Field(None, description="工作流定义")


class WorkflowUpdate(BaseModel):
    """更新工作流"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    agent_id: Optional[int] = Field(None, description="关联的智能体ID")
    definition: Optional[WorkflowDefinition] = Field(None, description="工作流定义")
    status: Optional[WorkflowStatusEnum] = Field(None, description="工作流状态")


class WorkflowResponse(BaseModel):
    """工作流响应"""
    id: int
    uuid: str
    name: str
    description: Optional[str]
    agent_id: Optional[int]
    user_id: int
    definition: Optional[Dict[str, Any]]
    status: WorkflowStatusEnum
    version: int
    execution_count: int
    success_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    total: int
    items: List[WorkflowResponse]


# ==================== 工作流执行相关 ====================

class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="输入数据")


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    id: int
    uuid: str
    workflow_id: int
    workflow_uuid: str
    workflow_version: int
    user_id: int
    status: ExecutionStatusEnum
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    context: Optional[Dict[str, Any]]
    error_message: Optional[str]
    error_node_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowExecutionListResponse(BaseModel):
    """工作流执行列表响应"""
    total: int
    items: List[WorkflowExecutionResponse]


# ==================== 工作流执行日志 ====================

class WorkflowExecutionLogResponse(BaseModel):
    """工作流执行日志响应"""
    id: int
    execution_id: int
    node_id: str
    node_name: Optional[str]
    node_type: Optional[str]
    level: str
    message: str
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    timestamp: datetime
    duration_ms: Optional[int]
    
    class Config:
        from_attributes = True


# ==================== 工作流验证 ====================

class WorkflowValidationResult(BaseModel):
    """工作流验证结果"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ==================== 工作流统计 ====================

class WorkflowStatistics(BaseModel):
    """工作流统计信息"""
    total_workflows: int
    draft_workflows: int
    published_workflows: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_duration_seconds: Optional[float]
