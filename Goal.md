# AI Piano Arranger —— 重构方案（2026-07-30）

> 这是当前生效的主方案。  
> 顶层愿景仍以 `docs/project-vision.md` 为准；2026-07-30 之前的旧技术方案已归档到 `docs/archive/2026-07-30-reset/`。

## 1. 为什么现在必须重构

这次重构不是“局部换模型”，而是项目技术路线要重新定轴。

旧方案的问题已经比较清楚：

1. `SheetSage + Jukebox` 这条理解链路已经不再适合作为主线。
   `Jukebox` 太重、过时，而且把后续设计绑死在历史接口上。
2. 把样本定义成 `(原曲音频, 改编 MIDI)` 太窄。
   这没有把个人用户最容易收集到的三类资源真正利用起来：
   - JPOP 原曲音频
   - 改编钢琴谱
   - 由钢琴谱渲染出来的纯净钢琴音频
3. 把 MIDI 当作唯一“真值”会压扁信息。
   钢琴谱里真正有价值的记谱结构、分声部、指法痕迹、版面层级、演奏语义，一旦先粗暴塌缩成 MIDI，就很难完整回来。

所以这次重构的目标不是“把 Jukebox 替换成 MERT 就结束”，而是把整个项目从“旧输入接口兼容工程”改成“面向三视角资源的音乐改编系统”。

## 2. 新版项目目标

项目的大愿景不变：从原曲出发，生成可控、可个性化、接近真实编曲者风格的钢琴改编结果。

但在技术路径上，短中期目标改成三层：

1. 先重建数据底座。
   用一个新的样本单位统一原曲、乐谱、渲染钢琴音频，而不是继续围绕单一 MIDI 管线堆补丁。
2. 再重建音乐理解前端。
   不预设只选 `MERT`，而是把 `MERT`、`MuQ`、`MusicFM` 作为首批主候选做 benchmark。
3. 最后再接生成器与个性化层。
   生成器短期仍可借助 `PiCoGen2` 验证路线，但不再让旧接口决定整个系统的边界。

## 3. 新的核心判断

### 3.1 乐谱不是为了被尽快变成 MIDI

乐谱首先是高价值的结构化监督源。  
MusicXML / 原始 PDF / 页图像 / 渲染钢琴音频，这些都应保留为一等资产。MIDI 只是在需要事件序列训练、对齐或兼容旧模型时派生出来的辅助视图。

### 3.2 OMR / AMT 可以用，但不能当真值中心

`homr`、AMT、MIDI 转写、音频对齐都可以进入工具箱，但它们的角色是：

- 补齐缺失视图
- 生成候选对齐
- 提供检验信号

而不是把整个数据流都建立在“先识别成 MIDI，再假装没有损失”这件事上。

### 3.3 这次重构的优先级应是“表示与数据”，不是先改 decoder

研究结果表明，现阶段真正稀缺的不是又一个 decoder 变体，而是：

- 对个人可收集资源友好的数据规范
- 对原曲与改编之间跨视角关系的对齐层
- 可以替换和比较的音乐理解前端

因此短期应先把“输入表示”做好，再决定要不要大动生成器。

## 4. 新的样本单位：`ArrangementBundle`

以后项目中的标准样本不再是 `(audio, midi)`，而是一个多视角样本包：

```text
dataset/
  {bundle_id}/
    source/
      song_audio.mp3
      metadata.yaml
    arrangement/
      score/
        master.musicxml        # 如果有原生可编辑谱面，这是最高优先级
        source.pdf             # 原始谱面 PDF
        pages/                 # 从 PDF 切出来的页面图像
      render/
        piano_clean.wav        # 由谱面渲染得到的纯净钢琴音频
      symbolic/
        optional.mid           # 可选派生视图，不再是唯一真值
      align/
        audio_to_render.json
        score_to_render.json
        source_to_sections.json
    qc/
      quality_report.yaml
```

### 资源优先级

1. `score-native`：MusicXML、可编辑谱面、原始 PDF
2. `render-audio`：由谱面渲染出的纯净钢琴音频
3. `symbolic-derived`：从谱面或音频派生的 MIDI / note events

这个优先级意味着：如果乐谱和 MIDI 冲突，以乐谱为准；如果渲染钢琴音频和 AMT 结果冲突，以更高质量的可验证来源为准。

## 5. 新版系统架构

新版系统围绕“五层”而不是旧的单通道：

### 5.1 原曲理解层

目标：从 `JPOP 原曲` 抽取稳定的语义、结构、节奏与风格表示。

候选编码器首批限定为：

- `MERT`
- `MuQ`
- `MusicFM`

这里不预设赢家。第一阶段只做 benchmark，比较：

- 段落/结构感知能力
- 节奏与拍点稳健性
- 对风格迁移和检索的可分性
- 与后续改编目标的相关性
- 本地部署成本

### 5.2 改编表示层

目标：让改编侧不再只有一个 MIDI 视图。

至少保留三类表示：

- 记谱表示：MusicXML / score tokens / page-level layout anchors
- 渲染表示：纯净钢琴音频 embedding
- 事件表示：MIDI / note events / tokenizer events

这样做的意义是：你可以分别学习“谱面长什么样”“听起来像什么”“事件层怎么编码”，而不是把三件事挤成同一种表示。

### 5.3 跨视角对齐层

这是新方案的中轴。

它负责建立：

- 原曲音频 ↔ 改编渲染钢琴音频
- 改编渲染钢琴音频 ↔ 改编乐谱
- 原曲片段 ↔ 改编段落 / 动机 / 和声区域

这层可以吸收研究与开源参考中的方法：

- 音频到乐谱对齐
- 音频到钢琴渲染对齐
- 共享 embedding 空间检索

没有这层，后面无论用 `PiCoGen2` 还是别的生成器，都会继续被劣质监督拖住。

### 5.4 条件构建层

将多视角信息整理成可供生成器消费的条件：

- 原曲内容条件
- 编曲风格条件
- 难度 / 密度 / 情绪 / 演奏性条件
- 用户偏好条件

这层不等于某个具体模型，而是一个稳定接口。  
以后无论接 `PiCoGen2`、diffusion、seq2seq、retrieval-augmented generator，都尽量复用这层。

### 5.5 生成与重排层

短期策略：

- 继续把 `PiCoGen2` 当成可用 baseline
- 主要目的是验证新数据表示与条件接口是否有效

中期策略：

- 如果 `PiCoGen2` 与新表示长期不兼容，再考虑替换生成器主干
- 但那应该建立在 benchmark 和误差分析之上，而不是先入为主地全栈推翻

## 6. 明确保留、退出、降级的东西

### 保留

- `docs/project-vision.md` 中的顶层产品愿景
- “个人用户也能训练出有风格差异的系统”这一方向
- `PiCoGen2` 作为短期 baseline / 兼容验证器的价值

### 退出主线

- `SheetSage + Jukebox` 作为理解前端主路径
- “蒸馏回旧 SheetSage 接口”作为系统中心思路
- “Standard MIDI 是唯一核心输出”的假设
- “paired (audio, midi) 就够了”的数据前提

### 降级为辅助工具

- OMR（如 `homr` 一类）
- AMT / audio-to-MIDI
- MIDI-only tokenizer 流程

这些工具仍然可以服务于数据补全、对齐、兼容训练，但不能再决定全局架构。

## 7. 分阶段实施计划

### Phase 0: 文档与基线重置

- 归档旧技术方案
- 确认新的主文档集合：`Goal.md`、`docs/architecture.md`、`research.md`
- 明确哪些旧 ADR 已失效

### Phase 1: 建立 `ArrangementBundle`

- 个人可执行基线建议：聚焦单一 JPOP 歌手，`20-30` 首歌，推荐目标为 `24` 首
- 设计 bundle schema
- 先手工构建一小批高质量样本
- 为每个样本保留 score / render / optional MIDI / alignment / QC
- 建立数据质量分级
- 具体执行清单见 `docs/superpowers/plans/2026-07-30-phase1-single-artist-dataset.md`
- 当前试点歌手已锁定为 `ヨルシカ`，并已从现有本地素材初始化 `song_001` 到 `song_003` 三个 reference bundles

### Phase 2: 原曲理解前端 benchmark

- 针对 `MERT`、`MuQ`、`MusicFM` 建立统一评测脚本
- 比较它们在检索、结构切分、风格判别、下游条件构建上的表现
- 选出第一阶段主编码器，必要时保留第二候选做 fallback

### Phase 3: 改编侧表示与对齐

- 实现 score parser / score tokenization
- 建立 render-audio encoder
- 建立 score-render 与 source-render 对齐产物
- 明确哪些监督信号来自乐谱，哪些来自音频

### Phase 4: 生成 baseline 接入

- 把新的条件构建层接到 `PiCoGen2` baseline
- 验证是否能在不依赖旧 `SheetSage` 接口的情况下训练 / 推理
- 记录 mismatch 和瓶颈

### Phase 5: 风格与偏好层

- 重新定义 style / preference 的学习对象
- 区分“编曲者风格”与“最终用户偏好”
- 为偏好学习设计 rerank / adapter / reward 三种候选路线

### Phase 6: 评估与产品化闭环

- 同时评估可听性、可弹性、记谱质量、风格贴近度
- 形成用户能实际使用的数据收集闭环
- 再决定是否推进更强主生成器

## 8. 当前阶段明确不做的事

为了防止这次重构再次失焦，当前阶段先不做下面几件事：

1. 不从零训练新的音乐基础模型
2. 不强制把所有乐谱先塌缩成 MIDI 才能进入系统
3. 不在没有 benchmark 的前提下预设 `MERT` 一定是唯一答案
4. 不急着做完全端到端的大一统多模态生成器
5. 不再围绕旧 `SheetSage` 接口做长期兼容设计

## 9. 三个关键决策检查点

### D1. 主音频编码器最终选谁

在 `MERT / MuQ / MusicFM` 中选第一主线，标准不是“谁名气大”，而是“谁最适合改编任务的数据现实和本地算力约束”。

### D2. 乐谱主表示怎么定

需要尽快决定：系统内部到底以 MusicXML 为主、score tokens 为主，还是双轨并存。  
这个决策会直接影响后续 parser、alignment、generator interface 的形状。

### D3. 个性化落在哪一层

偏好学习可以落在：

- 生成前条件层
- 生成后的 rerank 层
- 轻量 adapter / reward 层

这个问题不该现在拍板，但必须在 Phase 5 前收敛。

## 10. 成功标准

如果这次重构成功，至少应达到下面几个结果：

1. 样本单位从 `(audio, midi)` 升级为稳定可复用的 `ArrangementBundle`
2. 乐谱在系统中以原生资产身份长期保留，而不是一开始就被压扁
3. 原曲理解前端摆脱 `SheetSage + Jukebox` 历史包袱
4. 生成器可以消费新的多视角条件，而不是只吃旧接口蒸馏特征
5. 系统最终能支持风格、难度、密度、偏好等多维可控改编

## 11. 当前主张

基于 2026-07-30 的调研结果，当前建议很明确：

1. 立刻停止把旧 `SheetSage/Jukebox` 路线当作项目主线
2. 先建立 `ArrangementBundle`，把三类用户可得资源变成一套可靠数据规范
3. 对 `MERT`、`MuQ`、`MusicFM` 做同一套 benchmark，再选主理解前端
4. 短期继续使用 `PiCoGen2` 作为 baseline，而不是马上全盘替换生成器
5. 把“乐谱 + 渲染钢琴音频”提升为和原曲音频同等级的一等资产
