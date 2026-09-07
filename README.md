# MiniGenesis

MiniGenesis 是一个极简数字演化实验项目。`V0.1/S1` 已通过独立评审，现提供可复现实验骨架：用户可以从严格校验的 YAML 配置和显式 seed 运行有限数量的空世界 tick，并得到稳定、可逐字节比较的摘要。

项目原则是：**Specify laws, not outcomes（规定规律，而不是规定结果）**。

## 当前状态

- 当前版本：`V0.1 Deterministic World` — `In Progress`
- 已完成阶段：`S1 Reproducible Experiment Baseline` — `Completed`（Reviewer `PASS`）
- 下一阶段：`S2 Resource World and Lifecycle` — `Planned`
- 工作流状态：V0.1/S1 已收尾；V0.1 等待 S2 实现与验收
- 已验证环境：Windows 11、Python `3.13.9`
- 声明支持的 Python：`>=3.11`

`S1` 已由 `docs/reviewer/reports/V0.1/S1-report-001.md` 给出 `PASS`，没有 finding、技术债或关键未验证项。`V0.1/S2` 的资源世界尚未实现或验收，因此 `V0.1` 仍为 `In Progress`，不是 `Completed`。

## 当前能力

- 从 UTF-8 YAML 加载 `experiment.name`、`seed` 和 `max_ticks`。
- 拒绝缺失、未知、重复、类型或范围非法的字段，以及不安全 YAML 标签。
- 为每次运行创建独立的 `python.random.Random/MT19937` RNG 上下文。
- 从 tick `0` 运行到显式有限边界，硬上限为 `100_000`。
- 输出人类可读文本或带 SHA-256 digest 的规范化 JSON。
- 同一进程内的 A-B-A 多次运行彼此隔离。

## 环境与依赖

- Python：`>=3.11`
- 包管理：`pip`
- 运行依赖：`PyYAML>=6.0,<7`
- 开发/测试依赖：`pytest>=8,<10`
- 外部服务：无

本阶段在 Windows 11 / Python 3.13.9、PyYAML 6.0.3、pytest 9.1.1 上完成 Builder 与独立 Reviewer 验证；其他操作系统尚未独立验证。

## 快速开始

Shell：PowerShell

工作目录：仓库根目录。先激活一个 Python `>=3.11` 的隔离环境，再执行：

```powershell
python -m pip install -e ".[dev]"
python -m minigenesis --config examples/v0.1/s1-baseline.yaml --output-format json
```

成功时退出码为 `0`，stdout 是一个以单换行结尾的 JSON 对象，其中 `completed_ticks` 与示例的 `max_ticks` 都是 `10`，`status` 是 `completed`。

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

配置没有环境变量或命令行覆盖层。CLI 只读取 `--config` 指定的文件；运行不会创建正式实验数据、访问网络或启动子进程。配置/输入错误写入 stderr、返回非零码，并且不会向 stdout 伪造成功摘要。

## 项目结构

```text
.
├── examples/v0.1/                 # S1 最小示例配置
├── src/minigenesis/               # 配置、RNG、tick、摘要和 CLI
├── tests/                         # S1 自动化测试
├── docs/
│   ├── leader/                    # 设计、决策和生命周期记录
│   ├── builder/                   # 实现报告
│   └── reviewer/                  # 评审计划与后续验收报告
├── pyproject.toml                 # Python、依赖、包和 pytest 配置
├── README.md
└── ROADMAP.md
```

构建输出、隔离验证环境和原始测试日志位于被 Git 忽略的 `build/` 下，不属于程序输入或正式实验数据。

## 测试与验证

在已安装 `.[dev]` 的隔离环境中执行：

```powershell
python -m pytest
python -m minigenesis --config examples/v0.1/s1-baseline.yaml --output-format json
```

Builder 和独立 Reviewer 的完整测试结果均为 `60 passed`；Reviewer 另执行了 `37 passed` 定向测试、`48 passed` 关键路径测试和独立验证 harness。测试覆盖严格配置、重复键和 YAML 安全、tick 边界、RNG 隔离与空 tick 不消费、A-B-A 运行隔离、精确 JSON/digest/UTF-8/单换行，以及 CLI 成功与错误退出。

## 文档索引

- `ROADMAP.md`：版本目标、阶段顺序、边界和完成规则。
- `docs/leader/designs/V0.1/S1-design.md`：已批准的 S1 范围、需求与验收标准。
- `docs/reviewer/reviews/V0.1/S1-review.md`：已批准的独立评审计划。
- `docs/leader/reports/V0.1/`：S1 决策与批准生命周期记录。
- `docs/builder/reports/V0.1/`：S1 实现和 Builder 验证记录。
- `docs/reviewer/reports/V0.1/S1-report-001.md`：S1 独立验收证据与 `PASS` 结论。

## 已知限制

- S1 只有空世界 tick，不包含 World 资源、Agent、动作、代谢或死亡；这些属于 S2。
- 不包含 Genome/VM、繁殖、变异、谱系、正式实验持久化、批量实验、UI 或网络服务。
- 可复现承诺限定于相同代码、依赖、运行环境、配置和 seed，不承诺跨任意依赖版本产生相同结果。
- 当前没有 `ARCHITECTURE.md` 或 `TECH-DEBT-TRACKER.md`。

## License

仓库当前没有 `LICENSE` 文件。
