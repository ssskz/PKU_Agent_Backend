package edu.pku.agent.backend.repository;

import edu.pku.agent.backend.entity.Agent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Agent 数据访问接口
 */
@Repository
public interface AgentRepository extends JpaRepository<Agent, Long> {

    /**
     * 根据状态查询智能体列表
     * @param status 状态
     * @return 智能体列表
     */
    List<Agent> findByStatus(String status);

    /**
     * 根据名称查询智能体（模糊查询）
     * @param name 名称关键词
     * @return 智能体列表
     */
    List<Agent> findByNameContaining(String name);

    /**
     * 根据工作流ID查询智能体
     * @param workflowId 工作流ID
     * @return 智能体列表
     */
    List<Agent> findByWorkflowId(Long workflowId);
}
