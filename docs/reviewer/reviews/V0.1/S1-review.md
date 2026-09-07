# V0.1/S1 Reproducible Experiment Baseline Review Plan

## 文档元数据

- Version: `V0.1 Deterministic World`
- Stage: `S1 Reproducible Experiment Baseline`
- Status: `Approved`
- Date: `2026-08-25`
- Approval date: `2026-08-25`
- Approval authority: `PM/user`
- Approval decision: `批准 V0.1/S1 baseline 5BEC61F7...E34D9 + 71C3468C...92FCB`
- Approved draft SHA-256: `71C3468C1A9EFBADBB6BD78A289809C086F580BAAF732B91B6C76ED194692FCB`
- Decision package: `docs/leader/reports/V0.1/S1-report-002.md`
- Governing design: `docs/leader/designs/V0.1/S1-design.md`
- Applicable reworks: 无
- Review scope: S1 的配置、RNG、tick、摘要、CLI、安全与测试基线
- Excluded scope: Agent、资源、VM、遗传、持久化、批量实验及后续版本能力
- Required environment: Python `>=3.11`、可创建隔离虚拟环境并安装本地 `dev` 依赖；关键验证不得依赖网络或外部服务

本计划只细化评审方法，不改变设计范围、行为或验收标准。设计与本计划已经 PM/user 批准；本计划现为从属于获批设计的正式验收权威。

## 1. 评审目标

Reviewer 必须独立确认：

- `REQ-01` 至 `REQ-06` 均有实现和可重复证据；
- `AC-01` 至 `AC-07` 均被独立验证；
- 相同运行输入产生相同规范化结果；
- 无效配置严格失败且不会伪造成功；
- YAML、路径、资源上限和宿主能力边界安全；
- S2 或后续版本能力没有提前进入；
- README 中的命令与状态和实际仓库一致。

## 2. 评审输入

评审前读取：

- `ROADMAP.md` 的范围边界与 `V0.1` 条目；
- `docs/leader/designs/V0.1/S1-design.md`；
- 所有适用于 S1 的已批准 rework（若后续出现）；
- S1 Builder 报告及其中列出的修改文件；
- `pyproject.toml`、CLI、配置、RNG、simulation、summary 与全部测试；
- `README.md` 中的当前状态、运行和测试说明。
- 最新 S1 Leader 工作报告，以及所有编号的 S1 Builder/Reviewer 报告；不得只读取最高编号而忽略仍开放发现。

Builder 报告缺失属于流程发现，但 Reviewer 仍需独立检查，不得据此假定实现成功或失败。

## 3. 评审矩阵

### RV-01：最短运行路径

Source: `REQ-01`、`REQ-02`、`REQ-04`、`REQ-05`、`AC-01`

Required: Yes

Method:

```powershell
python -m pip install -e ".[dev]"
python -m minigenesis --help
python -m minigenesis --config examples/v0.1/s1-baseline.yaml --output-format json
```

Evidence:

- 实际命令、工作目录和退出码；
- help 中的真实参数；
- 完整 JSON 输出；
- `completed_ticks` 与示例配置的对应关系。

Pass condition:

- help 与实际命令一致；
- editable 安装从本仓库声明的元数据成功完成，命令不依赖手工设置 `PYTHONPATH`；
- 示例运行退出码为 `0`；
- stdout 是一个可解析 JSON 对象；
- 必填字段、状态和 digest 存在且含义正确。

Failure severity: `Major`；命令完全无法运行时为 `Blocker`。

### RV-02：严格配置校验

Source: `REQ-02`、`AC-03`

Required: Yes

Method:

- 检查配置 schema 与加载代码；
- 运行配置参数化测试；
- 在临时目录构造缺失字段、未知字段、重复映射键、类型错误、YAML 布尔值冒充整数、负 seed、非法 tick 和不可解析 YAML。

Evidence:

- 相关测试名称和结果；
- 每类失败的退出码及 stderr 摘要；
- 证明在 tick 执行前失败的测试断言。

Pass condition:

- 所有非法配置都被拒绝；
- 未知字段不被静默忽略；
- 重复键不采用“最后一个值获胜”，`true`/`false` 不被当作 seed 或 tick；
- `max_ticks=100_000` 被接受，`100_001` 被拒绝且不进入循环；
- 错误信息可定位问题；
- 不输出成功摘要。

Failure severity: `Major`。

### RV-03：确定性与摘要纯度

Source: `REQ-03`、`REQ-04`、`REQ-05`、`AC-02`

Required: Yes

Method:

```powershell
python -m pytest -k "determinism or summary or tick"
```

另外独立运行示例命令两次，将 stdout 作为 UTF-8 原始字节比较；从输出移除 `digest` 字段后，按设计规定的字段顺序、编码与分隔符独立重算 SHA-256。执行 RNG 模块测试，验证已知 seed 序列、独立实例隔离、不同 seed 差异，并检查空世界 tick 不消费 RNG。

Evidence:

- 两次输出及其 digest；
- 字节比较结果；
- 对全局随机调用、墙上时钟、绝对路径和进程号的代码搜索结果。

Pass condition:

- 两次 JSON 逐字节一致；
- JSON 恰好包含设计规定的八个字段，字段顺序、固定值、末尾单换行与独立重算的 digest 均一致；
- tick 精确到达 `max_ticks`；
- digest 输入中没有未批准的非确定性字段；
- 所有随机调用都经过运行级 RNG 上下文。
- 空世界运行前后的 RNG 状态一致，RNG 单元测试能证明上下文本身可用且相互隔离。

Failure severity: `Blocker`。

### RV-04：进程内运行隔离

Source: `REQ-03`、`REQ-06`、`AC-04`

Required: Yes

Method:

- 检查运行工厂与对象生命周期；
- 执行 A、B、A 顺序的集成测试；
- 检查模块级可变对象、缓存和 RNG 状态。

Evidence:

- A1、B、A2 的规范化摘要；
- A1/A2 相等断言；
- 相关代码位置与测试结果。

Pass condition:

- A1 与 A2 完全一致；
- B 的不同 seed/配置不会影响 A2；
- 没有跨运行可变状态泄漏。

Failure severity: `Major`。

### RV-05：YAML 与宿主安全边界

Source: `REQ-02`、`REQ-04`、`AC-05`、设计安全评估

Required: Yes

Method:

- 审查 YAML 加载 API；
- 使用能触发对象构造的恶意 YAML 标签和重复键执行安全测试；
- 检查网络、子进程、动态导入、`eval`/`exec` 和文件写入。

Evidence:

- 安全测试输入、退出码和无副作用证明；
- 依赖及源码检查结果；
- 临时目录在失败前后的文件差异。

Pass condition:

- 恶意标签仅导致安全解析失败；
- CLI 运行时没有对象构造、命令执行、网络或文件写入；安装器与测试框架自身的环境写入不计为 CLI 运行时副作用；
- `100_001` tick 在运行前拒绝。

Failure severity: `Blocker`。

### RV-06：测试与 README 一致性

Source: `REQ-01` 至 `REQ-06`、`AC-06`

Required: Yes

Method:

在新的隔离虚拟环境中执行 `python -m pip install -e ".[dev]"`，再执行：

```powershell
python -m pytest
```

将 README 的环境、命令、状态、目录和能力描述逐项与仓库核对。

Evidence:

- 测试命令、退出码和总结；
- Python 版本、隔离环境位置、安装命令、解析后的直接依赖版本；
- README 核对清单；
- 未运行测试及影响。

Pass condition:

- 完整测试通过；
- 干净环境安装成功且没有未声明依赖；
- README 中每条当前能力和命令都有仓库证据；
- README 没有把 S2 或后续能力描述为已实现。

Failure severity: 测试失败为 `Major`；关键测试无法运行时结论为 `BLOCKED`。

### RV-07：范围控制

Source: 设计范围与 `AC-07`

Required: Yes

Method:

- 检查源代码、配置、依赖和公开命令；
- 搜索 Agent、resource、genome、VM、reproduction、mutation、lineage、Parquet、UI 和网络能力。

Evidence:

- 修改文件列表；
- 依赖列表；
- 对疑似越界内容的代码位置和用途判断。

Pass condition:

- 没有后续阶段功能或未批准的大型依赖；
- 测试夹具中的词汇不会形成产品能力；
- 与阶段无关的重构不影响接受路径。

Failure severity: `Major`；改变架构或安全边界时为 `Blocker`。

## 4. 必需测试

Reviewer 必须从仓库根目录执行：

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m minigenesis --config examples/v0.1/s1-baseline.yaml --output-format json
```

必须在新建的隔离虚拟环境中执行并保留：Python 与解析后的直接依赖版本、完整命令、退出码、测试总结、示例 JSON、两次运行的原始字节比较、独立 digest 重算、RNG 序列/空世界不消费验证和临时安全测试结果。若 Builder 报告的实际安装步骤与设计不同，Reviewer 应记录设计偏差，不得用未批准的新步骤替代规定路径后宣告通过。

## 5. 风险验证

### 数据安全

本阶段不应写正式数据。使用临时目录运行合法与非法配置，验证目录中除 Reviewer 主动保存的证据外没有新增或覆盖文件。

### 失败路径

验证缺失文件、目录冒充文件、不可读文件、语法错误、重复键、未知字段和超限 tick。任一输入导致 traceback 泄露并以成功码退出，均为 `Major`。

### 资源边界

验证 `100_000` 边界可运行、`100_001` 在创建长循环前失败。上限不同、缺失或可绕过时为 `Major`。

### 并发

S1 不承诺多进程共享状态或并发执行，因此不要求并发压力测试；但实现不得引入共享外部服务。

## 6. 用户可见行为检查

- help 清楚说明必填配置与输出格式；
- 成功输出不混入调试日志；
- 错误输出说明文件或字段原因；
- text 与 JSON 含义一致；
- JSON stdout 只包含单个规范化对象，不混入日志；
- README 不提供未验证命令；
- 中文文档与英文代码标识不互相矛盾。

## 7. Builder 证据检查

Reviewer 必须核对 Builder 报告是否包含设计要求的版本、文件、命令、结果、确定性证据、未验证项和偏差。缺失证据记录为流程发现；关键路径仍须由 Reviewer 重新运行。

## 8. 追踪完整性

Reviewer 必须逐项确认以下链路；任一 mandatory 链路无法执行时，不得靠推断补足：

| Review item | Source | Acceptance |
|---|---|---|
| `RV-01` | `REQ-01`, `REQ-02`, `REQ-04`, `REQ-05` | `AC-01` |
| `RV-02` | `REQ-02` | `AC-03` |
| `RV-03` | `REQ-03`, `REQ-04`, `REQ-05` | `AC-02` |
| `RV-04` | `REQ-03`, `REQ-06` | `AC-04` |
| `RV-05` | `REQ-02`, `REQ-04`、安全评估 | `AC-05` |
| `RV-06` | `REQ-01` 至 `REQ-06` | `AC-06` |
| `RV-07` | 阶段范围与禁止项 | `AC-07` |

## 9. 结论规则

- `PASS`：全部 AC 满足，无关键未验证项。
- `PASS WITH DEBT`：仅存在不影响 AC 的明确遗留项，并已由用户或 Leader 批准延期。
- `FAIL`：任一 `Blocker`/`Major` 发现或 AC 未满足。
- `BLOCKED`：环境、权限、依赖或证据限制使关键路径无法验证。

`AC-02`、`AC-03`、`AC-04`、`AC-05`、`AC-07` 不得作为技术债延期。

## 10. 评审输出

评审结果应新建在 `docs/reviewer/reports/V0.1/S1-report-xxx.md`，其中 `xxx` 为评审开始时该阶段下一个未占用的三位序号（按当前仓库预计为 `001`）；重评递增序号，不得覆盖历史报告。本次请求不创建评审报告。

## 11. 修订记录

- 2026-08-24：创建初稿；建立从 `REQ/AC` 到 `RV`、命令和证据的完整评审路径。
- 2026-08-25：补充干净环境安装、精确配置边界、RNG 空世界不消费、独立 digest 重算、显式 RV 追踪与动态报告编号，消除实施和验收双方可能采用不同命令或规范化规则的歧义。
- 2026-08-25：对齐 `RV-04`/`RV-05` 正文的 Source 标注与已有追踪表；未改变评审方法、覆盖范围或验收标准。
- 2026-08-25：PM/user 批准 Report 002 映射的精确 Draft 基线；仅记录批准并将生命周期转为 `Approved`，未改变评审方法、覆盖范围或通过标准。
