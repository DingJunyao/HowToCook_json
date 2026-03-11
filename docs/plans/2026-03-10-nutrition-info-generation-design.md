# 营养信息生成功能设计文档

## 1. 功能概述

本功能旨在为HowToCook项目添加营养信息生成功能，从USDA FoodData Central获取营养数据，计算NRV/DV值，并生成相应的JSON输出文件。

## 2. 设计目标

- 从USDA FoodData Central获取全面的营养信息
- 基于中国GB标准优先、美国FDA标准补充的方式计算NRV/DV值
- 与现有`match-ingredients`技能无缝集成
- 生成包含详细营养信息和NRV/DV值的JSON文件

## 3. 实现步骤

### 步骤1: 数据获取
- 从USDA FoodData Central API获取最新食物营养数据库
- 下载包含全面营养信息的JSON数据文件
- 支持包括热量、宏量营养素、维生素、矿物质等在内的营养指标

### 步骤2: 数据预处理
- 提取USDA数据中的ID和名称信息
- 创建便于后续匹配查询的精简格式
- 处理数据格式使其适合食材匹配过程

### 步骤3: 食材匹配
- 读取`out/ingredients.json`获取当前原料数据
- 调用`match-ingredients`技能将食材与USDA数据库进行匹配
- 生成`out/nutrition_map.json`映射文件

### 步骤4: 营养信息检索
- 根据匹配结果从USDA数据中检索完整营养信息
- 关联食材与其详细的营养成分数据

### 步骤5: NRV/DV计算
- 使用中国GB标准作为主要参考值
- 对于中国标准未涵盖的营养素，使用美国FDA标准
- 计算每种营养素的百分比贡献值

### 步骤6: 数据输出
- 生成`out/nutritions.json`文件
- 包含完整的营养信息和NRV/DV值
- 确保数据格式标准化、易于消费

## 4. NRV/DV标准参考

### 4.1 中国GB 28050-2011 NRV参考值
- 能量: 8400 kJ
- 蛋白质: 60 g
- 脂肪: ≤60 g
- 饱和脂肪: ≤20 g
- 碳水化合物: 300 g
- 糖: ≤50 g
- 钠: 2000 mg
- 胆固醇: ≤300 mg
- 钙: 800 mg
- 铁: 15 mg
- 锌: 15 mg
- 硒: 50 μg
- 维生素A: 800 μg RE
- 维生素D: 5 μg
- 维生素E: 10 mg α-TE
- 维生素B1: 1.4 mg
- 维生素B2: 1.4 mg
- 维生素B6: 1.4 mg
- 维生素B12: 2.4 μg
- 维生素C: 100 mg
- 叶酸: 400 μg DFE
- 烟酸: 14 mg NE
- 泛酸: 6 mg
- 生物素: 30 μg
- 维生素K: 80 μg

### 4.2 美国FDA Daily Value (DV)参考值
- 能量: 2000 kcal
- 总脂肪: 78 g
- 饱和脂肪: 20 g
- 胆固醇: 300 mg
- 钠: 2400 mg
- 总碳水化合物: 300 g
- 膳食纤维: 25 g
- 总糖: 包含在碳水化合物中
- 蛋白质: 50 g
- 维生素A: 900 μg RAE
- 维生素C: 90 mg
- 维生素D: 20 μg
- 维生素E: 15 mg
- 维生素K: 120 μg
- 钙: 1300 mg
- 铁: 18 mg
- 镁: 420 mg
- 磷: 1250 mg
- 钾: 4700 mg
- 锌: 11 mg

## 5. 输出JSON格式

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
        "nrp_pct": 2.5,
        "standard": "中国GB标准"
      },
      "protein": {
        "value": 3.3,
        "unit": "g",
        "nrp_pct": 5.5,
        "standard": "中国GB标准"
      },
      "fat": {
        "value": 2.1,
        "unit": "g",
        "nrp_pct": 3.5,
        "standard": "中国GB标准"
      },
      "carbohydrate": {
        "value": 4.8,
        "unit": "g",
        "nrp_pct": 1.6,
        "standard": "中国GB标准"
      },
      "calcium": {
        "value": 124,
        "unit": "mg",
        "nrp_pct": 15.5,
        "standard": "中国GB标准"
      }
    }
  }
]
```

## 6. 错误处理策略

- 如果无法从USDA获取特定食材的营养数据，记录警告但不中断整个流程
- 对于营养素数值异常（如负值或明显错误的数据），进行验证和过滤
- 匹配失败的食材将在输出中标记，以便后续人工审核

## 7. 扩展性考虑

- 支持配置不同的营养标准
- 可调整的营养数据精度和详细程度
- 支持添加新的营养数据库源