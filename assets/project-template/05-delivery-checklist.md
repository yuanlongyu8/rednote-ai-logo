---
workflow_version: "1.0"
project_slug: "{{PROJECT_SLUG}}"
project_name: "{{PROJECT_NAME}}"
delivery_status: draft
validated_at: ""
validated_by: ""
created_at: "{{CREATED_AT}}"
---

# {{PROJECT_NAME}} · 交付检查

`delivery_status` 取值：`draft` / `validated`。自动脚本通过后仍需完成这里的视觉和业务检查。

## 必需项

- [ ] `delivery/logo-master.svg` 可正常解析，且不是把位图包进 SVG
- [ ] `delivery/logo-1024.png` 为 1024 × 1024
- [ ] `delivery/logo-32.png` 为 32 × 32，并人工确认可识别
- [ ] 彩色、单色、反白三种条件均已检查
- [ ] 主使用场景中已完成视觉检查
- [ ] 最小尺寸与安全区已记录
- [ ] 色值与字体/字形授权信息已记录
- [ ] 最终文件与所选方案的差异已记录
- [ ] 相似性检索和法律审查状态没有被省略或误写为自动通过

## 按需项

- [ ] 横版与竖版组合标
- [ ] 中英文字标组合
- [ ] App icon / favicon 专用微调版
- [ ] 印刷色与专色版本
- [ ] 动效起始/结束帧
- [ ] 品牌使用禁例

## 使用规范摘要

- 主版本：[待填写]
- 最小尺寸：[待填写]
- 安全区：[待填写]
- 主色与辅助色：[待填写]
- 字体/字形授权：[待填写]
- 不允许的用法：[待填写]

## 风险与外部确认

- 相似性检索状态：未开始/初筛完成/专业检索完成
- 法律审查状态：不适用/待进行/已由 [主体] 完成
- 最终业务确认：[待填写]

完成后填写 front matter 中的 `validated_by`、`validated_at`，并将 `delivery_status` 改为 `validated`。
