# RedNote AI Logo

`rednote-ai-logo` 是面向小红书内部产品的 AI 驱动 Logo 全流程 Skill。它不是一组通用提示词，而是一套从产品理解、方向探索、局部校准到评审、手机主屏、Figma 和生产交付的可追溯工作方法。

它由现有 `logo-design-review` Skill 与 Spark 长周期项目继续演化而来。仓库保留已经验证有效的脚本和交付结构，同时把连续反馈中形成的失败模式、校准方法和验收边界固化为可复用规则。

## 解决什么问题

- 让 Logo 方向来自产品事实与小红书设计取向，而不是默认的“AI 科技感”。
- 在连续修改中保住已经确认的轮廓、正负形、比例、连接关系和场景适配。
- 区分基础图形、材质/背景层和使用场景，避免用质感掩盖设计问题。
- 用相同尺寸、背景和手机主屏比较全部方案组合。
- 让生成、人工确认、机械校验、视觉验收和 Figma 写入都有清楚证据。

## 核心原则

1. **从当前阶段继续**：先找现有版本与人工确认，不重新开始。
2. **基础图形优先**：语义、轮廓和正负形先成立，再讨论颜色与材质。
3. **一次一个变量**：局部反馈转成明确的修改范围和禁改项。
4. **真实场景评审**：大图、小尺寸、单色、完整手机主屏与目标背景一起看。
5. **版本可追溯**：原稿不覆盖；提示词、工具、输入、输出和哈希可回看。
6. **证据不越界**：脚本 PASS 不等于视觉通过，Figma 节点不等于生产矢量。

## 安装

将仓库作为 Codex Skill 安装，或把仓库目录放入 Codex 的 Skills 目录。Skill 名称为：

```text
rednote-ai-logo
```

调用示例：

```text
使用 $rednote-ai-logo，读取当前 Logo 项目的既有方案、参考、反馈与 Figma 目标，继承已经确认的内容，只推进本轮要求。
```

## 仓库结构

```text
rednote-ai-logo/
├── SKILL.md                         Skill 入口与执行边界
├── agents/openai.yaml               Codex 展示信息
├── references/
│   ├── xiaohongshu-taste.md         小红书设计取向
│   ├── workflow.md                  全流程与阶段门禁
│   ├── design-rules.md              构形、颜色、材质与反馈规则
│   ├── generation-and-editing.md    受控生成与精确局部修改
│   ├── exploration-calibration.md   Spark 探索与校准经验
│   ├── review-contract.md           HTML 评审数据约定
│   ├── review-scenes.md             小尺寸、背景与手机主屏
│   ├── figma-handoff.md             Figma 写入与回读验收
│   ├── delivery.md                  生产交付边界
│   └── spark-lessons.md             长周期案例与规则来源
├── scripts/
│   ├── new_logo_project.py          新建项目结构
│   ├── validate_logo_project.py     校验证据与交付门禁
│   └── build_review.py              生成离线评审页和 Figma 插件包
├── assets/
│   ├── project-template/            项目记录模板
│   ├── review.html                  评审页模板
│   └── figma-plugin/                离线 Figma 开发插件
└── tests/                            脚本行为测试
```

## 推荐流程

### 1. 建立项目记录

```bash
python3 scripts/new_logo_project.py spark --name "Spark" --output-root /path/to/work
```

### 2. 从产品事实开始

填写 brief、方向、生成记录与 Evidence Ledger。已有项目先录入当前已确认版本和最近修改范围，不强制补演已经完成的早期阶段。

### 3. 生成和校准

生成模型适合视觉探索；精确几何、遮挡、位置、颜色替换和局部材质优先采用确定性编辑。每次修改保存新版本，不覆盖母版。

### 4. 统一评审

每个当前方案都检查：

- 独立大图；
- 24 / 32 / 48 / 64 px；
- 彩色、单色与反白；
- 要求的全部背景层；
- 清晰的完整手机主屏；
- 必要的概念、差异与风险说明。

### 5. Figma 与交付

写入用户指定的 Figma 文件和节点，并回读确认。正式交付必须另外验证矢量母版、单色/反白、小尺寸修订、安全区、色值、字体/字形授权和相似性/法律检查状态。

## 验证

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 /path/to/skill-creator/scripts/quick_validate.py .
```

这些命令验证 Skill 结构、数据约束和脚本行为，不替代设计师对调性、识别度和最终方案的确认。

## 当前成熟度

本 Skill 已通过 Spark 单一产品的长周期、多轮校准验证，覆盖方向发散、正负形、局部修改、轻材质、背景组合、小尺寸、手机主屏、HTML 与 Figma 交接。跨产品迁移仍应继续记录失败证据，并把新经验写成窄规则，避免把某一产品的造型偏好扩大成所有小红书产品的固定答案。
