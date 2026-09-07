# V0.1/S1 Builder Work Report 001

## 1. 结论

- Version: `V0.1 Deterministic World`
- Stage: `S1 Reproducible Experiment Baseline`
- Role: Builder
- Date: `2026-08-25`
- Report status: `Final`
- Workflow state: `Ready for Review`
- Builder conclusion: 获批的 `REQ-01..06` 与 Builder 负责的 `AC-01..07` 实现和验证证据已完成；无已知未满足项、范围偏差或待批准技术债。
- Acceptance boundary: 本报告只声明 Builder 实现和自测完成，不声明 Reviewer 已接受或 S1 已 `Completed`。

## 2. 权威输入与角色规则

本次读取并遵循：

- `docs/leader/designs/V0.1/S1-design.md`，`Approved`，实施前及报告前 SHA-256 均为 `A7BC6252AC3A6C6BB09BEF339A8D8D6E5D09DDC7CAF1AFF593BFC943720B59E7`；
- `docs/reviewer/reviews/V0.1/S1-review.md`，`Approved`，实施前及报告前 SHA-256 均为 `6F9D481334796AE6B6E964BB78F3797265CE7E5915FB5896E440122BC480E412`；
- `docs/leader/reports/V0.1/S1-report-003.md`，批准记录和 Builder 交接；
- `ROADMAP.md`，版本与阶段边界；
- 全局 `C:\Users\Powerup\.codex\agents\builder.toml`；
- 更新后的 `orchestrate-olympus-stage` skill。

Applicable reworks: 无。先前 S1 Builder/Reviewer reports: 无。

仓库没有 `AGENTS.md`、项目专属 `docs/builder/GUIDE.md` 或其他项目专属 Builder Guide。因此按 `builder.toml` 要求，使用全局 `plan-project-docs/references/role-guides/builder-guide-template.md` 作为 Builder fallback。本报告明确披露该 fallback；没有据此创建项目指南或扩大权限。

## 3. 目标、预期与实际结果

目标是在不引入 S2 能力的前提下建立可安装的 Python `src/` 项目，严格加载一个显式 YAML 配置，以运行级独立 RNG 和有限空世界 tick 产生精确规范化摘要，并建立可审计测试基线。

实际结果：

- `python -m pip install -e ".[dev]"` 在新建隔离环境中成功；
- `python -m minigenesis --help` 和设计规定的示例命令成功；
- 最终全量测试 `60 passed`；
- 两次示例 stdout 逐字节一致，文件 SHA-256 均为 `4DE55827EBBD9719A6BC42D8F426CF72307A0172603C3BA0090C2BBE166F6B34`；
- 示例摘要 digest 独立重算结果与输出均为 `sha256:93deab1c067673d192661637a2938bd919c768a8392d69d3513cf32fa10f12cb`；
- `100_000` tick 运行成功，`100_001` 在执行前失败；
- 重复键、恶意 Python YAML 标签及其他非法配置以非零码失败，stdout 为空；
- A-B-A、RNG 独立实例、模块级随机状态不变、空 tick 不消费 RNG 均有自动测试证据；
- 源码/依赖扫描未发现后续阶段能力、网络、子进程、动态执行、写文件、墙上时钟或未登记随机源。

## 4. 实现说明

### REQ-01：项目与 CLI

`pyproject.toml` 声明 Python `>=3.11`、`src/` 包发现、运行依赖 PyYAML 与 `dev` pytest 依赖。`__main__.py` 提供 `python -m minigenesis`；CLI 提供必填 `--config PATH`、默认 `text` 的 `--output-format text|json` 和真实 help。普通配置错误返回 `2`，未知运行错误返回 `1`，默认不输出 traceback。

### REQ-02：严格配置

`ExperimentConfig` 是 frozen/slots dataclass。基于 `yaml.SafeLoader` 的受限子类只增加重复键拒绝，不允许 Python 对象构造。根和 `experiment` 映射均采用精确字段集合；name 被 trim，seed/max_ticks 显式排除 bool，并执行非负与 `1..100_000` 边界。

### REQ-03、REQ-06：RNG 与隔离

每个 `Simulation` 构造自己的 `RNGContext(random.Random(seed))`，实现标识固定为 `python.random.Random/MT19937`。源码中只有 `rng.py` 创建随机源；没有模块级可变运行状态或摘要缓存。每次 execute 都创建新的 Simulation/RNG/tick。

### REQ-04：tick

tick 从 `0` 开始，`step()` 每次精确加一并拒绝越过完成边界，`run()` 在等于配置上限时结束。空步骤不调用 RNG、不读取时间、不保存逐 tick 历史。

### REQ-05：摘要

摘要严格按七个 digest 输入字段与最后的 `digest` 构造。JSON 使用 UTF-8、`ensure_ascii=False`、separators `(',', ':')` 和插入顺序；digest 输入无换行，完整 stdout 只追加一个 `LF`。不包含路径、时钟或进程信息。

## 5. 修改文件

| File | Purpose |
|---|---|
| `.gitignore` | 排除 Python 缓存、editable 元数据、隔离环境和可再生 build 证据。 |
| `pyproject.toml` | Python/依赖/包发现/pytest 项目元数据。 |
| `src/minigenesis/__init__.py` | 暴露 S1 最小公共对象。 |
| `src/minigenesis/__main__.py` | 模块命令入口。 |
| `src/minigenesis/cli.py` | 参数、用户错误、输出格式和一次运行编排。 |
| `src/minigenesis/config.py` | 安全 YAML、重复键、严格 schema、规范化不可变配置。 |
| `src/minigenesis/rng.py` | 运行级独立 MT19937 上下文与固定标识。 |
| `src/minigenesis/simulation.py` | 空世界 tick 状态、单步和有限运行。 |
| `src/minigenesis/summary.py` | 八字段摘要、规范化 JSON 与 SHA-256。 |
| `examples/v0.1/s1-baseline.yaml` | 设计规定的最小可运行配置。 |
| `tests/test_config.py` | 合法/非法/重复键/bool/范围/安全/路径校验。 |
| `tests/test_determinism.py` | RNG 序列、隔离、A-B-A、全局 random 不变。 |
| `tests/test_simulation.py` | tick 初值/单步/终止/十万边界/空 tick 不消费 RNG。 |
| `tests/test_summary.py` | 精确字段顺序、UTF-8、canonical bytes、digest 和单换行。 |
| `tests/test_cli.py` | help、text/JSON、正常/错误退出、执行前失败及宿主能力隔离。 |
| `README.md` | 更新实际环境、安装、运行、测试、配置、结构和未接受状态；未声称 Reviewer PASS。 |
| `docs/builder/reports/V0.1/S1-report-001.md` | 本实现、验证与交接记录。 |

未修改 `docs/leader/**`、`docs/reviewer/**`、`ROADMAP.md` 或 S2 文档。报告前重算的两份 Approved 权威哈希与交接值完全一致。没有创建 breakdown；阶段可在一次 Builder 工作会话内可靠完成。

## 6. 环境与依赖

- OS: Windows 11 `10.0.26200`, AMD64
- Python: `3.13.9`
- pip: `25.2`
- minigenesis: `0.1.0.dev0`, editable project location 为仓库根目录
- Direct runtime dependency: PyYAML `6.0.3`
- Direct dev dependency: pytest `9.1.1`
- Validation environment: `build/test-envs/V0.1-S1-clean`

环境和解析后的直接依赖证据见 `build/test-logs/V0.1/S1/06-environment.log`。

## 7. 实际命令与结果

| Command | Exit | Observed result | Evidence |
|---|---:|---|---|
| `python -m venv build/test-envs/V0.1-S1-clean` | 0 | 新建 Python 3.13.9 隔离环境。 | 环境由后续 `02`、`06` 的 interpreter/site-packages 路径证明；创建命令的工具输出已观察。 |
| `python -m pip install -e ".[dev]"`（沙箱内首次） | 1 | pip 被系统临时目录权限拒绝，未安装包。 | `01-install.log` |
| 同一安装命令（获准使用系统临时目录） | 0 | editable 构建并安装声明依赖成功。 | `02-install-escalated.log` |
| `python -m pytest`（初轮） | 1 | `26 passed, 1 failed, 33 errors`；33 errors 为 pytest 临时目录权限，1 fail 为测试错误地禁止名称内容中的合法空格。 | `03-pytest-initial.log` |
| `python -m pytest`（获准环境、首次修正） | 1 | `59 passed, 1 failed`；剩余失败为测试 regex 未转义括号，不是产品行为失败。 | `04-pytest.log` |
| `python -m pytest`（测试修正后） | 0 | `60 passed`。 | `05-pytest-final.log` |
| `python -m minigenesis --help` | 0 | help 列出必填 config 与 text/json。 | `07-cli-help.log` |
| 示例 JSON 命令两次 | 0 / 0 | stderr 均 0 bytes，stdout 原始文件各 283 bytes。 | `08-example-run1.json`, `08-example-run2.json`, `14-determinism-and-boundary.log` |
| `fc.exe /b` 比较两次原始输出 | 0 | 无差异；两个文件 SHA-256 相同。 | `14-determinism-and-boundary.log` |
| 独立 Python stdlib JSON/SHA-256 重算 | 0 | 字段顺序正确、digest 相同、完整 canonical bytes 相同、末尾单 LF。 | `09-independent-digest.log` |
| 配置/RNG/隔离/安全关键测试 `-vv` | 0 | `30 passed`，列出每个关键测试名。 | `10-critical-validation.log` |
| 三类实际非法 CLI（duplicate/100001/malicious tag） | 2 / 2 / 2 | stdout 均 0 bytes；错误可定位；fixture 哈希不变；无执行 marker。 | `11-invalid-cli-safety.log` 及同前缀 stdout/stderr |
| RNG/time/host/scope/dependency `rg` 检查 | 0/1（按预期） | 唯一 RNG 创建位于 `rng.py`；其余禁用模式和越界能力无匹配。 | `12-source-scope-scan.log` |
| `python -m pytest -k "determinism or summary or tick"` | 0 | `37 passed, 23 deselected`。 | `13-review-plan-targeted.log` |
| `100_000` tick CLI | 0 | `completed_ticks=100000`，stderr 0 bytes。 | `14-max-boundary.json`, `14-determinism-and-boundary.log` |
| `compileall` + 完整 pytest + 示例 CLI 最终复核 | 0 | compile 0；`60 passed`；CLI 0；overall 0。 | `15-final-verification.log` |
| 原始证据 SHA-256/字节数清单 | 0 | 枚举 `01..15`、原始 stdout/stderr 与安全 fixtures。 | `16-evidence-manifest.log` |
| Builder 完成条件一致性审计 | 0 | 权威哈希、文件、报告字段、关键证据、README 状态和 Git 忽略规则一致。 | `17-completion-audit.log` |

`08-cli-determinism.log` 保留了一次独立验证 one-liner 的 Builder 命令错误（`NameError`）；此前的两次 CLI 和 byte compare 已成功。未覆盖该历史记录，而是在 `09-independent-digest.log` 以修正后的独立命令成功重算。所有最终结论仅引用成功的 `09`/`14`/`15` 证据。

快速预检还曾在 editable 安装前用工作站全局解释器运行 pytest，因 `src/` 包尚未安装而出现五个 `ModuleNotFoundError`；这验证了实现没有依赖隐式 `PYTHONPATH`。正式测试全部在上述隔离 editable 环境执行。

## 8. REQ / AC / RV 证据追踪

| Requirement / Acceptance | Implementation and test evidence | Raw evidence |
|---|---|---|
| `REQ-01`, `AC-01`, `RV-01` | pyproject、模块入口、help、示例成功 JSON | `02`, `07`, `08`, `15` |
| `REQ-02`, `AC-03`, `RV-02` | 严格 schema、重复键、bool/int、缺失/未知/范围/YAML 错误；执行前拒绝 | `05`, `10`, `11` |
| `REQ-03`, `REQ-05`, `AC-02`, `RV-03` | 独立 RNG、已知序列、同输入 raw bytes、精确摘要与独立 digest | `08`, `09`, `10`, `13`, `14` |
| `REQ-03`, `REQ-06`, `AC-04`, `RV-04` | 无全局运行状态；A-B-A 与随机状态隔离测试 | `10`, `12`, `15` |
| `REQ-02`, `REQ-04`, `AC-05`, `RV-05` | SafeLoader、恶意标签/重复键、上限、无宿主能力或写文件 | `10`, `11`, `12`, `14` |
| `REQ-01..06`, `AC-06`, `RV-06` | 干净环境 editable 安装、环境版本、完整 60 tests、README 实际命令 | `02`, `05`, `06`, `15` |
| Scope, `AC-07`, `RV-07` | 仅配置/RNG/tick/摘要/CLI；依赖及关键字扫描无 S2+ 能力 | `12` |

## 9. 未完成项、风险、偏差与技术债

### 未完成项

- Builder 范围内：无。
- 工作流剩余：Reviewer 必须独立读取实现和本证据、重跑关键验证并给出结论；在此之前 S1 不是 `Completed`。

### 风险

- 声明支持 Python `>=3.11`，本轮实际隔离验证版本为 Python 3.13.9；Python 3.11/3.12/3.14 未在 Builder 本机矩阵执行。实现只使用 Python 3.11 可用语法/API，README 只把 3.13.9 标成已验证环境。
- 设计本身把可复现承诺限定在相同代码、依赖和环境；依赖版本变化不在跨版本序列稳定承诺内。

### 偏差

- 产品范围、接口、字段顺序、边界与依赖类别均无偏差。
- 预期文件清单外仅增加 `.gitignore`，用于隔离可再生缓存、环境与 raw evidence；属于必要仓库卫生，不增加产品能力。
- Builder 选择 PyYAML `6.x` 和 pytest `8..9`，属于设计明确授权的具体依赖选择。

### 技术债

无请求延期或需批准的技术债。

## 10. Reviewer 重点

Reviewer 应特别独立确认：

1. 使用新隔离环境重跑精确 editable 安装，不复用 Builder venv。
2. 直接检查 `_UniqueKeySafeLoader` 仍以 SafeLoader 为基类，重复键和恶意标签均在 tick 前拒绝。
3. 检查源码唯一随机源创建位置和空 tick RNG state 不变。
4. 重新生成两份原始 JSON 并自行重算 digest，不只信任 Builder 日志。
5. 检查 `sys.stdout.buffer` 输出的单 LF 与字段插入顺序。
6. 核对 README 的 `Ready for Review` 含义，没有把 S1/V0.1 误标完成。
7. 搜索 S2+ 能力与网络/子进程/持久化，确认阶段边界。

## 11. 交接

Builder 建议状态：`Ready for Review`。当前没有阻止 Reviewer 开始的环境、实现或证据 blocker。原始证据根目录为 `build/test-logs/V0.1/S1/`；该目录按设计是可再生构建证据并被 Git 忽略，但当前工作区中完整存在。
