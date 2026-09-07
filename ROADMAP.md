# MiniGenesis Roadmap

## 1. 项目概览

MiniGenesis 面向数字演化实验，目标是构造一个小型、可复现、可审计的数字培养皿。系统只定义资源、时间、动作、遗传和局部交互等底层规则；宏观行为必须来自个体执行、繁殖、变异和选择的累计结果。

当前 `V0.1/S1 Reproducible Experiment Baseline` 已实现并经独立 Reviewer `PASS`；`V0.1` 仍在进行中，下一执行焦点是尚未实现或验收的 `V0.1/S2 Resource World and Lifecycle`。

## 2. 状态定义

- `Planned`：范围已写入规划，但实现尚未开始或尚未接受。
- `In Progress`：实现或验证已开始，尚未完成接受。
- `Blocked`：关键依赖、环境或缺陷阻止继续验证。
- `Deferred`：已明确推迟，不属于当前执行范围。
- `Completed`：全部阶段满足完成条件，并由 Reviewer 给出 `PASS`；或在明确批准遗留项后给出 `PASS WITH DEBT`。

创建文档、提交代码或 Builder 自测通过都不能单独构成 `Completed` 证据。

## 3. 范围边界

### 3.1 长期范围

- 确定性模拟时钟、调度和资源账本。
- 能执行小型程序的沙箱 VM。
- 无显式 fitness 的自复制、变异和自然选择。
- birth、death、action、mutation 和 parent-child 谱系追踪。
- 多 seed 批量实验以及 novelty、diversity、lineage persistence、complexity 指标。
- 由研究假设驱动的通用交互与环境扩展。

### 3.2 长期非目标

- 预设生命史、物种路线、阵营或剧情。
- 以“演化出人类”或指定高级行为作为成功标准。
- 允许数字个体执行任意 Python 或宿主代码。
- 让 Observer、报告器或 LLM 修改世界状态。
- 为了展示效果而隐藏规则、seed、失败实验或负面结果。

### 3.3 当前规划期默认排除项

下列方向只有在进入新的获批版本后才可实施：

- 二维空间和图形化世界；
- 神经网络、强化学习和 Neuroevolution；
- ASAL 自动规则搜索；
- LLM 分析器；
- GPU、云集群或分布式执行；
- CA 与 Core 的集成；
- 预设的捕食、合作、寄生或社会角色。

### 3.4 受保护记录

实验配置、seed、依赖版本、事件数据、指标、谱系和评审历史一旦成为正式证据，不得被后续运行静默覆盖。具体持久化约束在 `V0.3` 的获批阶段设计中确定。

## 4. 版本序列

### V0.1 Deterministic World

Status: `In Progress`

Prerequisites:

- 无。

User-visible objective:

用户能够从显式配置和 seed 启动一个无空间资源世界，并证明相同代码、运行环境、配置和 seed 会产生相同的逐步状态与摘要。

Core capabilities:

- Python 项目、命令行入口和自动测试基线。
- 配置校验、集中式随机数源和确定性摘要。
- World、Agent、调度、资源获取、代谢、衰老和死亡。
- 可核对的能量/资源账本。

Current-version non-goals:

- Genome VM、繁殖、变异和谱系。
- 持久化事件仓库、批量实验和研究指标。
- 个体间交互、空间和环境反馈。
- UI、LLM、神经网络或自动搜索。

Stage breakdown:

- `S1 Reproducible Experiment Baseline` — `Completed`：建立项目入口、配置、集中 RNG、模拟时钟、确定性摘要和测试基线；详细设计见 `docs/leader/designs/V0.1/S1-design.md`，接受证据见 `docs/reviewer/reports/V0.1/S1-report-001.md`（`PASS`）。
- `S2 Resource World and Lifecycle` — `Planned`：加入无空间资源池、Agent、确定性调度、资源获取、代谢、衰老、死亡和守恒账本；详细设计见 `docs/leader/designs/V0.1/S2-design.md`。

Completion criteria:

- 用户可通过文档化命令运行有限步数的资源世界。
- 相同代码、环境、配置和 seed 的两次运行产生相同的规范化结果。
- 资源账本在正常、边界和死亡路径上满足设计恒等式。
- 自动测试覆盖确定性、配置校验、调度、生命周期和账本边界。
- `S1` 与 `S2` 均获得 Reviewer `PASS`，或在用户明确批准遗留项后获得 `PASS WITH DEBT`。

Related documents:

- Designs: `docs/leader/designs/V0.1/`
- Review plans: `docs/reviewer/reviews/V0.1/`

### V0.2 Digital Replication

Status: `Planned`

Prerequisites:

- `V0.1 Completed`。

User-visible objective:

用户能够观察受限程序控制个体行为和繁殖，后代发生可追踪的替换、插入或删除变异，并形成多代谱系。

Core capabilities:

- 有单轮预算的自定义沙箱 VM。
- 可执行基因组及稳定序列化。
- 由程序动作触发的复制和繁殖。
- 替换、插入、删除三类变异。
- parent-child 谱系与 mutation 事件。

Current-version non-goals:

- 显式 fitness、任务奖励或人工物种分类。
- 个体间通信、空间和行为聚类。
- 任意宿主代码、文件、网络或系统调用。

Stage breakdown:

- `S1 Genome and Sandboxed VM`：定义最小指令集、执行预算、错误语义和宿主隔离。
- `S2 Reproduction and Mutation`：实现复制、繁殖成本以及三类可配置变异。
- `S3 Lineage Continuity`：建立稳定身份、parent-child 关系和多代谱系验证。

Completion criteria:

- 至少一个公开的基准基因组可在无变异条件下完成自复制。
- 启用变异时，所有后代差异可由记录的 mutation 事件解释。
- 个体无法越过 VM 边界访问宿主能力。
- 多 seed 实验中至少存在可持续多代的谱系；不要求每个 seed 成功。
- 所有阶段通过独立评审。

### V0.3 Evolution Lab

Status: `Planned`

Prerequisites:

- `V0.2 Completed`。

User-visible objective:

用户能够批量运行多个 seed，保存不可静默覆盖的实验记录，并从原始事件重建谱系和核心指标。

Core capabilities:

- 实验配置、运行元数据和版本指纹。
- 结构化事件、指标及谱系数据。
- 多 seed 参数矩阵与失败隔离。
- population、diversity、novelty、lineage persistence 和 complexity 的首版定义。
- 基于结构化证据的自动摘要和基础图表。

Current-version non-goals:

- 宣称已经实现开放式演化。
- 由 LLM 生成实验结论。
- 自动搜索规则空间。

Stage breakdown:

- `S1 Experiment Records`：定义不可覆盖的实验目录、元数据、事件和谱系格式。
- `S2 Batch Execution`：运行多 seed 参数矩阵并隔离单次失败。
- `S3 Metrics and Reports`：实现可从原始数据重算的指标、图表和证据化摘要。

Completion criteria:

- 至少完成一次 100 seed 的可复现实验批次。
- 任一正式指标和图表都可追溯并重算自原始事件。
- Observer 开启或关闭不改变模拟事件流。
- 失败运行不会破坏已完成实验记录。
- 所有阶段通过独立评审。

### V0.4 Generic Interaction

Status: `Planned`

Prerequisites:

- `V0.3 Completed`。

User-visible objective:

用户能够研究个体间通用信息或能量交换是否产生可重复的行为差异，而无需在 Core 中预设合作、攻击或寄生。

Core capabilities:

- 小型、带成本、无高级语义的交互原语。
- 行为序列和行为特征记录。
- 无监督行为分组与对照实验。

Current-version non-goals:

- 手工标注社会角色。
- 为指定行为提供奖励。
- 空间拓扑和视觉化世界。

Stage breakdown:

- `S1 Interaction Primitives`：加入受资源守恒约束的通用交互动作。
- `S2 Behavior Observation`：提取行为特征，建立聚类与禁用交互的对照实验。

Completion criteria:

- Core 不包含预设社会或生态角色。
- 交互成本和资源转移可由账本解释。
- 多 seed 数据能够区分稳定行为差异与随机噪声。
- 所有阶段通过独立评审。

### V0.5 Environmental Structure

Status: `Planned`

Prerequisites:

- `V0.4 Completed`。
- `V0.3` 或 `V0.4` 的实验数据证明全局资源世界存在明确研究限制。

User-visible objective:

用户能够比较无空间基线与最小环境结构，判断环境异质性是否提高共存、多样性或新颖性。

Core capabilities:

- 首选一维环形空间。
- 局部资源访问和移动成本。
- 可单独启停的资源扩散、再生或简单环境反馈。
- 与无空间世界的对照和消融实验。

Current-version non-goals:

- 默认承诺二维空间或 CA。
- 用地形或角色名称编码预期生态结果。
- 在缺少实验依据时继续堆叠环境机制。

Stage breakdown:

- `S1 One-dimensional Locality`：建立一维邻域、局部资源和移动。
- `S2 Environmental Feedback Experiments`：逐项评估扩散、再生或反馈机制，并保留可撤回性。

Completion criteria:

- 空间规则保持确定性、账本可解释和配置可复现。
- 至少一组对照实验回答预先写明的研究假设。
- 每项环境机制都可独立禁用，不破坏无空间基线。
- 所有阶段通过独立评审。

## 5. 阶段依赖

```text
V0.1/S1 实验基线
  -> V0.1/S2 资源世界
    -> V0.2/S1 沙箱 VM
      -> V0.2/S2 繁殖与变异
        -> V0.2/S3 谱系连续性
          -> V0.3 实验记录、批量执行与指标
            -> V0.4 通用交互
              -> V0.5 环境结构（还需要实验触发条件）
```

阶段不得仅因实现方便而提前引入后续范围。若当前阶段暴露出必须改变版本目标、阶段顺序或完成标准的问题，应停止扩大实现并请求用户批准路线图变更。

## 6. 长期方向与未决事项

以下内容只是研究方向，不是 Builder 需求或 Reviewer 缺陷判据：

- 开放式演化及 MODES 类度量；
- 基因组无界或分段增长；
- Neuroevolution；
- ASAL 自动规则搜索；
- 只读式 LLM Observer；
- 二维环境或 CA-like 动态场；
- 与 ALife 数据标准或其他平台互操作。

这些方向只有在获得明确研究假设、资源预算和用户批准后，才能进入新的版本与阶段设计。

## 7. 路线图变更权限

下列变更需要用户明确批准：

- 改变版本目标或重要完成标准；
- 新增、删除或重排重要版本；
- 将已批准的当前范围推迟到未来；
- 引入高成本依赖、GPU、云服务、LLM 或宿主代码执行；
- 改变长期非目标。

## 8. 变更记录

- 2026-08-24：根据初始研究报告建立 `V0.1` 至 `V0.5` 的版本序列，将确定性世界、数字遗传、实验观测、通用交互和环境结构分离，避免后续能力提前进入首个版本。
- 2026-08-25：根据 `docs/reviewer/reports/V0.1/S1-report-001.md` 的 `PASS` 同步事实状态：V0.1/S1 转为 `Completed`，V0.1 因 S2 尚未实现或验收而转为 `In Progress`；未改变范围、目标或阶段顺序。
