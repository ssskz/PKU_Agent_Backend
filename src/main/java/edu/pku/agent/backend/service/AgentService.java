package edu.pku.agent.backend.service;

import edu.pku.agent.backend.entity.Agent;
import edu.pku.agent.backend.repository.AgentRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

/**
 * Agent 服务层
 */
@Service
@RequiredArgsConstructor
public class AgentService {

    private final AgentRepository agentRepository;

    /**
     * 查询所有智能体
     */
    public List<Agent> findAll() {
        return agentRepository.findAll();
    }

    /**
     * 根据ID查询智能体
     */
    public Optional<Agent> findById(Long id) {
        return agentRepository.findById(id);
    }

    /**
     * 根据状态查询智能体列表
     */
    public List<Agent> findByStatus(String status) {
        return agentRepository.findByStatus(status);
    }

    /**
     * 根据名称模糊查询智能体
     */
    public List<Agent> findByName(String name) {
        return agentRepository.findByNameContaining(name);
    }

    /**
     * 创建智能体
     */
    @Transactional
    public Agent create(Agent agent) {
        return agentRepository.save(agent);
    }

    /**
     * 更新智能体
     */
    @Transactional
    public Agent update(Long id, Agent agent) {
        Agent existingAgent = agentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Agent not found with id: " + id));
        
        // 更新字段
        if (agent.getName() != null) {
            existingAgent.setName(agent.getName());
        }
        if (agent.getDescription() != null) {
            existingAgent.setDescription(agent.getDescription());
        }
        if (agent.getSystemPrompt() != null) {
            existingAgent.setSystemPrompt(agent.getSystemPrompt());
        }
        if (agent.getUserPromptTemplate() != null) {
            existingAgent.setUserPromptTemplate(agent.getUserPromptTemplate());
        }
        if (agent.getModelConfig() != null) {
            existingAgent.setModelConfig(agent.getModelConfig());
        }
        if (agent.getWorkflowId() != null) {
            existingAgent.setWorkflowId(agent.getWorkflowId());
        }
        if (agent.getKnowledgeBaseIds() != null) {
            existingAgent.setKnowledgeBaseIds(agent.getKnowledgeBaseIds());
        }
        if (agent.getPluginIds() != null) {
            existingAgent.setPluginIds(agent.getPluginIds());
        }
        if (agent.getStatus() != null) {
            existingAgent.setStatus(agent.getStatus());
        }
        
        return agentRepository.save(existingAgent);
    }

    /**
     * 删除智能体
     */
    @Transactional
    public void delete(Long id) {
        agentRepository.deleteById(id);
    }

    /**
     * 检查智能体是否存在
     */
    public boolean exists(Long id) {
        return agentRepository.existsById(id);
    }
}
