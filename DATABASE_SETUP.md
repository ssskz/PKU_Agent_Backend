# 数据库配置说明

## 数据库初始化步骤

### 1. 确保 MySQL 服务已启动

确保你的本地 MySQL 服务正在运行。

### 2. 创建数据库和表

有两种方式来初始化数据库：

#### 方式一：使用 MySQL 客户端手动执行

```bash
# 登录 MySQL
mysql -u root -p

# 执行 schema.sql 脚本
source /Users/larrysu/Desktop/PKU_RAG/pku-agent-backend/src/main/resources/schema.sql
```

或者直接使用命令：

```bash
mysql -u root -p < /Users/larrysu/Desktop/PKU_RAG/pku-agent-backend/src/main/resources/schema.sql
```

#### 方式二：使用 Spring Boot 自动初始化

修改 `application.properties` 文件中的配置：

```properties
# 将 never 改为 always（仅首次运行时）
spring.sql.init.mode=always
```

首次运行应用后，再改回 `never`，避免每次启动都重新创建表。

### 3. 配置数据库连接

在 `src/main/resources/application.properties` 文件中修改数据库连接信息：

```properties
spring.datasource.url=jdbc:mysql://localhost:3306/pku_agent?useUnicode=true&characterEncoding=utf8mb4&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true
spring.datasource.username=root
spring.datasource.password=你的密码
```

**重要**：请将 `spring.datasource.password` 修改为你的 MySQL root 密码。

### 4. 验证数据库

登录 MySQL 验证表是否创建成功：

```sql
USE pku_agent;

SHOW TABLES;

DESC agent;
```

## 数据库结构

### agent 表结构

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | BIGINT | 主键，自增 |
| name | VARCHAR(100) | 智能体名称 |
| description | TEXT | 描述 |
| system_prompt | TEXT | 系统提示词 |
| user_prompt_template | TEXT | 用户提示词模板 |
| model_config | JSON | 模型配置 |
| workflow_id | BIGINT | 关联工作流ID |
| knowledge_base_ids | JSON | 关联知识库ID列表 |
| plugin_ids | JSON | 关联插件ID列表 |
| status | VARCHAR(20) | 状态（draft/published） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 索引

- PRIMARY KEY: `id`
- INDEX: `idx_status` (status)
- INDEX: `idx_created_at` (created_at)

## 数据示例

插入测试数据：

```sql
INSERT INTO agent (name, description, system_prompt, status) 
VALUES (
    'ChatBot助手', 
    '一个智能对话助手', 
    '你是一个友好、专业的AI助手，请帮助用户解决问题。',
    'published'
);
```

## 常见问题

### 1. 连接数据库失败

检查：
- MySQL 服务是否启动
- 数据库连接信息是否正确
- 用户名密码是否正确

### 2. 表已存在错误

如果提示表已存在，可以先删除：

```sql
DROP TABLE IF EXISTS agent;
```

然后重新执行创建表的 SQL。

### 3. JSON 字段不支持

确保 MySQL 版本 >= 5.7，JSON 类型从该版本开始支持。
