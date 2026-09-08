# MiniGenesis

MiniGenesis 是一个极简数字演化实验项目。`V0.1` 已完成，S1 与 S2 均通过独立评审。当前实现包含可复现实验骨架、资源世界、基线 Agent、代谢与死亡。用户可以从严格校验的 YAML 配置和显式 seed 运行有限 tick，并得到带守恒账本、可逐字节比较的摘要。

项目原则是：**Specify laws, not outcomes（规定规律，而不是规定结果）**。

## 当前状态

- 当前版本：`V0.1 Deterministic World` — `Completed`
- 已完成阶段：`S1 Reproducible Experiment Baseline` — `Completed`（Reviewer `PASS`）
- 已完成阶段：`S2 Resource World and Lifecycle` — `Completed`（Reviewer `PASS`）
- 下一阶段：`V0.2/S1 Genome and Sandboxed VM` — `Planned`，尚未实施
- 工作流状态：S2 `Completed`，已完成独立验收与 Leader 收尾
- S1 历史验收环境：Windows 11、Python `3.13.9`
- S2 Builder 与独立 Reviewer 验证环境：WSL2 Linux、Python `3.12.3`
- 声明支持的 Python：`>=3.11`

`S1` 已由 `docs/reviewer/reports/V0.1/S1-report-001.md` 给出 `PASS`，没有 finding、技术债或关键未验证项。`S2` 已由 `docs/reviewer/reports/V0.1/S2-report-001.md` 给出 `PASS`，无 finding、返工、技术债或关键未验证项。S1、S2 均已接受，故 `V0.1` 为 `Completed`；V0.2 及以后仍为 `Planned`。

## 当前能力

- 从 UTF-8 YAML 加载 `experiment.name`、`seed` 和 `max_ticks`。
- 拒绝缺失、未知、重复、类型或范围非法的字段，以及不安全 YAML 标签。
- 为每次运行创建独立的 `python.random.Random/MT19937` RNG 上下文。
- 从 tick `0` 运行到显式有限边界，硬上限为 `100_000`。
- 输出人类可读文本或带 SHA-256 digest 的规范化 JSON。
- 同一进程内的 A-B-A 多次运行彼此隔离，包括 S1/S2 混合运行。
- S2：全局资源注入、按稳定 ID 与运行级 RNG 调度，先生成全部意图再顺序结算 HARVEST/WAIT。
- S2：动作成本、基础代谢、年龄和能量死亡；年龄死亡剩余能量返回资源池。
- S2：每 tick 核验守恒；`Simulation.snapshot()` 返回嵌套只读的最新完整状态，不累计历史。
- S2：失败 tick 不发布部分快照、不推进 tick；失败运行不能继续或生成成功摘要。

## 环境与依赖

- Python：`>=3.11`
- 包管理：`pip`
- 运行依赖：`PyYAML>=6.0,<7`
- 开发/测试依赖：`pytest>=8,<10`
- 外部服务：无

S1 历史验收在 Windows 11 / Python 3.13.9 上完成。S2 本次 Builder 与独立 Reviewer 验证使用 WSL2 Linux / Python 3.12.3、PyYAML 6.0.3、pytest 9.1.1；不代表当前 S2 已验证 Windows 或全部 Python 版本。

## 快速开始

Shell：PowerShell 或已激活隔离环境的 Linux shell

工作目录：仓库根目录。先激活一个 Python `>=3.11` 的隔离环境，再执行：

```powershell
python -m pip install -e ".[dev]"
python -m minigenesis --config examples/v0.1/s2-resource-world.yaml --output-format json
```

成功时退出码为 `0`，stdout 是一个以单换行结尾的 JSON 对象，其中 `completed_ticks` 与 S2 示例的 `max_ticks` 都是 `30`，`status` 是 `completed`。最终资源为 `310`、存活 `0`、死亡 `3`，账本为 `100 + 30 + 300 = 310 + 0 + 120`。S1 示例仍使用原有 v1 摘要。

## 常用命令

查看真实命令参数：

```powershell
python -m minigenesis --help
```

使用默认文本输出：

```powershell
python -m minigenesis --config examples/v0.1/s1-baseline.yaml
```

运行完整测试：

```powershell
python -m pytest
```

## 配置

最小配置见 `examples/v0.1/s1-baseline.yaml`：

```yaml
experiment:
  name: s1-baseline
  seed: 1
  max_ticks: 10
```

- `name`：去除首尾空白后必须是非空字符串。
- `seed`：非负整数；布尔值不作为整数接受。
- `max_ticks`：`1..100000` 的整数；布尔值不作为整数接受。
- 所有字段必填；未知字段和重复映射键会导致失败。

S2 完整配置见 `examples/v0.1/s2-resource-world.yaml`。根字段只允许 `experiment`，或同时包含 `experiment`、`world`、`agent`，所有内层字段必填：

| 配置字段 | 整数闭区间 | 示例值 |
|---|---|---|
| world.initial_resource | 0..1000000 | 100 |
| world.resource_inflow_per_tick | 0..1000000 | 10 |
| world.harvest_amount | 0..1000000 | 4 |
| world.action_cost | 0..1000000 | 1 |
| world.metabolism_cost | 0..1000000 | 1 |
| agent.initial_count | 1..1000 | 3 |
| agent.initial_energy | 1..1000000 | 10 |
| agent.max_age | 1..100000 | 20 |

S2 还要求 `max_ticks * initial_count <= 1000000`，分配 Agent 前校验；所有数值拒绝 bool、浮点、字符串与 null。累计账本使用 Python 整数，不受输入上限截断。

只有 experiment 时完整保留 S1 空世界、v1 JSON 与文本合同；S2 使用 `minigenesis.summary.v2`，包含完整 world/agent 配置、资源、存活/死亡数、账本和按 ID 排序的全部 Agent。digest 为无换行规范 JSON 的 SHA-256，stdout 仅追加一个 LF。配置错误退出 2；运行/内部一致性错误退出 1、stderr 给原因、stdout 为空。

配置没有环境变量或命令行覆盖层。CLI 只读取 `--config` 指定的文件；运行不会创建正式实验数据、访问网络或启动子进程。配置/输入错误写入 stderr、返回非零码，并且不会向 stdout 伪造成功摘要。

## 项目结构

```text
.
├── examples/v0.1/                 # S1/S2 示例配置
├── src/minigenesis/               # 配置、RNG、World/Agent、账本、tick、摘要和 CLI
├── tests/                         # S1 回归与 S2 生命周期、确定性、长运行测试
├── docs/
│   ├── leader/                    # 设计、决策和生命周期记录
│   ├── builder/                   # 实现报告
│   └── reviewer/                  # 评审计划、验收报告与原始证据
├── pyproject.toml                 # Python、依赖、包和 pytest 配置
├── README.md
└── ROADMAP.md
```

构建输出与隔离验证环境位于被 Git 忽略的 `build/`。S2 Builder 与 Reviewer 原始验证日志和可重跑 harness 分别保存在 `docs/builder/evidence/V0.1/S2/` 与 `docs/reviewer/evidence/V0.1/S2/`，属于开发证据，不是正式实验数据。

## 测试与验证

在已安装 `.[dev]` 的隔离环境中执行：

```powershell
python -m pytest
python -m minigenesis --config examples/v0.1/s1-baseline.yaml --output-format json
```

S1 历史 Builder 和独立 Reviewer 的完整测试结果均为 `60 passed`；Reviewer 另执行了 `37 passed` 定向测试、`48 passed` 关键路径测试和独立验证 harness。测试覆盖严格配置、重复键和 YAML 安全、tick 边界、RNG 隔离与空 tick 不消费、A-B-A 运行隔离、精确 JSON/digest/UTF-8/单换行，以及 CLI 成功与错误退出。

S2 Builder 完整测试为 `190 passed`，独立 Reviewer 完整测试同为 `190 passed`；两者分别单独执行 slow 测试，均为 `2 passed`。Reviewer 另通过六组手算账本、120 个独立参考模型场景、精确 CLI 字节与故障注入，并独立观察两个十万 tick 场景。

S2 验证包括配置全边界、阶段顺序、动作拒绝、两类死亡、逐 tick 独立核账、故障锁定、精确 v1/v2 字节、调度及 A-B-A。两个 slow 场景真实运行 100000 tick：示例死亡后持续注入，以及每 tick 保持动作/代谢直到末 tick 的长寿 Agent。

```sh
python -m pytest --capture=sys -rP
python -m pytest --capture=sys -rP -m slow
```

本次 WSL `/mnt/e` 挂载卷的 pytest 默认 fd capture 出现匿名临时文件 truncate 错误，因此使用内存中的 `--capture=sys`。在仓库内设置任务专用 `TMPDIR`/`TEMP`/`TMP` 与 pytest `--basetemp`、`-o cache_dir=...`，避免依赖系统临时目录。具体执行命令、失败历史、环境和测试结果见 S2 Builder 与 Reviewer 报告；Reviewer 已使用独立环境完成验证。

## 文档索引

- `ROADMAP.md`：版本目标、阶段顺序、边界和完成规则。
- `docs/leader/designs/V0.1/S1-design.md`：已批准的 S1 范围、需求与验收标准。
- `docs/reviewer/reviews/V0.1/S1-review.md`：已批准的独立评审计划。
- `docs/leader/reports/V0.1/`：S1/S2 决策、批准与收尾记录。
- `docs/builder/reports/V0.1/`：S1/S2 实现和 Builder 验证记录。
- `docs/reviewer/reports/V0.1/S1-report-001.md`：S1 独立验收证据与 `PASS` 结论。

- `docs/leader/designs/V0.1/S2-design.md`：已批准的 S2 技术基线。
- `docs/reviewer/reviews/V0.1/S2-review.md`：已批准的 S2 独立评审计划。
- `docs/reviewer/reports/V0.1/S2-report-001.md`：S2 独立验收与 `PASS`。
- `docs/leader/reports/V0.1/S2-report-003.md`：S2 与 V0.1 收尾依据。

## 已知限制

- S1 输入运行空世界；S2 基线策略仅按资源是否大于零选择 HARVEST/WAIT，没有遗传行为或策略系统。
- 不包含 Genome/VM、繁殖、变异、谱系、正式实验持久化、批量实验、UI 或网络服务。
- 可复现承诺限定于相同代码、依赖、运行环境、配置和 seed，不承诺跨任意依赖版本产生相同结果。
- 当前没有 `ARCHITECTURE.md` 或 `TECH-DEBT-TRACKER.md`。

## License

仓库当前没有 `LICENSE` 文件。
