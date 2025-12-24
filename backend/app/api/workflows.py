"""
工作流管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
import logging

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.workflow import (
    Workflow, WorkflowExecution, WorkflowExecutionLog,
    WorkflowStatus, ExecutionStatus
)
from app.models.agent import Agent
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowListResponse,
    WorkflowExecuteRequest, WorkflowExecutionResponse, WorkflowExecutionListResponse,
    WorkflowExecutionLogResponse, WorkflowValidationResult, WorkflowStatistics
)
from app.services.workflow_engine import WorkflowEngine, WorkflowEngineError

logger = logging.getLogger(__name__)

router = APIRouter()


def check_workflow_permission(workflow: Workflow, user: User, require_owner: bool = False) -> bool:
    """检查工作流权限"""
    # 平台管理员有所有权限
    if user.role == "platform_admin":
        return True
    
    # 检查是否是所有者
    if workflow.user_id == user.id:
        return True
    
    # 如果需要所有者权限，其他情况返回 False
    if require_owner:
        return False
    
    # 已发布的工作流可以被所有人查看
    if workflow.status == WorkflowStatus.PUBLISHED:
        return True
    
    return False


# ==================== 工作流 CRUD ====================

@router.post("/", response_model=WorkflowResponse, summary="创建工作流")
def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新的工作流"""
    # 如果指定了 agent_id，检查 agent 是否存在且有权限
    if workflow_data.agent_id:
        agent = db.query(Agent).filter(Agent.id == workflow_data.agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="关联的智能体不存在")
        
        # 检查是否有权限关联该智能体
        if agent.user_id != current_user.id and current_user.role != "platform_admin":
            raise HTTPException(status_code=403, detail="无权关联该智能体")
    
    # 创建工作流
    workflow = Workflow(
        uuid=str(uuid.uuid4()),
        name=workflow_data.name,
        description=workflow_data.description,
        agent_id=workflow_data.agent_id,
        user_id=current_user.id,
        definition=workflow_data.definition.model_dump() if workflow_data.definition else None,
        status=WorkflowStatus.DRAFT,
        version=1
    )
    
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    logger.info(f"用户 {current_user.id} 创建工作流: {workflow.uuid}")
    
    return workflow


@router.get("/", response_model=WorkflowListResponse, summary="获取工作流列表")
def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[WorkflowStatus] = None,
    agent_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取工作流列表"""
    query = db.query(Workflow)
    
    # 根据角色过滤
    if current_user.role != "platform_admin":
        # 非管理员只能看到自己的工作流和已发布的工作流
        query = query.filter(
            (Workflow.user_id == current_user.id) | 
            (Workflow.status == WorkflowStatus.PUBLISHED)
        )
    
    # 状态过滤
    if status:
        query = query.filter(Workflow.status == status)
    
    # 智能体过滤
    if agent_id:
        query = query.filter(Workflow.agent_id == agent_id)
    
    # 搜索
    if search:
        query = query.filter(
            (Workflow.name.contains(search)) |
            (Workflow.description.contains(search))
        )
    
    # 总数
    total = query.count()
    
    # 分页
    workflows = query.order_by(Workflow.updated_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": workflows
    }


@router.get("/{workflow_uuid}", response_model=WorkflowResponse, summary="获取工作流详情")
def get_workflow(
    workflow_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取工作流详情"""
    workflow = db.query(Workflow).filter(Workflow.uuid == workflow_uuid).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if not check_workflow_permission(workflow, current_user):
        raise HTTPException(status_code=403, detail="无权访问该工作流")
    
    return workflow


@router.put("/{workflow_uuid}", response_model=WorkflowResponse, summary="更新工作流")
def update_workflow(
    workflow_uuid: str,
    workflow_data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新工作流"""
    workflow = db.query(Workflow).filter(Workflow.uuid == workflow_uuid).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限（需要所有者权限）
    if not check_workflow_permission(workflow, current_user, require_owner=True):
        raise HTTPException(status_code=403, detail="无权修改该工作流")
    
    # 更新字段
    if workflow_data.name is not None:
        workflow.name = workflow_data.name
    
    if workflow_data.description is not None:
        workflow.description = workflow_data.description
    
    if workflow_data.agent_id is not None:
        # 检查 agent 是否存在且有权限
        if workflow_data.agent_id != 0:  # 0 表示取消关联
            agent = db.query(Agent).filter(Agent.id == workflow_data.agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail="关联的智能体不存在")
            
            if agent.user_id != current_user.id and current_user.role != "platform_admin":
                raise HTTPException(status_code=403, detail="无权关联该智能体")
        
        workflow.agent_id = workflow_data.agent_id if workflow_data.agent_id != 0 else None
    
    if workflow_data.definition is not None:
        workflow.definition = workflow_data.definition.model_dump()
        # 更新定义时增加版本号
        workflow.version += 1
    
    if workflow_data.status is not None:
        workflow.status = workflow_data.status
    
    db.commit()
    db.refresh(workflow)
    
    logger.info(f"用户 {current_user.id} 更新工作流: {workflow.uuid}")
    
    return workflow


@router.delete("/{workflow_uuid}", summary="删除工作流")
def delete_workflow(
    workflow_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除工作流"""
    workflow = db.query(Workflow).filter(Workflow.uuid == workflow_uuid).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限（需要所有者权限）
    if not check_workflow_permission(workflow, current_user, require_owner=True):
        raise HTTPException(status_code=403, detail="无权删除该工作流")
    
    db.delete(workflow)
    db.commit()
    
    logger.info(f"用户 {current_user.id} 删除工作流: {workflow.uuid}")
    
    return {"message": "工作流已删除"}


@router.post("/{workflow_uuid}/validate", response_model=WorkflowValidationResult, summary="验证工作流")
def validate_workflow(
    workflow_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """验证工作流定义"""
    workflow = db.query(Workflow).filter(Workflow.uuid == workflow_uuid).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if not check_workflow_permission(workflow, current_user):
        raise HTTPException(status_code=403, detail="无权访问该工作流")
    
    # 验证工作流
    engine = WorkflowEngine(db)
    is_valid, errors, warnings = engine.validate_workflow(workflow)
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings
    }


# ==================== 工作流执行 ====================

@router.post("/{workflow_uuid}/execute", response_model=WorkflowExecutionResponse, summary="执行工作流")
async def execute_workflow(
    workflow_uuid: str,
    execute_request: WorkflowExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行工作流"""
    workflow = db.query(Workflow).filter(Workflow.uuid == workflow_uuid).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if not check_workflow_permission(workflow, current_user):
        raise HTTPException(status_code=403, detail="无权执行该工作流")
    
    # 检查工作流状态
    if workflow.status == WorkflowStatus.ARCHIVED:
        raise HTTPException(status_code=400, detail="已归档的工作流无法执行")
    
    # 创建执行记录
    execution = WorkflowExecution(
        uuid=str(uuid.uuid4()),
        workflow_id=workflow.id,
        workflow_uuid=workflow.uuid,
        workflow_version=workflow.version,
        user_id=current_user.id,
        status=ExecutionStatus.PENDING,
        input_data=execute_request.input_data
    )
    
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    logger.info(f"用户 {current_user.id} 执行工作流: {workflow.uuid}, 执行ID: {execution.uuid}")
    
    # 执行工作流
    try:
        engine = WorkflowEngine(db)
        output_data = await engine.execute_workflow(
            workflow,
            execution,
            execute_request.input_data or {}
        )
        
        # 刷新执行记录
        db.refresh(execution)
        
        return execution
    
    except WorkflowEngineError as e:
        logger.error(f"工作流执行失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"工作流执行异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {str(e)}")


@router.get("/{workflow_uuid}/executions", response_model=WorkflowExecutionListResponse, summary="获取工作流执行历史")
def list_workflow_executions(
    workflow_uuid: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ExecutionStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取工作流执行历史"""
    workflow = db.query(Workflow).filter(Workflow.uuid == workflow_uuid).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if not check_workflow_permission(workflow, current_user):
        raise HTTPException(status_code=403, detail="无权访问该工作流")
    
    query = db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == workflow.id)
    
    # 状态过滤
    if status:
        query = query.filter(WorkflowExecution.status == status)
    
    # 总数
    total = query.count()
    
    # 分页
    executions = query.order_by(WorkflowExecution.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": executions
    }


@router.get("/executions/{execution_uuid}", response_model=WorkflowExecutionResponse, summary="获取执行详情")
def get_execution(
    execution_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取执行详情"""
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.uuid == execution_uuid).first()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    # 检查权限
    workflow = execution.workflow
    if not check_workflow_permission(workflow, current_user):
        raise HTTPException(status_code=403, detail="无权访问该执行记录")
    
    return execution


@router.get("/executions/{execution_uuid}/logs", response_model=List[WorkflowExecutionLogResponse], summary="获取执行日志")
def get_execution_logs(
    execution_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取执行日志"""
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.uuid == execution_uuid).first()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    # 检查权限
    workflow = execution.workflow
    if not check_workflow_permission(workflow, current_user):
        raise HTTPException(status_code=403, detail="无权访问该执行记录")
    
    logs = db.query(WorkflowExecutionLog).filter(
        WorkflowExecutionLog.execution_id == execution.id
    ).order_by(WorkflowExecutionLog.timestamp).all()
    
    return logs


# ==================== 统计信息 ====================

@router.get("/statistics/overview", response_model=WorkflowStatistics, summary="获取工作流统计信息")
def get_workflow_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取工作流统计信息"""
    # 根据角色过滤
    workflow_query = db.query(Workflow)
    execution_query = db.query(WorkflowExecution)
    
    if current_user.role != "platform_admin":
        workflow_query = workflow_query.filter(Workflow.user_id == current_user.id)
        execution_query = execution_query.join(Workflow).filter(Workflow.user_id == current_user.id)
    
    # 工作流统计
    total_workflows = workflow_query.count()
    draft_workflows = workflow_query.filter(Workflow.status == WorkflowStatus.DRAFT).count()
    published_workflows = workflow_query.filter(Workflow.status == WorkflowStatus.PUBLISHED).count()
    
    # 执行统计
    total_executions = execution_query.count()
    successful_executions = execution_query.filter(WorkflowExecution.status == ExecutionStatus.COMPLETED).count()
    failed_executions = execution_query.filter(WorkflowExecution.status == ExecutionStatus.FAILED).count()
    
    # 平均执行时长
    avg_duration = db.query(func.avg(WorkflowExecution.duration_seconds)).filter(
        WorkflowExecution.status == ExecutionStatus.COMPLETED
    ).scalar()
    
    if current_user.role != "platform_admin":
        avg_duration = db.query(func.avg(WorkflowExecution.duration_seconds)).join(Workflow).filter(
            Workflow.user_id == current_user.id,
            WorkflowExecution.status == ExecutionStatus.COMPLETED
        ).scalar()
    
    return {
        "total_workflows": total_workflows,
        "draft_workflows": draft_workflows,
        "published_workflows": published_workflows,
        "total_executions": total_executions,
        "successful_executions": successful_executions,
        "failed_executions": failed_executions,
        "average_duration_seconds": float(avg_duration) if avg_duration else None
    }
