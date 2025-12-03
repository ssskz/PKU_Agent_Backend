-- 数据库初始化脚本 - 仅创建表结构
-- 注意：数据库 pku_agent 需要事先手动创建

-- 智能体表
CREATE TABLE IF NOT EXISTS `agent` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL COMMENT '智能体名称',
  `description` TEXT COMMENT '描述',
  `system_prompt` TEXT COMMENT '系统提示词',
  `user_prompt_template` TEXT COMMENT '用户提示词模板',
  `model_config` JSON COMMENT '模型配置',
  `workflow_id` BIGINT COMMENT '关联工作流ID',
  `knowledge_base_ids` JSON COMMENT '关联知识库ID列表',
  `plugin_ids` JSON COMMENT '关联插件ID列表',
  `status` VARCHAR(20) DEFAULT 'draft' COMMENT '状态：draft/published',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='智能体表';
