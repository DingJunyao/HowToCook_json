---
name: match-ingredients
description: 将给定列表的食材与 USDA 数据库匹配，并返回匹配结果。
---
# match-ingredients 技能

## 目标

给定食材列表，将食材与 USDA 数据库里面的食材匹配，并返回匹配结果。

## 输入

给定以下两个文件：

- 第一个参数：包含食材列表的 JSON 文件路径。对应的 JSON 格式如下：

```json
[
  {
    "ingredient_name": "西葫芦",
    "aliases": [],
    "category": "vegetables",
    "unit": "g"
  },
  {
    "ingredient_name": "鸡蛋",
    "aliases": [],
    "category": "eggs",
    "unit": "个"
  },
  ...
]
```

- 第二个参数：从 USDA 间接获得的 JSON 文件路径。该文件包含各食材的营养信息，格式如下：

```json
[
  {
    "id": "172193",
    "name": "Milk, reduced fat, fluid, 2% milkfat, with added nonfat milk solids, without added vitamin A",
    ...
  },
  ...
]
```

- 第三个参数：匹配结果保存的 JSON 文件路径。

## 输出

生成 JSON 文件。文件路径为第三个参数设定的路径。如果没有，则生成到 `out/matched_ingredients.json`。

JSON 格式如下：

```json
[
  {
    "ingredient_name": "低脂牛奶",
    "usda_id": "172193",
    "usda_name": "Milk, reduced fat, fluid, 2% milkfat, with added nonfat milk solids, without added vitamin A",
  },
  ...
]
```

## 要点

- 简单来说，就是判断食材与 USDA 食材库里面的哪一项最为类似。
- 判断类似，是按照整个 USDA 食材名称来看的，不能仅凭其中一部分看。比如说”Watermelon, raw”，需要匹配为”西瓜”，而不能因为其中有”water”就匹配为”水”！
- **非常重要：禁止写脚本进行匹配**。必须使用你的智能分析能力进行语义匹配，而不是通过编写程序或脚本来处理数据。
- **避免错误的匹配，特别注意以下原则**：
  - 匹配时要关注食材的主体/本质，而不是配料或加工方式
  - "食用油"应该匹配油脂类基本原料，而不是用油制作的零食
  - "盐"应该匹配基本盐类，而不是含盐的食品
  - "水"应该匹配纯净水，而不是含水的食品
  - 优先匹配名称中包含食材基本成分的条目，而不是名称中有部分词汇重叠的条目
  - 对于鱼类食材，优先区分淡水鱼和海水鱼，若无合适分类可使用"Fish, mixed species"作为通用匹配，不要强行匹配特定品种（如将所有淡水鱼都匹配为catfish/鲇鱼）
  - "奶粉"类应匹配到干燥奶粉制品，而非鲜奶
  - 面条类食材应寻找合适的面条匹配，而非米饭或其他谷物
  - 调料类应匹配到相应调料而非成品菜肴
  - 对于没有精确匹配的特殊食材（如食品添加剂），选择最接近的同类产品作为参考
  - 肉类制品应区分生熟状态，一般食材默认为生鲜状态
  - 蔬菜类食材应尽量匹配到对应类别，避免跨类别错误匹配（如将菠菜匹配为生菜）
  - 避免将不同类型的食材错误关联，如饮品与固体食品、调味品与主食材等
  - 在匹配置信度较低时，选择更通用的类别而非可能错误的特定类别
- **特殊食材处理规则**：
  - 水类：纯净水 -> "Water, bottled, non-carbonated, [brand]"
  - 油类：各种食用油 -> "Oil, [oil type], salad or cooking"
  - 奶粉：奶粉制品 -> "Milk, dry, [type], with added vitamin D"
  - 酱油/调料：各类调料 -> 相应调味品类别
  - 面条：荞麦面等 -> "Noodles, cooked, without added salt" 或类似面条类
  - 肉类：特定肉品 -> 具体肉类，通用肉类 -> "Meat, [type], raw"
  - 鱼类：按淡水/海水分类，无明确分类则用"Fish, mixed species"
- **验证匹配结果**：在输出前，对自己进行二次验证，确保匹配结果符合逻辑和常识
  - 检查是否出现明显错误的匹配，如：含品牌名的产品、餐厅菜品、糖果、快餐食品等
  - 检查食材与其匹配结果在物理性质上是否匹配（固态vs液态、生鲜vs加工品等）
  - 检查食材分类是否合理（鱼类归鱼类、肉类归肉类、蔬菜归蔬菜等）
  - 检查是否存在明显的跨类别错误（如将绿叶蔬菜匹配为根茎类或果实类）
  - 确认食材的营养特征是否大致匹配（如高纤维食材应当匹配到相应高纤维食品）
- 输出的文件必须符合上面的要求。
- 必须处理好全部的给定食材，也就是说，包含食材列表的 JSON 文件里面有多少个项目，输出的 JSON 文件里面也要有那么多项目。不允许缺少或多出项目。
- 如果检查发现输出结果存在问题，请直接自己处理，不需要询问。执行此技能时，一般通过 `-p` 参数，所以我无法回答你的询问。
- 如果没有指定输出文件路径，则生成到 `out/matched_ingredients.json`，不允许别的名称。输出文件有且只有一个，如果有问题，则原位修改。
- **匹配完成后验证步骤**：
  - 检查是否存在高频重复匹配（某一条目被多个不同类型食材共享）：若有超过10个食材共享同一USDA条目，需重新评估匹配合理性
  - 检查是否存在语义错配：如水类食材匹配到含水量高的果蔬，调料匹配到成品菜肴等
  - 验证关键食材匹配：对鱼类、肉类、调料等关键食材的匹配结果进行二次人工核查

## 参考

### 正确例子

```json
{
  "ingredient_name": "葱",
  "usda_id": "4829929721947263855",
  "usda_name": "Onions, spring or scallions (includes tops and bulb), raw"
},
{
  "ingredient_name": "荞麦面",
  "usda_id": "174258",
  "usda_name": "Noodles, cooked, without added salt"
},
{
  "ingredient_name": "培根片",
  "usda_id": "170047",
  "usda_name": "Bacon, pre-sliced, cooked"
}
```

### 错误例子

绝对不要犯这种错误！

```json
{
  "ingredient_name": "猪肉",
  "usda_id": "-5633805580547018161",
  "usda_name": "Kraft Foods, Shake N Bake Original Recipe, Coating for Pork, dry"
}, // 名称里面带 pork 不一定是猪肉，这只是调味酱
{
  "ingredient_name": "面粉",
  "usda_id": "5513811906290135769",
  "usda_name": "Pie crust, deep dish, frozen, unbaked, made with enriched flour"
}, // 名称里面带 flour 不一定是面粉，这只是饼皮
{
  "ingredient_name": "水",
  "usda_id": "4127147529829287979",
  "usda_name": "Watermelon, raw"
}, // 名称中带 water 不一定是水，西瓜的单词也包含 water
{
  "ingredient_name": "菠菜",
  "usda_id": "168429",
  "usda_name": "Lettuce, butterhead (includes boston and bibb types), raw"
} // 菠菜不应当匹配到生菜，这是跨类别错误
```