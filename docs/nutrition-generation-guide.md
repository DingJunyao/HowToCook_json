# 营养信息生成功能使用说明

## 概述

我们已成功实现了营养信息生成功能，可以从USDA FoodData Central获取营养数据，计算NRV/DV值，并生成标准化的营养信息JSON文件。

## 功能特点

1. **多标准支持**：优先使用中国GB 28050-2011标准计算NRV%，如无对应标准则使用美国FDA标准计算DV%
2. **全面营养素覆盖**：包含能量、宏量营养素（蛋白质、脂肪、碳水化合物）、矿物质和维生素等
3. **智能匹配**：利用`match-ingredients`技能将食材与USDA数据库中的营养数据进行匹配
4. **标准化输出**：生成格式统一的JSON文件，包含详细的营养成分及NRV/DV百分比

## 使用方法

### 1. 通过命令行运行
```bash
python generate_nutrition_data.py --output-dir out
```

### 2. 通过Claude Code技能运行
```bash
claude -p "/generate-nutrition-data"
```

## 输出文件

- `out/nutritions.json` - 包含所有食材的详细营养信息和NRV/DV值
- `out/nutrition_map.json` - 食材与USDA营养数据的匹配关系

## 数据格式

生成的营养信息JSON格式如下：

```json
[
  {
    "usda_id": "172193",
    "ingredient_name": "低脂牛奶",
    "usda_name": "Milk, reduced fat, fluid, 2% milkfat, with added nonfat milk solids, without added vitamin A",
    "nutrients": {
      "energy": {
        "value": 50,
        "unit": "kcal",
        "nrp_pct": 2.5,  // NRV/DV百分比
        "standard": "中国GB标准"  // 使用的计算标准
      },
      "protein": {
        "value": 3.3,
        "unit": "g",
        "nrp_pct": 5.5,
        "standard": "中国GB标准"
      }
      // ... 更多营养素
    }
  }
  // ... 更多食材
]
```

## 计算标准

- **中国GB标准**：按照《预包装食品营养标签通则》(GB 28050-2011)的营养素参考值计算
- **美国FDA标准**：按照美国食品药品监督管理局的日常摄入量标准计算
- **计算公式**：NRV% = (食品中某营养素含量 / 该营养素NRV值) × 100%

## 核心流程

1. **数据获取**：从USDA FoodData Central获取营养数据库
2. **食材匹配**：使用`match-ingredients`技能将食材与USDA数据库匹配
3. **营养计算**：根据中国GB标准优先、美国FDA标准补充的原则计算NRV/DV值
4. **数据输出**：生成标准化的营养信息JSON文件

## 依赖项

- `match-ingredients` 技能：用于食材与USDA数据库的精准匹配
- `out/ingredients.json`：作为输入数据源

## 注意事项

- 如需使用真实的USDA API数据，请在环境变量中设置`USDA_API_KEY`
- 匹配成功率取决于食材名称与USDA数据库的对应程度
- 单位不匹配时会标注"单位不匹配，无法计算百分比"