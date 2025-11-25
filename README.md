# PKU-Agent-Backend

## 项目介绍

PKU-Agent-Backend 是一个基于 Spring Boot 4.0.0 的智能体平台后端项目，采用现代化的 Java 技术栈构建。

## 技术栈

- **开发语言**: Java 23
- **核心框架**: Spring Boot 4.0.0
- **构建工具**: Maven
- **主要依赖**:
  - Spring Boot Starter WebMVC - Web 应用开发
  - Spring Boot DevTools - 开发热部署
  - Lombok - 简化 Java 代码
  - Spring Boot Starter Test - 单元测试

## 项目结构

```
pku-agent-backend/
├── pom.xml                                    # Maven 项目配置文件
├── README.md                                  # 项目说明文档
├── LICENSE                                    # 开源许可证
├── mvnw & mvnw.cmd                           # Maven Wrapper 脚本
└── src/
    ├── main/
    │   ├── java/
    │   │   └── edu/pku/agent/backend/
    │   │       ├── PkuAgentBackendApplication.java      # Spring Boot 主启动类
    │   │       └── controller/
    │   │           └── HelloController.java             # Hello World 示例控制器
    │   └── resources/
    │       ├── application.properties         # 应用配置文件
    │       ├── static/                        # 静态资源目录
    │       └── templates/                     # 模板文件目录
    └── test/
        └── java/                              # 单元测试目录
            └── edu/pku/agent/backend/
                └── PkuAgentBackendApplicationTests.java
```

## 快速开始

### 环境要求

- JDK 23 或更高版本
- Maven 3.6+ 或使用项目自带的 Maven Wrapper

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://gitee.com/ssskz/pku-agent-backend.git
   cd pku-agent-backend
   ```

2. **编译项目**
   ```bash
   mvn clean install
   ```

3. **运行项目**
   
   方式一：使用 Maven 命令
   ```bash
   mvn spring-boot:run
   ```
   
   方式二：运行打包后的 JAR
   ```bash
   mvn clean package
   java -jar target/pku-agent-backend-0.0.1-SNAPSHOT.jar
   ```

4. **验证启动**
   
   应用启动后，默认运行在 `http://localhost:8080`
   
   访问测试接口：
   ```bash
   curl http://localhost:8080/api/hello
   ```
   
   预期返回：
   ```
   Hello World!
   ```

## API 接口

### Hello World 接口

- **接口地址**: `GET /api/hello`
- **功能说明**: 返回简单的问候信息
- **请求示例**:
  ```bash
  curl http://localhost:8080/api/hello
  ```
- **响应示例**:
  ```
  Hello World!
  ```

## 开发指南

### 添加新的 Controller

1. 在 `src/main/java/edu/pku/agent/backend/controller/` 目录下创建新的 Controller 类
2. 使用 `@RestController` 注解标注类
3. 使用 `@RequestMapping` 定义基础路径
4. 使用 `@GetMapping`、`@PostMapping` 等注解定义具体接口

示例代码：
```java
@RestController
@RequestMapping("/api")
public class YourController {
    
    @GetMapping("/your-endpoint")
    public String yourMethod() {
        return "Your response";
    }
}
```

### 配置说明

主要配置文件：`src/main/resources/application.properties`

```properties
# 应用名称
spring.application.name=PKU-Agent-Backend

# 服务端口（默认 8080）
# server.port=8080

# 其他配置...
```

## 测试

运行单元测试：
```bash
mvn test
```

## 打包部署

### 生成可执行 JAR

```bash
mvn clean package
```

生成的 JAR 文件位于 `target/` 目录下。

### 运行生产环境

```bash
java -jar target/pku-agent-backend-0.0.1-SNAPSHOT.jar
```


## 许可证

本项目采用开源许可证，详见 [LICENSE](LICENSE) 文件。