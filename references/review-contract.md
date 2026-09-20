# Review 数据与执行

`review.json` 相对自身目录解析路径，禁止越界/远程资源。PNG 仅做头信息及哈希机械检查，不宣称完成像素质量检测。模板只支持 PNG 图片；SVG 或其他格式需先正常渲染为 PNG 供评审，保留原始资产。

```json
{
  "schemaVersion": 1,
  "project": "产品名",
  "revision": "review-v1",
  "scene": {
    "label": "设计师提供的手机主屏",
    "background": "assets/wallpaper.png",
    "overlay": "assets/apps.png",
    "backgroundRect": [-9.66, -9.73, 119.31, 119.46],
    "overlayRect": [7.2, 8.87, 85.6, 87.93],
    "slot": [7.2, 70.8128, 17.0667],
    "width": 375,
    "height": 812
  },
  "concepts": [{
    "id": "direction-a", "title": "方向 A", "version": "v2",
    "concept": "产品关系、表达机制与取舍。", "changes": "本轮改动范围。",
    "status": "exploration", "previous": "assets/v1.png",
    "placement": {"mode": "contain", "scale": 0.8, "x": 0.1, "y": 0.1, "background": "#ffffff"},
    "palettes": [{"id": "original", "label": "原版", "asset": "assets/v2.png", "kind": "original", "filter": "none"}]
  }]
}
```

`scene` 可省略，页面明确显示示意场景。真实截图应移除目标图标但保留其他 App；不把任意桌面标为用户真实截图。`overlay` 可省略。百分比 rect 是 x/y/w/h；slot 是 x/y/宽度，图标高度随宽度保持方形。主屏母版必须保持原始清晰度，只在 slot 内替换目标图标；禁止用先缩小再放大的整屏截图。

placement 的 x/y/scale 是相对于方形占位的比例；可为已确认组合画布裁切设置大于 1 的 scale 和负偏移，必须视觉核对。默认 contain 为 .8，full-bleed 为 1，不自动推测光学尺寸。所有配色必须采用同一构形；需要单独裁切时拆为版本。

用户要求多主体、多背景时，每个 `concept` 的 `palettes` 应枚举全部背景组合。每个 palette 由页面生成自己的小尺寸与手机场景，不允许只为一个代表性背景制作主屏。背景层必须在组合资产中铺满最终图标容器，主体尺寸由该方向独立配置。

状态：exploration / retained / parked；parked 不出现在当前页面。保留不代表生产验收。palette kind：original / color-artwork / filter-preview / grayscale-preview / monochrome-artwork。生产单色需 `humanReviewed: true`（Agent 只能依据实际确认填写）。filter 只支持 none、hue-rotate、grayscale、brightness、contrast；确认包直接输出渲染像素。

构建器拒绝重复 ID、缺失资产、无效 PNG、非法 filter、越界路径和无审核的生产单色标签。输出新目录，含可离线 HTML 及 Figma 开发插件；不覆写原始素材。对比模板保留旧稿，原尺寸检查、手机效果和配色都来自同一个数据快照。生成 HTML 前确认每张输入图的实际内容、构形与适配；机械程序不替代这些判断。

最终评审页面只呈现方案、必要理念、差异、风险和决策。过程性话术、Agent 自我解释、已经回答完的问题和“这轮不继续”等项目管理句子留在工作记录，不进入面对评审者的页面。
