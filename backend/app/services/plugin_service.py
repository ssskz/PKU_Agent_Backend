"""
插件解析和调用服务
将 OpenAPI 规范转换为 Function Calling 格式
"""

import json
import requests
from typing import List, Dict, Any, Optional
from app.models.plugin import Plugin


class PluginService:
    """插件服务"""
    
    @staticmethod
    def parse_openapi_to_functions(plugins: List[Plugin]) -> List[Dict[str, Any]]:
        """
        将插件的 OpenAPI 规范转换为 Function Calling 格式
        
        Args:
            plugins: 插件列表
        
        Returns:
            函数定义列表
        """
        functions = []
        
        for plugin in plugins:
            if not plugin.openapi_spec:
                continue
            
            spec = plugin.openapi_spec
            paths = spec.get("paths", {})
            servers = spec.get("servers", [])
            base_url = servers[0]["url"] if servers else ""
            
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                        continue
                    
                    function = {
                        "name": details.get("operationId", f"{method}_{path.replace('/', '_')}"),
                        "description": details.get("summary") or details.get("description", ""),
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        },
                        "metadata": {
                            "plugin_id": plugin.id,
                            "plugin_name": plugin.name,
                            "method": method.upper(),
                            "path": path,
                            "base_url": base_url
                        }
                    }
                    
                    # 解析路径参数
                    if "parameters" in details:
                        for param in details["parameters"]:
                            if param["in"] == "path" or param["in"] == "query":
                                param_schema = param.get("schema", {})
                                function["parameters"]["properties"][param["name"]] = {
                                    "type": param_schema.get("type", "string"),
                                    "description": param.get("description", "")
                                }
                                if param.get("required"):
                                    function["parameters"]["required"].append(param["name"])
                    
                    # 解析请求体参数
                    if "requestBody" in details:
                        request_body = details["requestBody"]
                        content = request_body.get("content", {})
                        if "application/json" in content:
                            schema = content["application/json"].get("schema", {})
                            if "properties" in schema:
                                for prop_name, prop_schema in schema["properties"].items():
                                    function["parameters"]["properties"][prop_name] = {
                                        "type": prop_schema.get("type", "string"),
                                        "description": prop_schema.get("description", "")
                                    }
                                    if prop_name in schema.get("required", []):
                                        function["parameters"]["required"].append(prop_name)
                    
                    functions.append(function)
        
        return functions
    
    @staticmethod
    def call_function(
        function_name: str,
        arguments: Dict[str, Any],
        functions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        调用插件函数
        
        Args:
            function_name: 函数名称
            arguments: 函数参数
            functions: 函数定义列表
        
        Returns:
            函数调用结果
        """
        # 查找函数定义
        function_def = None
        for func in functions:
            if func["name"] == function_name:
                function_def = func
                break
        
        if not function_def:
            return {"error": f"函数 {function_name} 不存在"}
        
        metadata = function_def["metadata"]
        method = metadata["method"]
        path = metadata["path"]
        base_url = metadata["base_url"]
        
        # 构建完整 URL
        url = f"{base_url}{path}"
        
        # 替换路径参数
        for key, value in arguments.items():
            placeholder = f"{{{key}}}"
            if placeholder in url:
                url = url.replace(placeholder, str(value))
        
        # 分离路径参数和请求体参数
        path_params = {}
        query_params = {}
        body_params = {}
        
        for key, value in arguments.items():
            if f"{{{key}}}" in path:
                path_params[key] = value
            elif method in ["GET", "DELETE"]:
                query_params[key] = value
            else:
                body_params[key] = value
        
        try:
            # 增强日志输出
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🔌 [插件调用] 开始执行")
            logger.info(f"  函数名: {function_name}")
            logger.info(f"  方法: {method}")
            logger.info(f"  完整URL: {url}")
            logger.info(f"  Query参数: {json.dumps(query_params, ensure_ascii=False)}")
            logger.info(f"  Body参数: {json.dumps(body_params, ensure_ascii=False)}")
            
            # 发送请求
            if method == "GET":
                logger.info(f"  发送GET请求...")
                response = requests.get(url, params=query_params, timeout=30)
            elif method == "POST":
                logger.info(f"  发送POST请求...")
                response = requests.post(url, json=body_params, timeout=30)
            elif method == "PUT":
                logger.info(f"  发送PUT请求...")
                response = requests.put(url, json=body_params, timeout=30)
            elif method == "DELETE":
                logger.info(f"  发送DELETE请求...")
                response = requests.delete(url, params=query_params, timeout=30)
            elif method == "PATCH":
                logger.info(f"  发送PATCH请求...")
                response = requests.patch(url, json=body_params, timeout=30)
            else:
                return {"error": f"不支持的 HTTP 方法: {method}"}
            
            logger.info(f"  响应状态码: {response.status_code}")
            logger.info(f"  响应内容: {response.text[:500]}")
            
            response.raise_for_status()
            
            # 返回结果
            try:
                return {
                    "success": True,
                    "data": response.json(),
                    "status_code": response.status_code
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "data": response.text,
                    "status_code": response.status_code
                }
        
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def format_function_result(result: Dict[str, Any]) -> str:
        """
        格式化函数调用结果为文本
        
        Args:
            result: 函数调用结果
        
        Returns:
            格式化后的文本
        """
        if not result.get("success"):
            return f"调用失败: {result.get('error', '未知错误')}"
        
        data = result.get("data")
        if isinstance(data, dict):
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif isinstance(data, str):
            return data
        else:
            return str(data)


def create_plugin_service() -> PluginService:
    """创建插件服务实例"""
    return PluginService()
