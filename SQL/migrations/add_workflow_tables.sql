-- 工作流系统表结构迁移脚本
-- 创建时间: 2025-12-24

-- 1. 创建工作流表
CREATE TABLE IF NOT EXISTS `workflows` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(36) NOT NULL COMMENT '工作流UUID',
  `name` varchar(255) NOT NULL COMMENT '工作流名称',
  `description` text COMMENT '工作流描述',
  `agent_id` int DEFAULT NULL COMMENT '关联的智能体ID',
  `user_id` int NOT NULL COMMENT '创建者ID',
  `definition` json DEFAULT NULL COMMENT '工作流定义（节点和边）',
  `status` enum('DRAFT','PUBLISHED','ARCHIVED') NOT NULL DEFAULT 'DRAFT' COMMENT '工作流状态',
  `version` int NOT NULL DEFAULT '1' COMMENT '版本号',
  `execution_count` int NOT NULL DEFAULT '0' COMMENT '执行次数',
  `success_count` int NOT NULL DEFAULT '0' COMMENT '成功次数',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `idx_agent_id` (`agent_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_workflows_agent` FOREIGN KEY (`agent_id`) REFERENCES `aiot_agents` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_workflows_user` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流表';

-- 2. 创建工作流执行记录表
CREATE TABLE IF NOT EXISTS `workflow_executions` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(36) NOT NULL COMMENT '执行UUID',
  `workflow_id` int NOT NULL COMMENT '工作流ID',
  `workflow_uuid` varchar(36) NOT NULL COMMENT '工作流UUID快照',
  `workflow_version` int NOT NULL COMMENT '工作流版本快照',
  `user_id` int NOT NULL COMMENT '执行者ID',
  `status` enum('PENDING','RUNNING','COMPLETED','FAILED','CANCELLED') NOT NULL DEFAULT 'PENDING' COMMENT '执行状态',
  `input_data` json DEFAULT NULL COMMENT '输入数据',
  `output_data` json DEFAULT NULL COMMENT '输出数据',
  `context` json DEFAULT NULL COMMENT '执行上下文',
  `error_message` text COMMENT '错误信息',
  `error_node_id` varchar(100) DEFAULT NULL COMMENT '出错节点ID',
  `started_at` datetime DEFAULT NULL COMMENT '开始时间',
  `completed_at` datetime DEFAULT NULL COMMENT '完成时间',
  `duration_seconds` int DEFAULT NULL COMMENT '执行时长（秒）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `idx_workflow_id` (`workflow_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_workflow_executions_workflow` FOREIGN KEY (`workflow_id`) REFERENCES `workflows` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_workflow_executions_user` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流执行记录表';

-- 3. 创建工作流执行日志表
CREATE TABLE IF NOT EXISTS `workflow_execution_logs` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `execution_id` int NOT NULL COMMENT '执行记录ID',
  `node_id` varchar(100) NOT NULL COMMENT '节点ID',
  `node_name` varchar(255) DEFAULT NULL COMMENT '节点名称',
  `node_type` varchar(50) DEFAULT NULL COMMENT '节点类型',
  `level` varchar(20) NOT NULL DEFAULT 'INFO' COMMENT '日志级别: DEBUG, INFO, WARNING, ERROR',
  `message` text NOT NULL COMMENT '日志消息',
  `input_data` json DEFAULT NULL COMMENT '节点输入',
  `output_data` json DEFAULT NULL COMMENT '节点输出',
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日志时间',
  `duration_ms` int DEFAULT NULL COMMENT '节点执行时长（毫秒）',
  PRIMARY KEY (`id`),
  KEY `idx_execution_id` (`execution_id`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_node_id` (`node_id`),
  CONSTRAINT `fk_workflow_execution_logs_execution` FOREIGN KEY (`execution_id`) REFERENCES `workflow_executions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流执行日志表';

-- 4. 创建索引以优化查询性能
CREATE INDEX `idx_workflow_name` ON `workflows` (`name`);
CREATE INDEX `idx_workflow_updated_at` ON `workflows` (`updated_at`);
CREATE INDEX `idx_execution_workflow_status` ON `workflow_executions` (`workflow_id`, `status`);
CREATE INDEX `idx_execution_user_status` ON `workflow_executions` (`user_id`, `status`);
CREATE INDEX `idx_log_execution_timestamp` ON `workflow_execution_logs` (`execution_id`, `timestamp`);

-- 完成
SELECT '工作流系统表结构创建完成！' as message;
