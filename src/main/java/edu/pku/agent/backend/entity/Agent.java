package edu.pku.agent.backend.entity;

import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 智能体实体类
 */
@Data
@Entity
@Table(name = "agent")
public class Agent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * 智能体名称
     */
    @Column(name = "name", nullable = false, length = 100)
    private String name;

    /**
     * 描述
     */
    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    /**
     * 系统提示词
     */
    @Column(name = "system_prompt", columnDefinition = "TEXT")
    private String systemPrompt;

    /**
     * 用户提示词模板
     */
    @Column(name = "user_prompt_template", columnDefinition = "TEXT")
    private String userPromptTemplate;

    /**
     * 模型配置（JSON格式）
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "model_config", columnDefinition = "JSON")
    private Map<String, Object> modelConfig;

    /**
     * 关联工作流ID
     */
    @Column(name = "workflow_id")
    private Long workflowId;

    /**
     * 关联知识库ID列表（JSON格式）
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "knowledge_base_ids", columnDefinition = "JSON")
    private List<Long> knowledgeBaseIds;

    /**
     * 关联插件ID列表（JSON格式）
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "plugin_ids", columnDefinition = "JSON")
    private List<Long> pluginIds;

    /**
     * 状态：draft/published
     */
    @Column(name = "status", length = 20)
    private String status = "draft";

    /**
     * 创建时间
     */
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
