---
name: parse-single-receipe
description: 解析 HowToCook 项目中的单个 Markdown 菜谱文件，提取菜谱信息并生成符合 scripts/receipe_schema.json 格式的 JSON 数据。
---

# parse-single-receipe 技能

## 目标
解析 HowToCook 项目中的单个 Markdown 菜谱文件，提取菜谱信息并生成符合 scripts/receipe_schema.json 格式的 JSON 数据，写入到给定文件中。

## 输入
- 一个文件路径，用于保存生成的 JSON 数据
- 一个 HowToCook 项目的 Markdown 菜谱文件内容

## 输出
- 在给定文件路径保存符合菜谱 Schema 的 JSON 数据，严格遵循 scripts/receipe_schema.json 这个 Schema。包含以下字段：
  - name: 菜谱名称
  - source_file: 原始文件路径（相对于 HowToCoook 仓库下的 dishes/ 目录）
  - category: 菜谱分类（素菜、荤菜、水产、早餐、主食、汤与粥、调料、甜品、饮料、半成品等）
  - difficulty: 烹饪难度等级（simple/easy/medium/hard/expert）
  - total_time_minutes: 总耗时（分钟），如果没有提供则设为 null
  - servings: 分量（固定为1，表示已转换为一人份）
  - original_servings: 原始分量（菜谱中标注的分量），如果没有提供则设为 null
  - images: 菜谱相关图片链接数组
  - ingredients: 食材列表（每人份）
  - steps: 制作步骤列表
  - tips: 小贴士列表

例：

```json
{
  "name": "菜谱名称",
  "source_file": "原始文件路径",
  "category": "分类",
  "difficulty": "easy/medium/hard/simple/expert",
  "total_time_minutes": 15,
  "servings": 1,
  "original_servings": 2,
  "images": ["图片路径"],
  "ingredients": [
    {
      "ingredient_name": "食材名称",
      "quantity": 200,
      "unit": "g",
      "quantity_range": { "min": 150, "max": 200 },
      "is_optional": false,
      "note": "备注",
      "original_quantity": "适量",
      "is_estimated": true
    }
  ],
  "steps": [
    {
      "step": 1,
      "content": "步骤内容",
      "duration_minutes": 3,
      "tips": "提示"
    }
  ],
  "tips": ["整体提示"]
}
```

输出前，可以先生成空白的 JSON 文件，然后根据格式填写:

```json
{
  "name": null,
  "source_file": null,
  "category": null,
  "difficulty": null,
  "total_time_minutes": null,
  "servings": null,
  "original_servings": null,
  "images": [],
  "ingredients": [
    {
      "ingredient_name": null,
      "quantity": null,
      "unit": null,
      "quantity_range": { "min": null, "max": null },
      "is_optional": null,
      "note": null,
      "original_quantity": null,
      "is_estimated": null
    }
  ],
  "steps": [
    {
      "step": null,
      "content": null,
      "duration_minutes": null,
      "tips": null
    }
  ],
  "tips": []
}
```

给定文件一般在 out 目录下（不一定直属）。

## 食材列表字段要求
- ingredient_name: 食材名称
- quantity: 食材数量（已转换为一人份），如果是模糊数量（如适量、少许）则使用日常平均值或推荐值
- unit: 计量单位，如果没有提供则设为 null
- quantity_range: 数量区间（如果有区间值），否则设为 null
- is_optional: 是否为可选食材
- note: 补充说明，如果没有提供则设为 null
- original_quantity: 原始数量描述（用于模糊数量），如果是精确数值则设为 null
- is_estimated: 是否为估算值（用于模糊数量）

## 制作步骤字段要求
- step: 步骤序号
- content: 步骤具体内容
- duration_minutes: 此步骤预计耗时（分钟），如果没有提供则设为 null
- tips: 该步骤的小贴士或提示，如果没有提供则设为 null

## 重要约束
- 每道菜谱至少有一个原料和一个步骤
- 食材只有可食用部分，不得包含厨具、餐具、厨房用品
- 调料（盐、酱油、醋等）也属于食材
- 如果同时记录了食材的重量/体积和个数，记录 quantity 和 unit 时，记录重量/体积
- 如果遇到适量、少许等字眼，使用日常使用该食材的平均值，或者是推荐值（如：食盐一人一顿饭约 2 g)
- 如果遇到区间值，在 quantity_range 中记录区间，在 quantity 记录最大值
- 如果某个字段在菜谱中没有提及，请设置为 null 而不是省略
- 所有上述 JSON 结构中的字段都应该出现在最终输出中
- 菜谱解析必须输出 JSON 格式的内容，且 JSON 严格遵循 scripts/receipe_schema.json 这个 Schema
- 如果菜谱附有图片，也需提取图片链接
- 如果菜谱没有提到分量，默认为一人份