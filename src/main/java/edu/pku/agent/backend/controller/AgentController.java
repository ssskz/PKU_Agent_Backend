package edu.pku.agent.backend.controller;

import edu.pku.agent.backend.entity.Agent;
import edu.pku.agent.backend.service.AgentService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Agent REST API 控制器
 */
@RestController
@RequestMapping("/api/agents")
@RequiredArgsConstructor
@CrossOrigin(origins = "*") // 允许跨域访问
public class AgentController {

    private final AgentService agentService;

    /**
     * 获取所有智能体列表
     * GET /api/agents
     */
    @GetMapping
    public ResponseEntity<List<Agent>> getAllAgents() {
        List<Agent> agents = agentService.findAll();
        return ResponseEntity.ok(agents);
    }

    /**
     * 根据ID获取智能体
     * GET /api/agents/{id}
     */
    @GetMapping("/{id}")
    public ResponseEntity<Agent> getAgentById(@PathVariable Long id) {
        return agentService.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * 根据状态查询智能体列表
     * GET /api/agents/status/{status}
     */
    @GetMapping("/status/{status}")
    public ResponseEntity<List<Agent>> getAgentsByStatus(@PathVariable String status) {
        List<Agent> agents = agentService.findByStatus(status);
        return ResponseEntity.ok(agents);
    }

    /**
     * 根据名称模糊查询智能体
     * GET /api/agents/search?name=xxx
     */
    @GetMapping("/search")
    public ResponseEntity<List<Agent>> searchAgentsByName(@RequestParam String name) {
        List<Agent> agents = agentService.findByName(name);
        return ResponseEntity.ok(agents);
    }

    /**
     * 创建智能体
     * POST /api/agents
     */
    @PostMapping
    public ResponseEntity<Agent> createAgent(@RequestBody Agent agent) {
        Agent createdAgent = agentService.create(agent);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdAgent);
    }

    /**
     * 更新智能体
     * PUT /api/agents/{id}
     */
    @PutMapping("/{id}")
    public ResponseEntity<Agent> updateAgent(@PathVariable Long id, @RequestBody Agent agent) {
        try {
            Agent updatedAgent = agentService.update(id, agent);
            return ResponseEntity.ok(updatedAgent);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * 删除智能体
     * DELETE /api/agents/{id}
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteAgent(@PathVariable Long id) {
        if (!agentService.exists(id)) {
            return ResponseEntity.notFound().build();
        }
        agentService.delete(id);
        return ResponseEntity.noContent().build();
    }

    /**
     * 检查智能体是否存在
     * HEAD /api/agents/{id}
     */
    @RequestMapping(value = "/{id}", method = RequestMethod.HEAD)
    public ResponseEntity<Void> checkAgentExists(@PathVariable Long id) {
        if (agentService.exists(id)) {
            return ResponseEntity.ok().build();
        }
        return ResponseEntity.notFound().build();
    }
}
