"""
工作流相关数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class WorkflowStatus(str, enum.Enum):
    """工作流状态"""
    DRAFT = "DRAFT"  # 草稿
    PUBLISHED = "PUBLISHED"  # 已发布
    ARCHIVED = "ARCHIVED"  # 已归档


class ExecutionStatus(str, enum.Enum):
    """执行状态"""
    PENDING = "PENDING"  # 等待执行
    RUNNING = "RUNNING"  # 执行中
    COMPLETED = "COMPLETED"  # 执行完成
    FAILED = "FAILED"  # 执行失败
    CANCELLED = "CANCELLED"  # 已取消


class NodeType(str, enum.Enum):
    """节点类型"""
    START = "start"  # 开始节点
    END = "end"  # 结束节点
    LLM = "llm"  # LLM 调用节点
    HTTP = "http"  # HTTP 请求节点
    KNOWLEDGE = "knowledge"  # 知识库检索节点
    INTENT = "intent"  # 意图识别节点
    STRING = "string"  # 字符串处理节点
    CONDITION = "condition"  # 条件分支节点（预留）
    CODE = "code"  # 代码节点（预留）


class Workflow(Base):
    """工作流表"""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, comment="工作流UUID")
    name = Column(String(255), nullable=False, comment="工作流名称")
    description = Column(Text, nullable=True, comment="工作流描述")
    
    # 所属关系
    agent_id = Column(Integer, ForeignKey("aiot_agents.id", ondelete="CASCADE"), nullable=True, comment="关联的智能体ID")
    user_id = Column(Integer, ForeignKey("aiot_core_users.id", ondelete="CASCADE"), nullable=False, comment="创建者ID")
    
    # 工作流定义（JSON 格式）
    definition = Column(JSON, nullable=True, comment="工作流定义（节点和边）")
    
    # 状态
    status = Column(
        Enum(WorkflowStatus),
        default=WorkflowStatus.DRAFT,
        nullable=False,
        comment="工作流状态"
    )
    
    # 版本信息
    version = Column(Integer, default=1, nullable=False, comment="版本号")
    
    # 统计信息
    execution_count = Column(Integer, default=0, comment="执行次数")
    success_count = Column(Integer, default=0, comment="成功次数")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # 关系
    agent = relationship("Agent", back_populates="workflows")
    user = relationship("User")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workflow(uuid={self.uuid}, name={self.name}, status={self.status})>"


class WorkflowExecution(Base):
    """工作流执行记录表"""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, comment="执行UUID")
    
    # 关联工作流
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, comment="工作流ID")
    workflow_uuid = Column(String(36), nullable=False, comment="工作流UUID快照")
    workflow_version = Column(Integer, nullable=False, comment="工作流版本快照")
    
    # 执行者
    user_id = Column(Integer, ForeignKey("aiot_core_users.id", ondelete="CASCADE"), nullable=False, comment="执行者ID")
    
    # 执行状态
    status = Column(
        Enum(ExecutionStatus),
        default=ExecutionStatus.PENDING,
        nullable=False,
        comment="执行状态"
    )
    
    # 输入输出
    input_data = Column(JSON, nullable=True, comment="输入数据")
    output_data = Column(JSON, nullable=True, comment="输出数据")
    
    # 执行上下文（用于存储中间结果）
    context = Column(JSON, nullable=True, comment="执行上下文")
    
    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")
    error_node_id = Column(String(100), nullable=True, comment="出错节点ID")
    
    # 时间统计
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    duration_seconds = Column(Integer, nullable=True, comment="执行时长（秒）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # 关系
    workflow = relationship("Workflow", back_populates="executions")
    user = relationship("User")
    logs = relationship("WorkflowExecutionLog", back_populates="execution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WorkflowExecution(uuid={self.uuid}, status={self.status})>"


class WorkflowExecutionLog(Base):
    """工作流执行日志表"""
    __tablename__ = "workflow_execution_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 关联执行记录
    execution_id = Column(Integer, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, comment="执行记录ID")
    
    # 节点信息
    node_id = Column(String(100), nullable=False, comment="节点ID")
    node_name = Column(String(255), nullable=True, comment="节点名称")
    node_type = Column(String(50), nullable=True, comment="节点类型")
    
    # 日志级别
    level = Column(String(20), default="INFO", comment="日志级别: DEBUG, INFO, WARNING, ERROR")
    
    # 日志内容
    message = Column(Text, nullable=False, comment="日志消息")
    
    # 节点执行详情
    input_data = Column(JSON, nullable=True, comment="节点输入")
    output_data = Column(JSON, nullable=True, comment="节点输出")
    
    # 时间信息
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment="日志时间")
    duration_ms = Column(Integer, nullable=True, comment="节点执行时长（毫秒）")
    
    # 关系
    execution = relationship("WorkflowExecution", back_populates="logs")

    def __repr__(self):
        return f"<WorkflowExecutionLog(node_id={self.node_id}, level={self.level})>"
