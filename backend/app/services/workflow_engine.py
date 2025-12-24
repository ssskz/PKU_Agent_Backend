"""
工作流执行引擎服务
实现精简版的工作流执行引擎，支持串行执行
"""
import re
import logging
import json
import time
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.workflow import (
    Workflow, WorkflowExecution, WorkflowExecutionLog,
    ExecutionStatus, NodeType
)
from app.models.llm_model import LLMModel
from app.models.knowledge_base import KnowledgeBase, AgentKnowledgeBase
from app.models.document import Document, DocumentChunk
from app.services.llm_service import create_llm_service
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class WorkflowEngineError(Exception):
    """工作流引擎异常"""
    pass


class WorkflowValidator:
    """工作流验证器"""
    
    @staticmethod
    def validate(definition: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        验证工作流定义
        
        返回: (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        if not definition:
            errors.append("工作流定义不能为空")
            return False, errors, warnings
        
        nodes = definition.get("nodes", [])
        edges = definition.get("edges", [])
        
        if not nodes:
            errors.append("工作流必须至少包含一个节点")
            return False, errors, warnings
        
        # 检查是否有开始节点
        start_nodes = [n for n in nodes if n.get("type") == "start"]
        if len(start_nodes) == 0:
            errors.append("工作流必须有一个开始节点")
        elif len(start_nodes) > 1:
            errors.append("工作流只能有一个开始节点")
        
        # 检查是否有结束节点
        end_nodes = [n for n in nodes if n.get("type") == "end"]
        if len(end_nodes) == 0:
            warnings.append("建议添加结束节点")
        
        # 检查节点 ID 唯一性
        node_ids = [n.get("id") for n in nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("节点 ID 必须唯一")
        
        # 检查边的有效性
        node_id_set = set(node_ids)
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source not in node_id_set:
                errors.append(f"边的源节点 {source} 不存在")
            if target not in node_id_set:
                errors.append(f"边的目标节点 {target} 不存在")
        
        # 检查是否有环（DAG 验证）
        if not WorkflowValidator._is_dag(nodes, edges):
            errors.append("工作流不能包含循环依赖（必须是有向无环图）")
        
        # 检查是否所有节点都可达
        if start_nodes and not WorkflowValidator._all_reachable(nodes, edges, start_nodes[0].get("id")):
            warnings.append("存在无法从开始节点到达的节点")
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    @staticmethod
    def _is_dag(nodes: List[Dict], edges: List[Dict]) -> bool:
        """检查是否为有向无环图"""
        # 构建邻接表
        adj = {node.get("id"): [] for node in nodes}
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source in adj:
                adj[source].append(target)
        
        # 使用 DFS 检测环
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node in nodes:
            node_id = node.get("id")
            if node_id not in visited:
                if has_cycle(node_id):
                    return False
        
        return True
    
    @staticmethod
    def _all_reachable(nodes: List[Dict], edges: List[Dict], start_id: str) -> bool:
        """检查是否所有节点都可达"""
        # 构建邻接表
        adj = {node.get("id"): [] for node in nodes}
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source in adj:
                adj[source].append(target)
        
        # BFS 遍历
        visited = set()
        queue = [start_id]
        visited.add(start_id)
        
        while queue:
            current = queue.pop(0)
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return len(visited) == len(nodes)


class VariableReplacer:
    """变量替换器"""
    
    @staticmethod
    def replace(text: str, context: Dict[str, Any]) -> str:
        """
        替换文本中的变量
        支持格式: {{variable_name}} 或 {{node_id.output_field}}
        """
        if not isinstance(text, str):
            return text
        
        # 匹配 {{variable_name}} 模式
        pattern = r'\{\{([^}]+)\}\}'
        
        def replacer(match):
            var_path = match.group(1).strip()
            
            # 支持嵌套路径，如 node1.output.result
            value = context
            for key in var_path.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return match.group(0)  # 找不到变量，保持原样
            
            return str(value)
        
        return re.sub(pattern, replacer, text)
    
    @staticmethod
    def replace_dict(data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """递归替换字典中的所有变量"""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = VariableReplacer.replace(value, context)
            elif isinstance(value, dict):
                result[key] = VariableReplacer.replace_dict(value, context)
            elif isinstance(value, list):
                result[key] = [
                    VariableReplacer.replace(item, context) if isinstance(item, str)
                    else VariableReplacer.replace_dict(item, context) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result


class NodeExecutor:
    """节点执行器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def execute_node(
        self,
        node: Dict[str, Any],
        context: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """
        执行单个节点
        
        返回: 节点输出数据
        """
        node_type = node.get("type")
        node_id = node.get("id")
        node_data = node.get("data", {})
        
        logger.info(f"执行节点: {node_id}, 类型: {node_type}")
        
        try:
            if node_type == "start":
                return await self._execute_start_node(node, context, execution)
            elif node_type == "end":
                return await self._execute_end_node(node, context, execution)
            elif node_type == "llm":
                return await self._execute_llm_node(node, context, execution)
            elif node_type == "http":
                return await self._execute_http_node(node, context, execution)
            elif node_type == "knowledge":
                return await self._execute_knowledge_node(node, context, execution)
            elif node_type == "intent":
                return await self._execute_intent_node(node, context, execution)
            elif node_type == "string":
                return await self._execute_string_node(node, context, execution)
            else:
                raise WorkflowEngineError(f"不支持的节点类型: {node_type}")
        
        except Exception as e:
            logger.error(f"节点执行失败: {node_id}, 错误: {str(e)}")
            raise WorkflowEngineError(f"节点 {node_id} 执行失败: {str(e)}")
    
    async def _execute_start_node(
        self,
        node: Dict[str, Any],
        context: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """执行开始节点"""
        # 开始节点直接返回输入数据
        return context.get("input", {})
    
    async def _execute_end_node(
        self,
        node: Dict[str, Any],
        context: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """执行结束节点"""
        # 结束节点返回当前上下文
        return context
    
    async def _execute_llm_node(
        self,
        node: Dict[str, Any],
        context: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """执行 LLM 节点"""
        node_data = node.get("data", {})
        config = node_data.get("config", {})
        
        # 获取配置
        model_id = config.get("model_id")
        prompt = config.get("prompt", "")
        system_prompt = config.get("system_prompt", "")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)
        
        # 变量替换
        prompt = VariableReplacer.replace(prompt, context)
        system_prompt = VariableReplacer.replace(system_prompt, context)
        
        # 获取模型
        if not model_id:
            raise WorkflowEngineError("LLM 节点必须配置 model_id")
        
        model = self.db.query(LLMModel).filter(LLMModel.id == model_id).first()
        if not model:
            raise WorkflowEngineError(f"未找到模型 ID: {model_id}")
        
        # 调用 LLM
        llm_service = create_llm_service(model)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = llm_service.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 提取响应内容
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return {
            "content": content,
            "raw_response": response
        }
    
    async def _execute_http_node(
        self,
        node: Dict[str, Any],
        context: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """执行 HTTP 请求节点"""
        node_data = node.get("data", {})
        config = node_data.get("config", {})
        
        # 获取配置
        method = config.get("method", "GET").upper()
        url = config.get("url", "")
        headers = config.get("headers", {})
        body = config.get("body", {})
        timeout = config.get("timeout", 30)
        
        # 变量替换
        url = VariableReplacer.replace(url, context)
        headers = VariableReplacer.replace_dict(headers, context)
        body = VariableReplacer.replace_dict(body, context)
        
        if not url:
            raise WorkflowEngineError("HTTP 节点必须配置 URL")
        
        # 发送请求
        try:
            if method in ["GET", "DELETE"]:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=timeout
                )
            else:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body,
                    timeout=timeout
                )
            
            # 尝试解析 JSON 响应
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_data,
                "success": response.status_code < 400
            }
        
        except requests.RequestException as e:
            raise WorkflowEngineError(f"HTTP 请求失败: {str(e)}")
    
    async def _execute_knowledge_node(
        self,
        node: Dict[str, Any],
        context: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """
        执行知识库检索节点
        
        配置项:
        - knowledge_base_id: 知识库ID
        - query: 查询文本（支持变量替换）
        - top_k: 返回结果数量
        - similarity_threshold: 相似度阈值
        """
        node_data = node.get("data", {})
        config = node_data.get("config", {})
        
        # 获取配置
        knowledge_base_id = config.get("knowledge_base_id")
        query = config.get("query", "")
        top_k = config.get("top_k", 5)
        similarity_threshold = config.get("similarity_threshold", 0.7)
        
        # 变量替换
        query = VariableReplacer.replace(query, context)
        
        if not knowledge_base_id:
            raise WorkflowEngineError("知识库检索节点必须配置 knowledge_base_id")
        
        if not query:
            raise WorkflowEngineError("知识库检索节点必须配置查询内容")
        
        # 获取知识库
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if not kb:
            raise WorkflowEngineError(f"未找到知识库 ID: {knowledge_base_id}")
        
        # 对查询文本进行向量化
        embedding_service = get_embedding_service()
        query_vector = await embedding_service.embed_text(query)
        
        if not query_vector:
            raise WorkflowEngineError("查询文本向量化失败")
        
        # 获取该知识库的所有已向量化文本块
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.knowledge_base_id == kb.id,
            DocumentChunk.embedding_vector.isnot(None)
        ).all()
        
        # 计算相似度并筛选结果
        results = []
        for chunk in chunks:
            if chunk.embedding_vector:
                similarity = embedding_service.calculate_similarity(
                    query_vector,
                    chunk.embedding_vector
                )
                
                if similarity >= similarity_threshold:
                    doc = self.db.query(Document).filter(Document.id == chunk.document_id).first()
                    results.append({
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "document_title": doc.title if doc else "未知文档",
                        "content": chunk.content,
                        "similarity": round(similarity, 4),
                        "chunk_index": chunk.chunk_index
                    })
        
        # 按相似度排序并取top_k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = results[:top_k]
        
        # 构建知识库上下文字符串
        context_text = ""
        if top_results:
            context_parts = []
            for idx, result in enumerate(top_results, 1):
                context_parts.append(
                    f"[{idx}] 来自《{result['document_title']}》(相似度:{result['similarity']:.0%}):\n{result['content']}"
                )
            context_text = "\n\n".join(context_parts)
        
        return {
            "results": top_results,
            "count": len(top_results),
            "context_text": context_text,
            "query": query
        }
    
    async def _execute_intent_node(
        self,
        node: Dict[str, Any],
        context: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """
        执行意图识别节点
        
        配置项:
        - model_id: 用于意图识别的模型ID
        - input_text: 输入文本（支持变量替换）
        - intents: 预定义的意图列表 [{name, description, keywords}]
        """
        node_data = node.get("data", {})
        config = node_data.get("config", {})
        
        # 获取配置
        model_id = config.get("model_id")
        input_text = config.get("input_text", "")
        intents = config.get("intents", [])
        
        # 变量替换
        input_text = VariableReplacer.replace(input_text, context)
        
        if not model_id:
            raise WorkflowEngineError("意图识别节点必须配置 model_id")
        
        if not input_text:
            raise WorkflowEngineError("意图识别节点必须配置输入文本")
        
        if not intents:
            raise WorkflowEngineError("意图识别节点必须配置意图列表")
        
        # 获取模型
        model = self.db.query(LLMModel).filter(LLMModel.id == model_id).first()
        if not model:
            raise WorkflowEngineError(f"未找到模型 ID: {model_id}")
        
        # 构建意图识别提示词
        intent_descriptions = "\n".join([
            f"- {intent['name']}: {intent.get('description', '')} (关键词: {', '.join(intent.get('keywords', []))})"
            for intent in intents
        ])
        
        system_prompt = """你是一个意图识别助手。请根据用户输入，从给定的意图列表中识别出最匹配的意图。
只返回JSON格式的结果，包含以下字段：
- intent: 识别到的意图名称
- confidence: 置信度(0-1)
- reason: 简短的识别理由"""
        
        user_prompt = f"""可选的意图列表：
{intent_descriptions}

用户输入：
{input_text}

请识别用户的意图，返回JSON格式："""
        
        # 调用 LLM
        llm_service = create_llm_service(model)
        
        response = llm_service.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # 低温度以获得更稳定的结果
            max_tokens=500
        )
        
        # 提取响应内容
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 尝试解析JSON
        try:
            # 尝试从响应中提取JSON
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {
                    "intent": "unknown",
                    "confidence": 0,
                    "reason": "无法解析响应"
                }
        except json.JSONDecodeError:
            result = {
                "intent": "unknown",
                "confidence": 0,
                "reason": "JSON解析失败",
                "raw_response": content
            }
        
        return {
            "intent": result.get("intent", "unknown"),
            "confidence": result.get("confidence", 0),
            "reason": result.get("reason", ""),
            "input_text": input_text,
            "raw_response": content
        }
    
    async def _execute_string_node(
        self,
        node: Dict[str, Any],
        context: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """
        执行字符串处理节点
        
        配置项:
        - operation: 操作类型 (concat, replace, split, extract, format, upper, lower, trim, length)
        - input_text: 输入文本（支持变量替换）
        - 其他参数根据操作类型不同而不同
        """
        node_data = node.get("data", {})
        config = node_data.get("config", {})
        
        # 获取配置
        operation = config.get("operation", "concat")
        input_text = config.get("input_text", "")
        
        # 变量替换
        input_text = VariableReplacer.replace(input_text, context)
        
        result = ""
        
        if operation == "concat":
            # 字符串拼接
            texts = config.get("texts", [])
            separator = config.get("separator", "")
            processed_texts = [VariableReplacer.replace(t, context) for t in texts]
            result = separator.join(processed_texts)
            
        elif operation == "replace":
            # 字符串替换
            search = config.get("search", "")
            replace_with = config.get("replace_with", "")
            search = VariableReplacer.replace(search, context)
            replace_with = VariableReplacer.replace(replace_with, context)
            result = input_text.replace(search, replace_with)
            
        elif operation == "split":
            # 字符串分割
            delimiter = config.get("delimiter", ",")
            result = input_text.split(delimiter)
            
        elif operation == "extract":
            # 正则提取
            pattern = config.get("pattern", "")
            matches = re.findall(pattern, input_text)
            result = matches
            
        elif operation == "format":
            # 格式化模板
            template = config.get("template", "")
            template = VariableReplacer.replace(template, context)
            result = template
            
        elif operation == "upper":
            # 转大写
            result = input_text.upper()
            
        elif operation == "lower":
            # 转小写
            result = input_text.lower()
            
        elif operation == "trim":
            # 去除首尾空白
            result = input_text.strip()
            
        elif operation == "length":
            # 获取长度
            result = len(input_text)
            
        elif operation == "substring":
            # 截取子字符串
            start = config.get("start", 0)
            end = config.get("end", None)
            result = input_text[start:end]
            
        elif operation == "json_extract":
            # 从JSON字符串中提取字段
            json_path = config.get("json_path", "")
            try:
                data = json.loads(input_text)
                for key in json_path.split('.'):
                    if isinstance(data, dict) and key in data:
                        data = data[key]
                    elif isinstance(data, list) and key.isdigit():
                        data = data[int(key)]
                    else:
                        data = None
                        break
                result = data
            except json.JSONDecodeError:
                result = None
        else:
            raise WorkflowEngineError(f"不支持的字符串操作: {operation}")
        
        return {
            "result": result,
            "operation": operation,
            "input_text": input_text
        }


class WorkflowEngine:
    """工作流执行引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.executor = NodeExecutor(db)
    
    def validate_workflow(self, workflow: Workflow) -> Tuple[bool, List[str], List[str]]:
        """验证工作流"""
        if not workflow.definition:
            return False, ["工作流定义为空"], []
        
        return WorkflowValidator.validate(workflow.definition)
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        返回: 输出数据
        """
        # 验证工作流
        is_valid, errors, warnings = self.validate_workflow(workflow)
        if not is_valid:
            raise WorkflowEngineError(f"工作流验证失败: {', '.join(errors)}")
        
        # 初始化执行上下文
        context = {
            "input": input_data,
            "nodes": {}  # 存储每个节点的输出
        }
        
        # 更新执行状态
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.utcnow()
        execution.context = context
        self.db.commit()
        
        try:
            # 获取节点和边
            definition = workflow.definition
            nodes = definition.get("nodes", [])
            edges = definition.get("edges", [])
            
            # 构建执行顺序（拓扑排序）
            execution_order = self._topological_sort(nodes, edges)
            
            # 按顺序执行节点
            for node_id in execution_order:
                node = next((n for n in nodes if n.get("id") == node_id), None)
                if not node:
                    continue
                
                # 记录节点开始执行
                start_time = time.time()
                self._log_execution(
                    execution,
                    node_id,
                    node.get("data", {}).get("label", node_id),
                    node.get("type"),
                    "INFO",
                    f"开始执行节点: {node_id}"
                )
                
                try:
                    # 执行节点
                    output = await self.executor.execute_node(node, context, execution)
                    
                    # 保存节点输出到上下文
                    context["nodes"][node_id] = output
                    
                    # 记录节点执行成功
                    duration_ms = int((time.time() - start_time) * 1000)
                    self._log_execution(
                        execution,
                        node_id,
                        node.get("data", {}).get("label", node_id),
                        node.get("type"),
                        "INFO",
                        f"节点执行成功",
                        input_data=None,
                        output_data=output,
                        duration_ms=duration_ms
                    )
                
                except Exception as e:
                    # 记录节点执行失败
                    duration_ms = int((time.time() - start_time) * 1000)
                    self._log_execution(
                        execution,
                        node_id,
                        node.get("data", {}).get("label", node_id),
                        node.get("type"),
                        "ERROR",
                        f"节点执行失败: {str(e)}",
                        duration_ms=duration_ms
                    )
                    raise
            
            # 执行成功
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
            execution.context = context
            execution.output_data = context.get("nodes", {})
            
            # 更新工作流统计
            workflow.execution_count += 1
            workflow.success_count += 1
            
            self.db.commit()
            
            return execution.output_data
        
        except Exception as e:
            # 执行失败
            execution.status = ExecutionStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
            execution.error_message = str(e)
            execution.context = context
            
            # 更新工作流统计
            workflow.execution_count += 1
            
            self.db.commit()
            
            raise WorkflowEngineError(f"工作流执行失败: {str(e)}")
    
    def _topological_sort(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """拓扑排序，返回节点执行顺序"""
        # 构建邻接表和入度表
        adj = {node.get("id"): [] for node in nodes}
        in_degree = {node.get("id"): 0 for node in nodes}
        
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source in adj and target in in_degree:
                adj[source].append(target)
                in_degree[target] += 1
        
        # Kahn 算法
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in adj.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def _log_execution(
        self,
        execution: WorkflowExecution,
        node_id: str,
        node_name: Optional[str],
        node_type: Optional[str],
        level: str,
        message: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None
    ):
        """记录执行日志"""
        log = WorkflowExecutionLog(
            execution_id=execution.id,
            node_id=node_id,
            node_name=node_name,
            node_type=node_type,
            level=level,
            message=message,
            input_data=input_data,
            output_data=output_data,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms
        )
        self.db.add(log)
        self.db.commit()
