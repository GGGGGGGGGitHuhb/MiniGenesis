# V0.1/S2 Resource World and Lifecycle Design

## 文档元数据

- Version: `V0.1 Deterministic World`
- Stage: `S2 Resource World and Lifecycle`
- Status: `Draft`
- Date: `2026-08-24`
- Roadmap: `ROADMAP.md / V0.1`
- Prerequisite: `V0.1/S1 Completed`
- Rework documents: 无

本设计在用户批准后才成为阶段权威。对应评审计划为 `docs/reviewer/reviews/V0.1/S2-review.md`。

## 1. 阶段目标

在 S1 的确定性实验骨架上建立无空间资源世界。系统应能创建一组没有基因组的基线 Agent，以确定性顺序执行资源获取、代谢、衰老和死亡，并通过能量账本解释每一步状态变化。

用户可观察一个有限运行的最小世界，但不能在本阶段观察繁殖、变异或演化。

## 2. 范围与边界

### 2.1 必须包含

- 全局资源池和外部资源注入。
- Agent 的稳定 ID、energy、age 和 alive 状态。
- tick 级确定性调度。
- `HARVEST` 与 `WAIT` 两个基线动作。
- 动作成本、基础代谢、衰老和死亡。
- 资源/能量账本与规范化逐 tick 状态摘要。
- 正常、边界和长时间运行测试。

### 2.2 明确排除

- Genome、程序计数器、VM、复制、繁殖、变异和谱系。
- Agent 间能量转移、通信、攻击或任何带高级语义的交互。
- 空间、位置、移动和局部资源。
- Parquet、批量实验、研究指标和图表。
- 人工 fitness、分数或“最优个体”判断。

### 2.3 基线动作策略

由于本阶段没有 Genome，Agent 使用一个明确标记为测试基线的无状态策略：当全局资源池大于零时请求 `HARVEST`，否则 `WAIT`。该策略不得被解释为遗传行为，也不得扩展成策略系统；`V0.2` 将由 VM 输出动作意图。

### 2.4 停止并确认条件

- 需要引入繁殖或基因组才能完成生命周期；
- 需要改变 S1 已接受的配置、RNG 或摘要语义且无法兼容；
- 资源守恒只能通过隐藏修正值维持；
- 需要空间或个体交互解决调度问题。

## 3. 需求

### REQ-01：世界配置

在 S1 配置基础上增加：

```yaml
world:
  initial_resource: 100
  resource_inflow_per_tick: 10
  harvest_amount: 4
  action_cost: 1
  metabolism_cost: 1
agent:
  initial_count: 3
  initial_energy: 10
  max_age: 20
```

所有数值使用整数。资源、能量、成本和数量不得为负；`initial_count`、`initial_energy`、`max_age` 必须大于零。必须设置并测试合理硬上限，拒绝而非截断超限配置。

### REQ-02：Agent 状态与身份

- 初始 Agent ID 必须唯一、稳定且与容器内存地址无关。
- Agent 持有 ID、energy、age、alive；不得持有资源池、RNG 或输出器。
- age 在每个完成的 tick 增加一次。
- `energy <= 0` 或 `age >= max_age` 时死亡。
- 死亡后不得再次调度或执行动作。

### REQ-03：tick 顺序

每个 tick 必须按下列固定阶段执行：

1. 将配置的外部资源注入全局资源池并记账；
2. 从 tick 开始时的存活 Agent 取得调度快照；
3. 通过运行级 RNG 对快照产生确定性顺序；
4. 每个 Agent 生成并提交一个动作意图；
5. World 顺序校验并执行动作；
6. 对本 tick 快照中的仍存活 Agent 扣除基础代谢并增加 age；
7. 结算死亡并处理剩余 energy；
8. 核对账本、生成 tick 摘要并推进 tick。

任何实现顺序变化都属于设计变更，不得由 Builder 静默调整。

### REQ-04：动作语义

- `HARVEST`：World 先验证 Agent 当前 energy 是否足以支付 `action_cost`；验证通过后，将动作成本转入 `dissipated_energy`，再从全局资源池取得 `min(harvest_amount, available_resource)` 并转为 Agent energy。
- `WAIT`：不获取资源，不支付动作成本。
- 当动作开始时 Agent energy 不足以支付动作成本，动作失败且不扣成本、不发生资源转移；随后仍进入代谢与死亡结算。
- World 是动作合法性和资源转移的唯一权威；Agent 不得直接修改资源池。
- 动作结果必须区分 applied、rejected 及拒绝原因。

### REQ-05：代谢、衰老与死亡

- 基础代谢从 Agent energy 扣除，实际扣除量为 `min(metabolism_cost, current_energy)`，扣除部分进入 `dissipated_energy`。
- 动作成本同样进入 `dissipated_energy`。
- 因年龄上限死亡时，剩余正 energy 返回全局资源池。
- 因能量耗尽死亡时没有正能量可返还。
- 死亡结算必须恰好发生一次。

### REQ-06：资源账本

对初始状态及每个完整 tick，必须满足：

```text
initial_resource
+ initial_agent_energy
+ cumulative_external_inflow
= current_world_resource
+ living_agent_energy
+ cumulative_dissipated_energy
```

所有变量必须为整数。系统不得通过未记录的“纠偏”修改任一项；恒等式失败必须中止运行并报告内部一致性错误。

### REQ-07：确定性状态与摘要

JSON 摘要必须扩展为至少包含：

- tick；
- world resource；
- living/dead counts；
- total living energy；
- cumulative inflow；
- cumulative dissipated energy；
- 按 Agent ID 排序的最终状态；
- 账本校验结果；
- 规范化 digest。

调度顺序可由 seed 影响，但容器遍历、内存地址和日志时序不得影响结果。

## 4. 目录与模块影响

预期新增或扩展：

```text
src/minigenesis/
    actions.py
    agent.py
    scheduler.py
    world.py
    ledger.py
    simulation.py
    summary.py
examples/v0.1/s2-resource-world.yaml
tests/
    test_actions.py
    test_agent.py
    test_scheduler.py
    test_world.py
    test_ledger.py
    test_lifecycle.py
    test_world_determinism.py
```

强制责任边界：

- `agent`：拥有个体状态并产生基线动作意图；不得直接改变 World。
- `world`：拥有资源池、Agent 集合和动作结算；不得决定输出格式。
- `scheduler`：只产生顺序；不得执行动作或修改 Agent。
- `ledger`：记录和验证资源流；不得通过修正状态使校验通过。
- `simulation`：编排固定 tick 阶段；不得隐藏跨阶段副作用。
- `summary`：只读规范化投影；不得成为状态来源。

## 5. 关键数据流

```text
validated config + run RNG
  -> Simulation begins tick
    -> World records external inflow
    -> Scheduler orders start-of-tick live snapshot
    -> Agent produces HARVEST or WAIT intent
    -> World validates and applies intent
    -> Simulation applies metabolism and aging
    -> World settles death and returns residual energy
    -> Ledger verifies conservation identity
    -> Summary reads canonical state
```

若某一步失败，当前运行必须失败，不得输出 `completed` 状态或继续后续 tick。

## 6. 错误与恢复

- 配置非法：沿用 S1 的严格失败，不创建 World。
- 动作非法或来自已死亡 Agent：拒绝并记录内部错误；测试用非法输入不得破坏状态。
- 账本不平：立即中止并报告 tick 及各账本科目，不自动纠正。
- tick 中出现异常：不得把部分 tick 标记为已完成；摘要必须表明失败状态。
- 本阶段不写正式实验数据，因此不存在磁盘回滚；内存状态可直接丢弃。

## 7. 安全评估

本阶段不新增外部输入类型、文件写入、网络、子进程或动态代码执行。主要安全边界是防止超大配置导致资源耗尽：`initial_count` 和 `max_ticks` 必须有硬上限，并在分配大量对象前验证。

## 8. 性能与资源约束

- 时间复杂度应与 `max_ticks × initial_count` 近似线性；本阶段没有繁殖，因此种群不会增长。
- 不保存无限逐 tick 历史；只保留当前状态、累计账本和生成摘要所需的数据。
- 应能在普通开发环境中完成设计示例的十万 tick 稳定性测试；该测试可以标记为 slow，但 Reviewer 必须实际执行。

## 9. Builder 实施要求

推荐顺序：配置扩展 → Agent/动作值对象 → World 与 ledger → scheduler → 固定 tick 流程 → 摘要 → 边界/稳定性测试 → README。

Builder 可决定内部数据类与集合类型，但不得改变 tick 顺序、账本恒等式、动作成本、死亡能量返回、确定性要求或范围排除。

Builder 报告必须提供：

- 配置与摘要样例；
- 每个 REQ 对应的测试位置；
- 同 seed 完整结果比较；
- 账本边界与十万 tick 结果；
- 实际命令、退出码和观察结果；
- 任何设计偏差或未验证风险。

## 10. 测试设计

必须执行：

```powershell
python -m pytest
python -m pytest -m slow
python -m minigenesis --config examples/v0.1/s2-resource-world.yaml --output-format json
```

测试至少覆盖：

- 配置边界和硬上限；
- 初始 Agent ID 唯一性与稳定排序；
- 空资源、资源不足、刚好足够和充足资源的 `HARVEST`；
- 无法支付动作成本；
- 代谢导致死亡、年龄导致死亡、死亡只结算一次；
- 年龄死亡时剩余能量返回资源池；
- 每个 tick 的账本恒等式；
- 相同 seed 完整摘要相等；
- 不同 seed 在有竞争时可产生不同调度证据；
- 十万 tick 无状态损坏或非预期内存历史增长；
- S1 配置与错误行为的回归测试。

## 11. 验收标准

### AC-01：可运行资源世界

关联：`REQ-01` 至 `REQ-05`。

示例配置从仓库根目录成功运行到 `max_ticks`，输出最终资源、存活数、能量与账本状态；执行路径中至少实际发生资源获取、代谢和死亡。由集成测试和 Reviewer 独立运行验证。

### AC-02：逐 tick 守恒

关联：`REQ-04`、`REQ-05`、`REQ-06`。

正常、资源不足、动作拒绝、代谢死亡和年龄死亡场景的每个完整 tick 均满足账本恒等式。测试故意制造账本不一致时，运行失败而不是自动纠正。

### AC-03：调度与结果确定性

关联：`REQ-03`、`REQ-07`。

在相同代码、环境、配置和 seed 下运行两次，调度证据与规范化 JSON 逐字节一致；更换 seed 的竞争场景至少可观察到调度证据差异。

### AC-04：生命周期正确性

关联：`REQ-02`、`REQ-05`。

Agent 每个完整 tick 仅衰老一次，满足任一死亡条件后只结算一次且不再调度；年龄死亡的剩余能量完整返回资源池。

### AC-05：范围边界

关联：全部需求与范围约束。

实现不包含 Genome、VM、繁殖、变异、谱系、交互、空间、fitness 或正式实验持久化。由代码和依赖检查验证。

### AC-06：稳定性与回归

关联：`REQ-01`、`REQ-03`、`REQ-06`、`REQ-07`。

完整测试、slow 稳定性测试和 S1 回归均通过；十万 tick 运行没有账本错误、状态损坏或随 tick 累积的无界历史。

## 12. Reviewer 重点

- 逐行核对 tick 阶段顺序，避免动作、代谢和死亡的先后顺序漂移。
- 独立计算小样例的资源账本，不只检查程序自己的 `valid=true`。
- 检查死 Agent 是否可能残留在调度快照中再次行动。
- 检查集合遍历或并列顺序是否绕过集中 RNG。
- 检查基线策略是否被扩展为提前实现的行为系统。
- `AC-02`、`AC-03`、`AC-04`、`AC-05` 不可作为技术债延期。

## 13. 文档影响

阶段接受后更新 README 的功能、配置、运行、测试和项目结构；在 S1、S2 均接受后才可把 `V0.1` 标记为 `Completed`。

## 14. 修订记录

- 2026-08-24：创建初稿；明确固定 tick 顺序、基线动作策略、死亡能量处理和可独立核算的资源账本。
