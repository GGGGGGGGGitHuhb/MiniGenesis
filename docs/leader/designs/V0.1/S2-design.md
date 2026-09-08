# V0.1/S2 Resource World and Lifecycle Design

## 文档元数据

- Version: `V0.1 Deterministic World`
- Stage: `S2 Resource World and Lifecycle`
- Status: `Approved`
- Date: `2026-08-24`
- Last revised: `2026-09-07`
- Decision package: `docs/leader/reports/V0.1/S2-report-001.md`
- Approval authority: 用户 / PM，本线程 S2 开发目标中的明确“批准”
- Approval date: `2026-09-07`
- Approval record: `docs/leader/reports/V0.1/S2-report-002.md`
- Approved pre-metadata SHA-256: `5021f4bfa606682586a7e35a11d2b87ecf125a4fb8414736ac810e07b1ac2a4c`
- Roadmap: `ROADMAP.md / V0.1`
- Prerequisite: `V0.1/S1 Completed`
- Rework documents: 无

本设计已获用户批准，现为阶段权威。对应评审计划为 `docs/reviewer/reviews/V0.1/S2-review.md`。

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

完整 S2 示例（由 Builder 创建 `examples/v0.1/s2-resource-world.yaml`）：

```yaml
experiment:
  name: s2-resource-world
  seed: 1
  max_ticks: 30
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

所有数值使用整数，显式拒绝 bool、浮点、字符串和 null。边界如下，超限在创建 World/Agent 或进入循环前失败，不截断：

| 字段 | 闭区间 |
|---|---|
| `experiment.max_ticks` | `1..100_000`，沿用 S1 |
| `agent.initial_count` | `1..1_000` |
| `agent.initial_energy` | `1..1_000_000` |
| `agent.max_age` | `1..100_000` |
| `world` 中五个数值字段 | `0..1_000_000` |

此外 S2 要求 `max_ticks × initial_count <= 1_000_000`，这是运行工作量预算，不因预计提前死亡而豁免。累计账本使用 Python 整数，不将上述输入上限错误应用于累积结果。name 和 seed 的语义沿用 S1。

兼容规则为强制约束：根字段集合只允许 `{experiment}` 或 `{experiment, world, agent}`。仅有 experiment 时完整沿用 S1 空世界和 v1 摘要；world/agent 必须同时存在，所有内层字段必填，不提供隐式默认值。各层未知字段、重复键和不安全 YAML 标签仍拒绝。既有 `ExperimentConfig(name, seed, max_ticks)`、`Simulation(config)` 和 `execute(config)` 调用继续有效；推荐增加可选的不可变世界/个体配置值对象，配对校验同样适用于程序直接构造的 S2 配置。

### REQ-02：Agent 状态与身份

- 初始 Agent ID 固定为整数 `0..initial_count-1`；初始 age 为 0、alive 为 true，energy 为 initial_energy。身份不依赖容器或内存地址。
- Agent 持有 ID、energy、age、alive；不得持有资源池、RNG 或输出器。
- 本 tick 开始时存活的每个 Agent 在阶段 6 增加一次 age；已死亡 Agent 的 age 冻结。
- `energy <= 0` 或 `age >= max_age` 时死亡。
- 死亡后不得再次调度或执行动作。

### REQ-03：tick 顺序

每个 tick 必须按下列固定阶段执行：

1. 将配置的外部资源注入全局资源池并记账；
2. 从 tick 开始时的存活 Agent 取得调度快照；
3. 按 ID 升序构造快照，再通过运行级 RNG 的 shuffle 产生确定性顺序；
4. 按该顺序生成全部动作意图，此阶段不结算资源；所有 Agent 看到阶段 1 注入后的同一个资源量；
5. World 按阶段 3 顺序校验并执行已生成的动作意图，每个 Agent 恰好一个；
6. 对本 tick 快照中的 Agent 扣除基础代谢并增加 age，包含动作结束后 energy 为 0 的 Agent；
7. 结算死亡并处理剩余 energy；
8. 核对账本、生成目标 tick（旧 tick + 1）的状态快照，并在成功后发布该快照与推进 tick。

阶段 7 才标记死亡；HARVEST 支付成本后暂时 energy 为 0 仍继续该动作的获取，不在动作中途死亡。资源被前一个 Agent 取尽时，后续已排定 HARVEST 不改成 WAIT。没有存活 Agent 时仍每 tick 注入资源、核账并推进到 max_ticks，不提前结束；0 或 1 个 Agent 的调度不消费 RNG。

RNGContext 新增 shuffle 封装，唯一随机源仍是其内部 `random.Random(seed)`；保留已有 random/getstate 语义。禁止模块级随机调用、按 seed 特判或新增随机源。调度不依赖底层 Agent 集合顺序。

任何实现顺序变化都属于设计变更，不得由 Builder 静默调整。

### REQ-04：动作语义

- `HARVEST`：World 先验证 Agent 当前 energy 是否足以支付 `action_cost`；验证通过后，将动作成本转入 `dissipated_energy`，再从全局资源池取得 `min(harvest_amount, available_resource)` 并转为 Agent energy。
- `WAIT`：不获取资源，不支付动作成本。
- 合法且付得起成本的 HARVEST 即使当前资源或 harvest_amount 为 0，也支付成本并返回 applied，获取量为 0。
- 当动作开始时 Agent energy 不足以支付动作成本，动作失败且不扣成本、不发生资源转移；随后仍进入代谢与死亡结算。
- World 是动作合法性和资源转移的唯一权威；Agent 不得直接修改资源池。
- 动作结果至少包含 `agent_id`、`action`、`status`、`reason`、`harvested`、`cost_paid`。applied 的 reason 为 null；付不起成本时为 `insufficient_energy`，harvested/cost_paid 均为 0。该拒绝是正常模拟结果，不终止运行。
- 未知动作、未知 ID 或已死亡 Agent 的请求为 `invalid_action`、`unknown_agent` 或 `dead_agent`，拒绝且不修改状态；若出现在正常 tick 管线，编排器以内部一致性错误终止。动作结果只需供测试及当次结算使用，不积累事件历史。

### REQ-05：代谢、衰老与死亡

- 基础代谢从 Agent energy 扣除，实际扣除量为 `min(metabolism_cost, current_energy)`，扣除部分进入 `dissipated_energy`。
- 动作成本同样进入 `dissipated_energy`。
- 因年龄上限死亡时，剩余正 energy 返回全局资源池。
- 因能量耗尽死亡时没有正能量可返还。
- 死亡结算必须恰好发生一次。结算后 energy 为 0、alive 为 false，ID 和最终 age 保留；两种死亡条件同时命中仍只结算一次。

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

S1 输入的摘要字段、字段顺序、schema、digest、文本输出与单换行合同全部保持。S2 使用 `minigenesis.summary.v2`，成功 JSON 的顶层字段按以下顺序固定：

```text
schema_version, experiment_name, seed, rng_implementation,
requested_ticks, completed_ticks, status, config, state, digest
```

- 前七项沿用 S1 意义，status 为 completed，completed_ticks 等于 max_ticks。
- `config`：顺序为 world、agent；各内层字段按 REQ-01 示例顺序，值为完整已校验配置，确保参数变化进入 digest。
- `state`：顺序为 tick、world_resource、living_count、dead_count、living_agent_energy、ledger、agents。tick 表示已完成 tick 数，初始 0。
- `ledger`：顺序为 initial_resource、initial_agent_energy、cumulative_external_inflow、cumulative_dissipated_energy、valid。initial_agent_energy 是初始总能量，valid 只在独立核账成功后为 true。
- `agents`：包含全部初始 Agent，按 ID 升序；每项顺序为 id、energy、age、alive。死亡状态也保留，总长度固定 initial_count。
- digest 对除 digest 字段外的上述完整对象计算 SHA-256；沿用 S1 的 UTF-8、ensure_ascii=False、紧凑分隔符、插入顺序、输入无换行及 `sha256:` 小写十六进制。stdout 仅一个 JSON 对象和一个 LF。
- 文本摘要需报告 ticks、最终资源、存活/死亡数、存活总能量、账本结果和 digest；不固定 S2 文本措辞。

初始状态和每个成功 step 后可获取同结构的只读 `state` 快照（推荐接口 `Simulation.snapshot()`）；调用不得消费 RNG、修改世界或向内部追加历史。模拟仅保留最新快照或按需生成，测试可在小样例中自行收集。最终 build_summary 仍只接受完整成功运行，失败/未完成运行不得生成成功摘要。

调度证据由测试直接检查 scheduler 返回顺序及小样例的逐 tick 观察收集，CLI 不新增事件流。同 seed 比较逐 tick 状态和调度，不能只比较全体死亡后的最终状态。A-B-A 隔离需同时覆盖 S2 与 S1/S2 混合运行。

## 4. 目录与模块影响

预期新增或扩展：

```text
src/minigenesis/
    config.py       # 配对配置与输入上限
    rng.py          # shuffle 封装
    cli.py          # S1/S2 路由与错误合同
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
- 正常动作拒绝与内部非法请求按 REQ-04 区分；直接单元测试非法输入不修改状态，管线出现非法请求则终止。
- 账本不平：立即中止并报告 tick 及各账本科目，不自动纠正。
- tick 中出现异常：不推进完成 tick，不发布部分状态为成功快照，将运行标为失败并禁止继续 step/run 或构造成功摘要；不尝试回滚后续重试。
- CLI 配置失败退出 2，内部一致性或运行异常退出 1；stderr 给出可读原因，账本错误包含失败的目标 tick（completed_ticks + 1）及等式两侧科目；stdout 保持为空。成功退出 0。不增加失败 JSON schema，以保持 S1 错误合同。
- 本阶段不写正式实验数据，因此不存在磁盘回滚；内存状态可直接丢弃。

## 7. 安全评估

本阶段不新增外部输入类型、文件写入、网络、子进程或动态代码执行。主要安全边界是防止超大配置导致资源耗尽：`initial_count` 和 `max_ticks` 必须有硬上限，并在分配大量对象前验证。

## 8. 性能与资源约束

- 时间复杂度应与 `max_ticks × initial_count` 近似线性；本阶段没有繁殖，因此种群不会增长。
- 不保存无限逐 tick 历史；只保留当前状态、累计账本和生成摘要所需的数据。
- 必须以 slow 测试实际执行两个十万 tick 资源世界：其一使用主示例参数但 max_ticks=100000，覆盖死亡后持续注入；其二 initial_count=1、initial_energy=10、max_age=100000，world 的 initial_resource=0、resource_inflow_per_tick=1、harvest_amount=1、action_cost=0、metabolism_cost=1，保证每 tick 均执行动作/代谢，末 tick 年龄死亡。不得仅运行早期全灭后的空循环证明活体稳定性。
- slow marker 由 Builder 在 pyproject.toml 注册；全量命令包含 slow，定向命令再次独立选择它。记录实际耗时和环境，不预设未经测量的速度承诺。
- 长运行测试以在线断言/累计计数验证每 tick，不保存完整轨迹；比较 1000/10000/100000 tick 下保留容器的大小及内存观察，区分测试日志自身增长。产品持有状态为 O(initial_count)，允许固定数量最新快照。

## 9. Builder 实施要求

实施里程碑均为 Planned：

1. M1 配置与兼容：配对 world/agent、边界、旧调用和 v1 字节合同；S1 回归通过后进入 M2。
2. M2 世界与生命周期：Agent/动作值对象、World/ledger、固定调度和 tick；手算账本、拒绝和两类死亡通过后进入 M3。
3. M3 输出与确定性：v2 摘要、只读快照、同 seed 逐 tick 与 A-B-A；故障注入通过后进入 M4。
4. M4 交付证据：两个十万 tick 场景、干净安装、完整回归、README 和 Builder 报告，然后独立 Reviewer。

保留 Python >=3.11、现有 PyYAML/pytest 依赖，不新增外部服务或运行依赖。验收优先在已验证的 Windows 环境运行；记录实际 Python/依赖版本与当前 checkout，不复用指向旧位置的 editable 安装。其他环境结果只能按实际证据声明。

配置/接口/字段顺序、调度算法和错误语义为强制约束；数据类名称、私有辅助函数和低层集合组织由 Builder 决定。

Builder 可决定内部数据类与集合类型，但不得改变 tick 顺序、账本恒等式、动作成本、死亡能量返回、确定性要求或范围排除。

Builder 报告必须提供：

- 配置与摘要样例；
- 每个 REQ 对应的测试位置；
- 同 seed 完整结果比较；
- 账本边界与十万 tick 结果；
- 实际命令、退出码和观察结果；
- 任何设计偏差或未验证风险。

## 10. 测试设计

以下为批准后 Builder/Reviewer 的计划命令，本次准备尚未执行。工作目录为仓库根，激活各自隔离环境后先执行 `python -m pip install -e ".[dev]"`；Reviewer 使用独立环境。必须执行：

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

### 11.1 需求追踪

| 需求 | 验收 | 必需评审 |
|---|---|---|
| REQ-01 | AC-01、AC-06 | RV-01、RV-07、RV-09 |
| REQ-02 | AC-01、AC-04 | RV-02、RV-05 |
| REQ-03 | AC-01、AC-03、AC-06 | RV-02、RV-06、RV-07 |
| REQ-04 | AC-01、AC-02 | RV-03、RV-04 |
| REQ-05 | AC-01、AC-02、AC-04 | RV-04、RV-05 |
| REQ-06 | AC-02、AC-06 | RV-04、RV-07 |
| REQ-07 | AC-03、AC-06 | RV-06、RV-07、RV-09 |
| 范围边界 | AC-05 | RV-08 |

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

- 2026-09-07：基于合并后的 S1 实现修订 Draft；明确配置配对与上限、S1/v2 兼容、批量意图与顺序结算、延迟死亡、失败合同、快照、有效活体长运行和 REQ/AC/RV 追踪。尚未批准或实现。

- 2026-09-07：用户批准 S2-report-001 决策包；记录批准日期、权威及批准前哈希，状态改为 Approved。技术正文与验收要求保持原批准基线；批准原文见 S2-report-002。
