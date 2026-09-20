---
workflow_version: "1.0"
project_slug: "{{PROJECT_SLUG}}"
project_name: "{{PROJECT_NAME}}"
review_status: draft
retained_candidate_ids: ""
retained_asset_paths: ""
primary_candidate_id: ""
human_approved_by: ""
human_approved_at: ""
created_at: "{{CREATED_AT}}"
---

# {{PROJECT_NAME}} · 候选评审

`review_status` 取值：`draft` / `approved`。

## 淘汰门禁

对最终入围方案逐项确认：

- [ ] 与 PRD 核心价值不冲突
- [ ] 没有明显复制参考或已知品牌
- [ ] 24–32 px 仍有基本识别
- [ ] 单色与反白仍成立
- [ ] 没有明显文化、冒犯或误读风险
- [ ] 结构可被干净地矢量重建
- [ ] 含字标时关键尺寸仍可读，或本项不适用

## 统一评分

每项按 1–5 分填写。总分用于比较，不替代判断。

| Candidate | 产品关联 25 | 区分度 20 | 记忆性 15 | 简洁缩放 15 | 系统一致 10 | 完成度 10 | 延展 5 | 加权总分 | 主要风险 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| [ID] |  |  |  |  |  |  |  |  |  |

## 场景检查

| Candidate | 32 px | 导航栏 | App 图标/头像 | 深色背景 | 单色打印 | 备注 |
|---|---|---|---|---|---|---|
| [ID] | 通过/失败 | 通过/失败 | 通过/失败/不适用 | 通过/失败 | 通过/失败 |  |

## 保留结论

- 当前保留候选：[允许多个]
- 主候选（如已确定）：[待填写/未确定]
- 保留理由：[待填写]
- 主动放弃了什么：[待填写]
- 精修时必须保持不变的部分：[待填写]
- 允许局部调整的部分：[待填写]
- 上线前仍需完成的相似性/法律检查：[待填写]

确认后，把保留候选复制到 `selected/` 并另存，不覆盖 `candidates/` 中的原始输出。front matter 中多个 ID 与路径用英文逗号分隔，顺序一一对应。尚未确定唯一方案时允许 `primary_candidate_id` 为空；正式生产交付前应明确主版本。
