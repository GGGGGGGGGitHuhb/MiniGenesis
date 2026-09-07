# V0.1/S2 Resource World and Lifecycle Review Plan

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
- Approved pre-metadata SHA-256: `42219a92f4a1a68c4a4e2cb3a6d329a73fd6698fd2ffefe0153dbbf8494ab9d6`
- Governing design: `docs/leader/designs/V0.1/S2-design.md`
- Prerequisite evidence: S1 Reviewer conclusion is `PASS` or approved `PASS WITH DEBT`
- Applicable reworks: 无
- Review scope: 资源世界、Agent、调度、动作、代谢、衰老、死亡、账本、确定性与 S1 回归
- Excluded scope: VM、繁殖、变异、谱系、个体交互、空间、批量实验和研究指标

本计划只细化验证方法，不修改 S2 设计。若 S1 未被接受，S2 的最终结论必须为 `BLOCKED`，但 Reviewer 可以记录非最终的预检查结果。

## 1. 评审目标

Reviewer 必须独立确认：

- 固定 tick 顺序被完整实现；
- World 是资源与动作结算的唯一权威；
- 每个完整 tick 都满足资源账本恒等式；
- Agent 衰老、代谢、死亡和剩余能量处理符合设计；
- 调度和最终结果在相同输入下确定；
- 十万 tick 基线不会积累无界历史或破坏状态；
- S1 能力没有回归，后续阶段能力没有提前实现。

## 2. 评审输入

评审前读取：

- `ROADMAP.md / V0.1`；
- `docs/leader/designs/V0.1/S1-design.md` 与 S1 最终 Reviewer 报告；
- `docs/leader/designs/V0.1/S2-design.md`；
- 所有适用 rework；
- S2 Builder 报告及之前仍开放的相关发现；
- world、agent、actions、scheduler、ledger、simulation、summary、配置和全部测试；
- README 的当前功能、命令、配置和状态。

## 3. 评审矩阵

### RV-01：资源世界最短路径

Source: `REQ-01` 至 `REQ-05`、`AC-01`

Required: Yes

Method:

```powershell
python -m minigenesis --config examples/v0.1/s2-resource-world.yaml --output-format json
```

Evidence:

- 配置、命令、退出码和 JSON；
- 资源获取、代谢和至少一种死亡实际发生的事件或测试证据；
- 最终 tick、资源、存活数、能量和账本科目。

Pass condition:

- 运行到配置的 `max_ticks` 并成功退出；
- 输出字段与最终状态一致；
- 接受路径不是仅由空世界或全 WAIT 构成。

Failure severity: `Major`；无法启动为 `Blocker`。

### RV-02：tick 阶段顺序

Source: `REQ-03`、`AC-01`、`AC-04`

Required: Yes

Method:

- 审查 simulation 编排；
- 使用单 Agent、两 Agent 和资源竞争用例断言每个阶段的中间状态；
- 验证调度快照在 tick 开始时生成，死亡 Agent 不进入后续 tick。

Evidence:

- 阶段顺序对应的代码位置；
- 中间状态测试与结果，明确全部意图先生成、再顺序结算；
- 资源竞争耗尽后后续 HARVEST 仍扣成本，以及支付后暂时零能量仍完成获取的结果；
- 死亡边界测试。

Pass condition:

- 八个阶段与设计顺序一致；
- 每个 Agent 每 tick 最多一个动作、一次代谢和一次衰老；
- 死亡只结算一次。

Failure severity: `Blocker`。

### RV-03：动作权威与边界

Source: `REQ-04`、`AC-01`、`AC-02`

Required: Yes

Method:

```powershell
python -m pytest -k "action or harvest or wait"
```

覆盖空资源、资源少于 harvest、刚好足够、充足资源、零 harvest、无法支付动作成本、刚好付清成本后获取，以及 invalid_action/unknown_agent/dead_agent。检查正常 insufficient_energy 继续运行，内部非法请求在 tick 管线中终止且无部分状态转移。

Evidence:

- 每个用例的执行前后 World/Agent/ledger 状态；
- applied/rejected 结果及原因；
- Agent 无法直接改资源池的代码检查。

Pass condition:

- 转移量、成本和拒绝语义与设计逐项一致；
- 拒绝动作不产生部分资源转移；
- 所有资源变化由 World 结算并进入 ledger。

Failure severity: `Major`；可绕过 World 修改资源时为 `Blocker`。

### RV-04：独立账本核算

Source: `REQ-05`、`REQ-06`、`AC-02`

Required: Yes

Method:

- Reviewer 手工计算至少五个小型场景：初始状态、正常获取、资源不足、代谢死亡、年龄死亡；
- 将手算结果与程序输出逐项比较；
- 通过测试注入不一致账本科目，验证系统中止而非纠偏。

Evidence:

- 输入配置；
- 每 tick 手算表；
- 程序状态与差异结果；
- 故障注入的错误输出。

Pass condition:

- 每个小型场景满足设计恒等式；
- 动作/代谢成本进入 dissipated；
- 年龄死亡剩余能量返回资源池；
- 故障注入使运行失败且指出目标 tick 和账本科目；CLI 退出 1、stdout 为空，失败 tick 不增加计数，后续 step/run 和成功摘要均被拒绝。

Failure severity: `Blocker`。

### RV-05：生命周期

Source: `REQ-02`、`REQ-05`、`AC-04`

Required: Yes

Method:

```powershell
python -m pytest -k "lifecycle or death or age or metabolism"
```

Evidence:

- 能量耗尽与年龄上限的前后状态；
- 死亡结算次数；
- 后续 tick 调度集合；
- Agent ID 与最终排序。

Pass condition:

- 两类死亡条件均正确；
- 同 tick 同时满足两个条件仍只死亡一次；
- 死亡后不再调度；
- ID 唯一稳定且不依赖内存地址。

Failure severity: `Major`；重复结算破坏账本时为 `Blocker`。

### RV-06：调度与最终确定性

Source: `REQ-03`、`REQ-07`、`AC-03`

Required: Yes

Method:

```powershell
python -m pytest -k "scheduler or determinism"
```

独立运行 S2 示例两次并逐字节比较 JSON；使用至少两个 seed 运行有资源竞争的配置，记录实际出现不同调度的 seed 对，不要求任意两个 seed 均不同。按设计 REQ-07 的准确字段顺序和 v2 schema 独立重算 digest，比较小场景逐 tick 的只读快照、调度和 RNG 状态。测试底层容器排列变化、重复读取快照、S2 A-B-A 及 S1/S2 混合运行；0/1 个 Agent 调度不消费 RNG。

Evidence:

- 同 seed 两次调度证据与 JSON；
- 不同 seed 的调度证据；
- 容器排序和 RNG 使用的代码位置。

Pass condition:

- 同 seed 输出完全一致；
- 不同 seed 的竞争用例能够改变调度证据；
- 输出始终按稳定 ID 规范化，不受容器遍历影响。

Failure severity: `Blocker`。

### RV-07：稳定性、资源上限与回归

Source: `REQ-01`、`REQ-03`、`REQ-06`、`REQ-07`、`AC-06`

Required: Yes

Method:

```powershell
python -m pytest
python -m pytest -m slow
```

Reviewer 必须实际执行设计第 8 节两个十万 tick 场景，核对长寿 Agent 场景每一步发生获取/代谢，直到末 tick 才年龄死亡；不允许 mock 掉主循环。使用在线断言和累计计数，不让测试完整轨迹掩盖产品内存观察。

配置验证逐项覆盖 REQ-01 的最小值、最大值、超出一单位、bool/float/string/null，world/agent 缺一、未知/重复字段和不安全标签；乘积 1_000_000 接受、超出拒绝，输入边界验证无需实际运行最大负载。验证 S1 原有 60 项测试与 CLI v1 精确输出保持，不得删除或削弱旧断言。

Evidence:

- 完整与 slow 测试结果；
- 两个十万 tick 的最终摘要、有效动作/代谢计数、耗时和 1000/10000/100000 tick 内存/保留容器观察；
- 超限 `initial_count` 与 `max_ticks` 拒绝结果；
- S1 测试结果。

Pass condition:

- 所有测试通过；
- 十万 tick 无账本失败或状态损坏；
- 内存中不保留与 tick 数线性增长的完整历史；
- 超限配置在对象大量分配前失败；
- S1 回归通过。

Failure severity: `Major`；账本或确定性回归为 `Blocker`。

### RV-08：范围控制

Source: S2 范围、`AC-05`、ROADMAP 后续版本

Required: Yes

Method:

- 检查代码、配置、依赖、命令和 README；
- 搜索 genome、VM、copy、reproduce、mutation、lineage、fitness、interaction、position、Parquet、LLM 和网络服务。

Evidence:

- 源文件与依赖列表；
- 疑似越界位置及判断；
- 基线策略的职责说明。

Pass condition:

- 没有 V0.2+ 功能或未批准依赖；
- 基线策略保持无状态且只选择 HARVEST/WAIT；
- README 不宣称演化已发生。

Failure severity: `Major`；引入宿主代码执行或破坏长期边界时为 `Blocker`。

### RV-09：文档与状态

Source: `REQ-01`、`REQ-07`、`AC-06`、设计文档影响

Required: Yes

Method:

- 按 README 从最短路径运行；
- 核对环境、配置、命令、目录、功能和限制；
- 核对 ROADMAP 状态更新是否有 S1/S2 Reviewer 证据。

Evidence:

- README 命令结果；
- 文档差异；
- 支撑状态的 Reviewer 报告路径。

Pass condition:

- README 清楚区分已实现待验收的 S2 和已接受的 S1，最终接受后再同步 S2 状态；
- V0.1 仅在 S1、S2 均满足接受规则后标为 `Completed`；
- 未接受后续版本保持 `Planned`。

Failure severity: `Major`；仅有轻微文字不一致时为 `Minor`。

## 4. 必需测试

以下为计划验证，尚未执行 S2 测试。Reviewer 在独立隔离环境中，从当前仓库根执行 `python -m pip install -e ".[dev]"`，确认安装路径和 Python/依赖版本后执行：

```powershell
python -m pytest
python -m pytest -m slow
python -m minigenesis --config examples/v0.1/s2-resource-world.yaml --output-format json
```

必须保留环境版本、完整命令、退出码、测试总结、S2 JSON、同 seed 比较、不同 seed 调度证据、手工账本表和十万 tick 结果。

## 5. 风险验证

### 数据安全

S2 仍不应创建正式实验文件。所有评审在临时目录进行；验证错误与中止不会覆盖配置或写入未知位置。

### 边界条件

必须覆盖零世界资源、零 inflow、零 harvest、零成本、最小合法 Agent 数、刚好达到 max age、同 tick 同时年龄/能量死亡，以及资源不足的顺序竞争。

### 资源耗尽

验证极大 `initial_count` 和 `max_ticks` 在构造 Agent 或进入循环前被拒绝。若配置可以导致明显失控且无边界，至少为 `Major`。

### 并发

V0.1 不承诺共享世界的并发访问，因此不要求并发正确性测试。若实现主动引入线程或多进程，应视为越界并要求解释或移除。

### 安全边界

确认 S1 的 YAML 安全、无网络、无子进程和无动态代码执行仍成立。任何回归均为 `Blocker`。

## 6. 用户可见行为检查

- S2 示例配置字段在 README 或配置示例中有准确说明；
- 成功摘要能解释最终资源、存活数和能量；
- 账本错误不会伪装成成功；
- 错误信息不要求用户理解内部对象结构；
- 文档不把基线 Agent 称为已进化生命。

## 7. Builder 证据检查

核对 Builder 报告是否为每个 REQ 指出测试位置，并提供配置、摘要、确定性、账本、十万 tick、命令和偏差证据。Reviewer 必须重新执行关键路径，不得仅转述报告。

## 8. 结论规则

- `PASS`：全部 AC 满足，无关键未验证项。
- `PASS WITH DEBT`：仅存在不影响 AC 的已批准遗留项。
- `FAIL`：任一 `Blocker`/`Major` 或 AC 未满足。
- `BLOCKED`：S1 未接受，或环境/证据限制阻止关键验证。

`AC-02`、`AC-03`、`AC-04`、`AC-05` 以及 S1 安全回归不可延期。

## 9. 评审输出

评审结果应新建为 `docs/reviewer/reports/V0.1/S2-report-001.md`；后续重评递增序号，不覆盖历史。本次请求不创建评审报告。

## 10. 追踪与证据要求

采用 S2 Design 第 11.1 节的 REQ/AC/RV 表，不新增设计外需求。RV-07 同时覆盖 REQ-03 的实际十万 tick 调度和无界历史风险。全部 RV 必需；任一缺少关键动态证据均不得 PASS。失败记录在 S2 Reviewer 报告中，包含 REQ/AC/RV、严重性、复现步骤、观察和所需返工。

S1 前置依据为 `docs/reviewer/reports/V0.1/S1-report-001.md` 的 PASS 及 `docs/leader/reports/V0.1/S1-report-004.md` 的 Completed；2026-09-07 合并为 `df98562`。这些不是 S2 验收证据。

## 11. 修订记录

- 2026-08-24：创建初稿；重点覆盖 tick 顺序、独立账本核算、生命周期、确定性、十万 tick 稳定性和范围控制。

- 2026-09-07：同步 S2 Draft 的兼容、配置边界、阶段顺序、错误合同、v2 字节校验、逐 tick 证据及两个长运行场景；保持全部 RV 必需，未执行验收。

- 2026-09-07：用户批准 S2-report-001 决策包；记录批准日期、权威及批准前哈希，状态改为 Approved。技术正文与验收要求保持原批准基线；批准原文见 S2-report-002。
