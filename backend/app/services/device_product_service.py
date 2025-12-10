"""
设备产品动态绑定服务
处理设备产品信息上报、自动匹配和切换逻辑
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_now():
    """获取当前北京时间（不带时区信息，用于存储到数据库）"""
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)

from app.models.device import Device, DeviceStatus
from app.models.product import Product
from app.schemas.device import DeviceProductReport, DeviceProductSwitch
import logging

logger = logging.getLogger(__name__)


class DeviceProductService:
    """设备产品绑定服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_matching_product(self, product_code: str, product_version: str) -> Optional[Product]:
        """
        查找匹配的产品
        1. 精确匹配：产品代码 + 版本
        2. 代码匹配：仅产品代码，取最新版本
        """
        # 1. 精确匹配
        product = self.db.query(Product).filter(
            and_(
                Product.product_code == product_code,
                Product.version == product_version
            )
        ).first()
        
        if product:
            logger.info(f"找到精确匹配的产品: {product.name} (ID: {product.id})")
            return product
        
        # 2. 代码匹配，取最新版本
        product = self.db.query(Product).filter(
            Product.product_code == product_code
        ).order_by(Product.version.desc()).first()
        
        if product:
            logger.info(f"找到代码匹配的产品: {product.name} (ID: {product.id}), 版本: {product.version}")
            return product
        
        logger.info(f"未找到匹配的产品: {product_code} v{product_version}")
        return None
    
    def auto_create_product(self, product_code: str, product_version: str, 
                          capabilities: Optional[Dict[str, Any]] = None) -> Product:
        """
        自动创建产品
        """
        try:
            # 解析能力信息
            sensor_config = {}
            control_config = {}
            
            if capabilities:
                sensors = capabilities.get("sensors", [])
                actuators = capabilities.get("actuators", [])
                
                # 构建传感器配置
                for sensor in sensors:
                    sensor_config[sensor] = {
                        "enabled": True,
                        "unit": self._get_default_unit(sensor),
                        "min_value": 0,
                        "max_value": 100
                    }
                
                # 构建控制器配置
                for actuator in actuators:
                    control_config[actuator] = {
                        "enabled": True,
                        "type": self._get_actuator_type(actuator)
                    }
            
            # 创建新产品
            new_product = Product(
                name=f"自动创建-{product_code}",
                product_code=product_code,
                version=product_version,
                category="auto_generated",
                description=f"根据设备 {product_code} v{product_version} 自动创建的产品",
                sensor_types=sensor_config,
                control_ports=control_config,
                is_active=True
            )
            
            self.db.add(new_product)
            self.db.commit()
            self.db.refresh(new_product)
            
            logger.info(f"自动创建产品成功: {new_product.name} (ID: {new_product.id})")
            return new_product
            
        except Exception as e:
            logger.error(f"自动创建产品失败: {e}")
            self.db.rollback()
            raise
    
    def bind_device_to_product(self, device: Device, product: Product, 
                             product_code: str, product_version: str,
                             is_auto_created: bool = False) -> Device:
        """
        绑定设备到产品
        """
        try:
            # 记录产品切换历史（如果之前有产品）
            if device.product_id and device.product_id != product.id:
                self._record_product_switch(device, device.product_id, product.id, 
                                          device.product_code, product_code, "auto_report")
                device.product_switch_count = (device.product_switch_count or 0) + 1
            
            # 更新设备信息
            device.product_id = product.id
            device.product_code = product_code
            device.product_version = product_version
            device.last_product_report = get_beijing_now()
            device.auto_created_product = is_auto_created
            device.device_status = DeviceStatus.BOUND
            
            self.db.commit()
            self.db.refresh(device)
            
            logger.info(f"设备 {device.uuid} 成功绑定到产品 {product.name}")
            return device
            
        except Exception as e:
            logger.error(f"绑定设备到产品失败: {e}")
            self.db.rollback()
            raise
    
    def handle_product_report(self, device: Device, product_code: str, product_version: str,
                            device_capabilities: Optional[Dict[str, Any]] = None,
                            sensor_config: Optional[Dict[str, Any]] = None,
                            control_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理设备产品信息上报
        """
        try:
            # 1. 查找匹配的产品
            product = self.find_matching_product(product_code, product_version)
            
            # 2. 判断是否需要切换产品
            is_product_switch = (device.product_id is not None and 
                               device.product_code != product_code)
            
            binding_type = "existing"
            
            # 3. 如果没有找到产品，自动创建
            if not product:
                product = self.auto_create_product(
                    product_code, product_version, device_capabilities
                )
                binding_type = "auto_created"
            elif is_product_switch:
                binding_type = "switched"
            
            # 4. 如果是产品切换，记录历史
            if is_product_switch:
                self._record_product_switch(
                    device, device.product_id, product.id,
                    device.product_code, product_code, "设备上报新产品信息"
                )
            
            # 5. 绑定设备到产品
            device = self.bind_device_to_product(
                device, product, product_code, product_version, 
                binding_type == "auto_created"
            )
            
            # 6. 更新设备配置信息
            if device_capabilities:
                device.device_capabilities = device_capabilities
            if sensor_config:
                device.device_sensor_config = sensor_config
            if control_config:
                device.device_control_config = control_config
            
            return {
                "product_id": product.id,
                "product_name": product.name,
                "binding_type": binding_type
            }
            
        except Exception as e:
            logger.error(f"处理产品信息上报失败: {e}")
            raise
    
    def handle_product_switch(self, device: Device, new_product_code: str, new_product_version: str,
                            device_capabilities: Optional[Dict[str, Any]] = None,
                            sensor_config: Optional[Dict[str, Any]] = None,
                            control_config: Optional[Dict[str, Any]] = None,
                            switch_reason: str = "用户主动切换") -> Dict[str, Any]:
        """
        处理设备产品切换
        """
        try:
            # 1. 查找新产品
            new_product = self.find_matching_product(new_product_code, new_product_version)
            
            # 2. 如果没有找到新产品，自动创建
            if not new_product:
                new_product = self.auto_create_product(
                    new_product_code, new_product_version, device_capabilities
                )
                is_auto_created = True
            else:
                is_auto_created = False
            
            # 3. 记录切换历史
            old_product_id = device.product_id
            old_product_code = device.product_code
            
            # 4. 绑定到新产品
            device = self.bind_device_to_product(
                device, new_product, new_product_code, new_product_version, is_auto_created
            )
            
            # 5. 更新设备配置信息
            if device_capabilities:
                device.device_capabilities = device_capabilities
            if sensor_config:
                device.device_sensor_config = sensor_config
            if control_config:
                device.device_control_config = control_config
            
            # 6. 记录切换历史
            self._record_product_switch(
                device, old_product_id, new_product.id,
                old_product_code, new_product_code, switch_reason
            )
            
            return {
                "old_product_id": old_product_id,
                "new_product_id": new_product.id,
                "new_product_name": new_product.name
            }
            
        except Exception as e:
            logger.error(f"处理产品切换失败: {e}")
            raise
    
    def _record_product_switch(self, device: Device, old_product_id: Optional[int], 
                             new_product_id: int, old_product_code: Optional[str],
                             new_product_code: str, reason: str):
        """
        记录产品切换历史
        """
        try:
            from sqlalchemy import text
            
            # 准备旧配置和新配置数据
            old_config = {
                "product_code": old_product_code,
                "sensor_config": device.device_sensor_config,
                "control_config": device.device_control_config,
                "capabilities": device.device_capabilities
            }
            
            # 获取新产品信息
            new_product = self.db.query(Product).filter(Product.id == new_product_id).first()
            new_config = {
                "product_code": new_product_code,
                "sensor_config": new_product.sensor_config if new_product else None,
                "control_config": new_product.control_config if new_product else None,
                "capabilities": device.device_capabilities
            }
            
            # 插入产品切换历史记录
            insert_query = text("""
                INSERT INTO aiot_device_product_history 
                (device_id, old_product_id, new_product_id, switch_reason, 
                 old_config, new_config, switched_at)
                VALUES (:device_id, :old_product_id, :new_product_id, :switch_reason,
                        :old_config, :new_config, :switched_at)
            """)
            
            self.db.execute(insert_query, {
                "device_id": device.id,
                "old_product_id": old_product_id,
                "new_product_id": new_product_id,
                "switch_reason": reason,
                "old_config": str(old_config),  # 转换为字符串存储
                "new_config": str(new_config),
                "switched_at": get_beijing_now()
            })
            
            # 更新设备的产品切换计数
            device.product_switch_count = (device.product_switch_count or 0) + 1
            
            logger.info(f"设备产品切换记录已保存: 设备={device.uuid}, "
                       f"旧产品={old_product_id}({old_product_code}), "
                       f"新产品={new_product_id}({new_product_code}), "
                       f"原因={reason}")
            
        except Exception as e:
            logger.error(f"记录产品切换历史失败: {e}")
            # 不抛出异常，避免影响主流程
    
    def _get_default_unit(self, sensor_name: str) -> str:
        """
        获取传感器的默认单位
        """
        unit_mapping = {
            "temperature": "°C",
            "humidity": "%",
            "pressure": "hPa",
            "light": "lux",
            "voltage": "V",
            "current": "A",
            "power": "W",
            "distance": "cm",
            "ph": "pH",
            "co2": "ppm"
        }
        return unit_mapping.get(sensor_name.lower(), "")
    
    def _get_actuator_type(self, actuator_name: str) -> str:
        """
        获取执行器的类型
        """
        type_mapping = {
            "led": "digital",
            "relay": "digital", 
            "motor": "pwm",
            "servo": "pwm",
            "buzzer": "digital",
            "fan": "pwm",
            "heater": "digital",
            "pump": "digital"
        }
        return type_mapping.get(actuator_name.lower(), "digital")