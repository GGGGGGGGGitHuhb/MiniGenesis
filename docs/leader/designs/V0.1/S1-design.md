# V0.1/S1 Reproducible Experiment Baseline Design

## 文档元数据

- Version: `V0.1 Deterministic World`
- Stage: `S1 Reproducible Experiment Baseline`
- Status: `Approved`
- Date: `2026-08-25`
- Approval date: `2026-08-25`
- Approval authority: `PM/user`
- Approval decision: `批准 V0.1/S1 baseline 5BEC61F7...E34D9 + 71C3468C...92FCB`
- Approved draft SHA-256: `5BEC61F77F5471DDBD59E3DCBDE4B1F7E17C8C87DCB652BCA40804ECA03E34D9`
- Decision package: `docs/leader/reports/V0.1/S1-report-002.md`
- Roadmap: `ROADMAP.md / V0.1`
- Rework documents: 无

本设计已经 PM/user 批准，现为 Builder 与 Reviewer 的阶段权威。对应评审计划为 `docs/reviewer/reviews/V0.1/S1-review.md`；评审计划只能细化验证方法，不能改变本设计的范围或验收标准。

## 1. 阶段目标

建立 MiniGenesis 的最小可执行实验骨架，使用户可以加载一份显式配置，在给定 seed 下运行有限数量的空世界 tick，并得到稳定、可比较的规范化摘要。

本阶段的价值不是模拟生命，而是先证明配置、随机性、时间推进和输出边界可控，为 `S2` 的资源世界提供可信基线。

前置条件：无。当前仓库只有规划文档，没有需要兼容的程序行为或数据格式。

## 2. 范围与边界

### 2.1 必须包含

- Python 包结构、依赖声明和命令行入口。
- YAML 实验配置读取、严格校验和规范化。
- 单一、显式 seed 的随机数上下文。
- 单调递增的整数 tick。
- 有限步运行；默认或显式上限必须阻止无意无限执行。
- 机器可比较的规范化运行摘要。
- 自动测试与一份最小示例配置。

### 2.2 明确排除

- World 资源、Agent、动作、代谢和死亡；这些属于 `S2`。
- Genome、VM、繁殖、变异和谱系；这些属于 `V0.2`。
- 正式实验目录、Parquet、批量 seed、指标和图表；这些属于 `V0.3`。
- NumPy 数组优化、并行、GPU、UI、网络和外部服务。

### 2.3 停止并确认条件

Builder 在以下情况下必须停止扩大实现并请求 Leader 或用户决定：

- 需要改变 `V0.1` 的目标或新增持久化格式；
- 认为必须加入 Agent 或资源才能完成 `S1`；
- 需要网络服务、数据库或非 Python 运行时；
- 无法在不依赖全局随机状态的情况下实现确定性。

## 3. 需求

### REQ-01：项目与命令入口

系统必须是声明支持 Python `>=3.11` 的 `src/` 布局 Python 项目，并提供开发/评审依赖组 `dev`。从仓库根目录执行 `python -m pip install -e ".[dev]"` 后，必须可通过 `python -m minigenesis` 运行；不得依赖未记录的 `PYTHONPATH` 或工作站全局包碰巧可用。

命令必须接受：

- `--config PATH`：必填 YAML 配置路径；
- `--output-format text|json`：默认 `text`，`json` 用于稳定比较；
- `--help`：说明当前真实可用的参数。

成功时退出码为 `0`；配置或输入错误时退出码非 `0`，且不打印 Python traceback 作为普通用户错误界面。

### REQ-02：配置模型与校验

首版配置必须至少包含：

```yaml
experiment:
  name: s1-baseline
  seed: 1
  max_ticks: 10
```

约束：

- `name`：字符串，去除首尾空白后必须非空；规范化配置保存去除首尾空白后的值；
- `seed`：非负整数；YAML 布尔值不得按整数接受；
- `max_ticks`：`1..100_000` 的整数；YAML 布尔值不得按整数接受，`100_000` 是本阶段固定硬上限；
- 未知字段、重复映射键、缺失字段、错误类型和不可解析 YAML 必须失败，不得静默采用猜测值；
- 配置加载后形成不可变或不被运行过程修改的规范化配置对象。

### REQ-03：随机数上下文

- 所有随机操作必须通过一次运行专属的 RNG 上下文取得。
- 禁止业务模块直接使用 Python 模块级随机状态或自行创建未登记的随机源。
- 摘要必须记录 seed 和 RNG 实现标识。
- RNG 上下文必须封装独立的 `random.Random(seed)` 实例，稳定实现标识固定为 `python.random.Random/MT19937`；不得把对象地址或 Python 补丁版本写入标识。
- 空世界 tick 不得为了“证明随机性”而虚耗随机数；RNG 序列与不同 seed 的差异由 RNG 模块单元测试验证，S2 再消费该上下文。
- 本阶段只承诺在相同代码、依赖、运行环境与配置下可复现，不承诺跨任意依赖版本产生相同序列。

### REQ-04：时间推进

- tick 从 `0` 开始表示初始状态。
- 每完成一个空世界步骤，tick 精确增加 `1`。
- 运行在 `tick == max_ticks` 时结束。
- 运行循环不得读取墙上时钟决定模拟行为。

### REQ-05：规范化摘要

成功 JSON 输出必须恰好使用以下顶层字段和顺序：

1. `schema_version`：固定为字符串 `minigenesis.summary.v1`；
2. `experiment_name`：规范化后的配置名称；
3. `seed`：配置 seed；
4. `rng_implementation`：固定为 `python.random.Random/MT19937`；
5. `requested_ticks`：配置 `max_ticks`；
6. `completed_ticks`：成功时等于 `requested_ticks`；
7. `status`：成功时固定为 `completed`；
8. `digest`：`sha256:` 加 64 位小写十六进制摘要。

digest 输入是上述前七个字段构成的对象，不包含 `digest` 自身。使用 UTF-8 编码、JSON `ensure_ascii=False`、分隔符 `(',', ':')`、不追加换行；字段按上述插入顺序序列化，再计算 SHA-256。CLI 输出同一完整对象时使用相同规范化规则并在末尾只追加一个换行，因此同输入 stdout 可逐字节比较。digest 与 JSON 不得包含绝对路径、墙上时间、进程号或其他非确定性值。人类可读文本可以调整措辞，但含义必须与 JSON 一致。

### REQ-06：进程内隔离

同一进程依次运行两个实验时，第二个实验不得继承第一个实验的 tick、RNG 状态、配置或摘要缓存。

## 4. 目录与文件影响

预期新增：

```text
pyproject.toml
src/minigenesis/
    __init__.py
    __main__.py
    cli.py
    config.py
    rng.py
    simulation.py
    summary.py
examples/v0.1/s1-baseline.yaml
tests/
    test_cli.py
    test_config.py
    test_determinism.py
    test_simulation.py
    test_summary.py
```

职责边界：

- `cli.py`：参数、退出码和用户信息；不得持有模拟状态。
- `config.py`：解析、校验、规范化配置；不得创建 RNG。
- `rng.py`：创建和标识运行级 RNG；不得读取配置文件。
- `simulation.py`：持有 tick 并驱动有限步骤；不得打印或写文件。
- `summary.py`：从完成状态产生规范化摘要和 digest；不得改变模拟状态。

文件清单是影响预测。Builder 可作最小调整，但必须在实现报告中解释有意义的偏差；不得借调整引入本阶段排除功能。

## 5. 核心流程

1. 用户从仓库根目录执行 `python -m pip install -e ".[dev]"`，建立本仓库声明的运行与测试依赖。
2. 用户执行 `python -m minigenesis --config examples/v0.1/s1-baseline.yaml --output-format json`。
3. CLI 解析参数并将路径交给配置模块。
4. 配置模块读取 YAML，完成结构、重复键、类型、范围和未知字段校验。
5. 运行工厂从规范化配置创建独立 RNG 上下文和初始 `tick = 0` 的 Simulation。
6. Simulation 在无墙上时钟参与、且不虚耗随机数的情况下执行 `max_ticks` 次空步骤。
7. Summary 从最终状态生成规范化结构和 digest。
8. CLI 输出摘要并以 `0` 退出。
9. 任一步骤失败时，CLI 不向 stdout 输出成功摘要，只向 stderr 输出简洁错误并以非零码退出。

## 6. 错误与恢复

- 配置文件不存在、不可读或不是普通文件：失败，不创建替代配置。
- YAML 语法错误、重复映射键或字段非法：列出可定位的字段路径与原因，不开始运行。
- `max_ticks` 超过硬上限：拒绝运行，不自动截断。
- 未知异常：允许在开发诊断模式保留 traceback，但默认 CLI 必须给出非零退出与简洁错误；不得伪造成功摘要。
- 本阶段不写正式实验数据，因此失败后没有迁移或回滚流程。

## 7. 安全评估

- 配置只作为数据解析，不允许 YAML 构造任意 Python 对象；必须使用安全加载方式。
- 配置内容不得作为代码、命令、模块名或动态导入目标执行。
- 本阶段不访问网络、不启动子进程、不删除或覆盖用户文件。
- 除用户指定配置外，运行不得读取仓库外的隐式状态。

## 8. 性能与资源约束

- `max_ticks` 硬上限固定为 `100_000`，以覆盖 S2 已规划的十万 tick 验证，同时避免 S1 接受后再改变配置语义。
- 空世界运行的内存使用不应随 tick 数线性增长；S1 不保存逐 tick 历史。
- 不为本阶段引入并行、缓存或预优化。

## 9. Builder 实施要求

推荐顺序：项目配置与测试入口 → 配置模型 → RNG 上下文 → Simulation → 摘要/digest → CLI 集成 → README 更新。

Builder 可决定具体类名、异常层次和 YAML 库，但不得改变命令入口、严格校验、集中 RNG、有限执行、摘要确定性和进程内隔离。

Builder 报告必须记录：

- 实际 Python 与依赖版本；
- 所有修改文件及用途；
- 从干净虚拟环境执行的安装、运行和测试命令及观察结果；
- 同 seed 比较证据；
- 未运行的验证及原因；
- 与本设计的任何偏差。

## 10. 测试设计

Builder 必须建立并执行：

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m minigenesis --config examples/v0.1/s1-baseline.yaml --output-format json
```

自动测试至少覆盖：

- 合法最小配置；
- 缺失、未知、重复映射键、错误类型、布尔值冒充整数、负 seed、零/负/超过 `100_000` 的 `max_ticks`；
- YAML 安全加载；
- tick 的初值、单步和终止边界；
- 同 seed/配置运行两次的完整 JSON 相等；
- RNG 上下文的已知 seed 序列、独立实例隔离与不同 seed 序列差异；
- 空世界 tick 不消费 RNG；
- 同进程连续运行相互隔离；
- JSON 精确字段、顺序、规范化字节、digest 重算与末尾单换行；
- JSON 中不含绝对路径、墙上时间或进程号；
- 正常和错误退出码。

## 11. 验收标准

### AC-01：最短运行路径

关联：`REQ-01`、`REQ-02`、`REQ-04`、`REQ-05`。

在干净虚拟环境中完成设计规定的 editable 安装后，从仓库根目录执行示例命令，进程以 `0` 退出，`completed_ticks` 等于配置的 `max_ticks`，并输出可解析的单个 JSON 摘要。由 Reviewer 独立运行验证。

### AC-02：确定性

关联：`REQ-03`、`REQ-04`、`REQ-05`。

在相同代码、依赖、环境、配置和 seed 下独立运行两次，规范化 JSON（包括 digest）逐字节一致；Reviewer 按本设计重算 digest 并得到相同值。由自动测试和 Reviewer 命令行复验共同验证。

### AC-03：严格失败

关联：`REQ-01`、`REQ-02`。

对每类无效配置，程序在执行 tick 前以非零码退出，stderr 指明问题字段或文件原因，不输出成功摘要。由参数化自动测试验证。

### AC-04：运行隔离

关联：`REQ-03`、`REQ-06`。

同一进程依次运行 A、B、A 三次，前后两次 A 摘要一致，B 不受 A 的 tick 或 RNG 状态影响。由集成测试验证。

### AC-05：安全与资源边界

关联：`REQ-02`、`REQ-04`。

恶意 YAML 标签不能构造或执行 Python 对象；重复键和超过 `100_000` 的运行被拒绝；S1 运行时不访问网络、不启动子进程且不写正式实验文件。由安全测试与代码检查验证。安装与测试工具自身的环境写入不属于 CLI 运行时行为。

### AC-06：测试基线

关联：`REQ-01` 至 `REQ-06`。

`python -m pip install -e ".[dev]"` 与 `python -m pytest` 在干净虚拟环境中成功，README 只记录实际验证过的 Python 范围、安装、运行和测试命令。失败必须记录在 Reviewer 报告，不得标记阶段完成。

### AC-07：阶段边界

关联：第 2 节范围与边界、全部需求。

实现及其公开配置、命令和依赖不包含 S2 的 World/Agent/资源能力，也不包含 V0.2+ 的 VM、繁殖、变异、谱系、正式实验持久化、批量实验、UI、网络服务或其他明确排除项。由 Reviewer 对源代码、依赖、配置、命令和 README 独立检查；越界内容不得作为技术债保留后通过。

## 12. 需求与验收追踪

| Requirement | Acceptance | Reviewer item |
|---|---|---|
| `REQ-01` | `AC-01`, `AC-03`, `AC-06` | `RV-01`, `RV-02`, `RV-06` |
| `REQ-02` | `AC-01`, `AC-03`, `AC-05`, `AC-06` | `RV-01`, `RV-02`, `RV-05`, `RV-06` |
| `REQ-03` | `AC-02`, `AC-04`, `AC-06` | `RV-03`, `RV-04`, `RV-06` |
| `REQ-04` | `AC-01`, `AC-02`, `AC-05`, `AC-06` | `RV-01`, `RV-03`, `RV-05`, `RV-06` |
| `REQ-05` | `AC-01`, `AC-02`, `AC-06` | `RV-01`, `RV-03`, `RV-06` |
| `REQ-06` | `AC-04`, `AC-06` | `RV-04`, `RV-06` |
| 第 2 节范围与边界 | `AC-07` | `RV-07` |

## 13. Reviewer 重点

- 检查是否存在隐藏全局 RNG 或墙上时间输入。
- 检查 digest 是否混入路径、时间或进程信息。
- 检查 YAML 是否安全加载。
- 检查 `S2` 的 Agent、资源等功能是否提前进入。
- 独立重复运行，不以 Builder 报告作为唯一证据。
- `AC-02`、`AC-03`、`AC-04`、`AC-05`、`AC-07` 不可延期而不改变阶段接受标准。

## 14. 文档影响

接受后更新 `README.md`：当前状态、实际环境、最短运行路径、测试命令和真实目录结构。未经 Reviewer 接受，不得将 `V0.1/S1` 标记为 `Completed`。

当前不存在 `ARCHITECTURE.md` 或 `TECH-DEBT-TRACKER.md`。本设计不据此新增长期架构或技术债权威；若 Builder 发现必须改变全局架构或形成需批准延期的跨阶段问题，必须停止并请求 Leader/用户补充相应权威。

## 15. 修订记录

- 2026-08-24：创建初稿；将 S1 限定为配置、RNG、tick、摘要和测试基线，排除资源世界与正式实验持久化。
- 2026-08-25：补齐 `src/` 布局的安装路径、精确配置边界、RNG 空世界消费规则、规范化 JSON/digest 合同与 REQ→AC→RV 追踪；固定 `max_ticks=100_000` 以消除与 S2 长运行验证的接口歧义。
- 2026-08-25：PM/user 批准 Report 002 映射的精确 Draft 基线；仅记录批准并将生命周期转为 `Approved`，未改变范围、行为、接口、技术基线或验收标准。
