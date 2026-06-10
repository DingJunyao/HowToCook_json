# HowToCook 菜谱解析工具

将 HowToCook 项目中的菜谱 Markdown 文件解析为标准化的 JSON 格式，并提供食材标准化处理功能。

本项目也附带了解析结果，可以直接使用。

## 📋 目录

- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [使用方法](#使用方法)
- [输出说明](#输出说明)
- [营养信息生成功能](#营养信息生成功能)
- [配置说明](#配置说明)
- [项目结构](#项目结构)

## ✨ 功能特性

- 📝 **菜谱解析**：自动解析 HowToCook 项目的 Markdown 菜谱文件
- 🖼️ **图片提取**：从菜谱中提取并保存相关图片
- 🥬 **食材标准化**：统一食材名称和单位格式
- 🧪 **营养信息生成**：从USDA SR数据库获取营养数据并计算NRV/DV值
- 🔄 **自动重试**：支持失败自动重试机制
- ⚙️ **灵活配置**：支持通过配置类调整各项参数

## 🔧 环境要求

### 必需软件

- **Python 3.6+**
- **Git**
- **Git LFS** (用于拉取图片资源)
- **Claude Code CLI** (用于 AI 解析)

### Git LFS 安装

#### macOS
```bash
brew install git-lfs
git lfs install
```

#### Linux (Debian/Ubuntu)
```bash
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
sudo apt-get install git-lfs
git lfs install
```

#### Windows
```powershell
winget install --id GitHub.GitLFS
# 或
choco install git-lfs
```

## 📦 安装步骤

1. **克隆项目**
```bash
git clone <your-repo-url>
cd HowToCook_json
```

2. **安装依赖**（如有需要）
```bash
pip install -r requirements.txt
```

3. **验证 Claude Code 安装**
```bash
claude --version
```

## 🚀 使用方法

### 完整 AI 解析流程

解析所有菜谱、提取图片、标准化食材，并生成营养信息：

```bash
python parse_recipes.py
```

> 之后还需要手工修正结果。为此使用工具 [HowToCook_json_organizer](https://github.com/DingJunyao/HowToCook_json_organizer)。实际上直接使用那个工具也行，因为 AI 解析效果并不理想。

### 仅解析菜谱

```bash
python parse_recipes.py --parse-recipe
```

### 仅解析食材

```bash
python parse_recipes.py --parse-ingredient
```

### 仅添加图片

```bash
python parse_recipes.py --add-images
```

### 流程A：匹配 USDA ID

将食材匹配到 USDA SR Legacy 数据库的 ID，生成 `matched_ingredients.json`：

```bash
python scripts/recipe_parser.py --match-usda-id
```

> **注意**：该步骤还不完善，匹配成功率极低。一定要检查生成文件，确认匹配正常。

### 流程B：生成营养信息

根据已匹配的 ID 生成营养信息，生成 `nutritions.json`：

```bash
python scripts/recipe_parser.py --match-nutrition
```

**注意：** 流程B 需要先运行流程A，生成 `matched_ingredients.json` 文件。

### 执行完整 AI 解析流程（流程A + 流程B）

同时匹配 USDA ID 和生成营养信息：

```bash
python scripts/recipe_parser.py --match-usda-id --match-nutrition
```

或直接运行完整流程（包含菜谱解析）：

```bash
python scripts/recipe_parser.py
```

### 仅解析指定数量的菜谱（测试模式）

用于测试解析效果，仅解析前 N 道菜谱：

```bash
python parse_recipes.py --limit 2
```

### 使用现有仓库

```bash
python parse_recipes.py --repo-path /path/to/HowToCook
```

### 指定输出目录

```bash
python parse_recipes.py --output-dir ./my_output
```

### 详细日志

```bash
python parse_recipes.py -v
```

### 命令行参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--repo-path` | HowToCook 仓库路径 | 自动克隆 |
| `--output-dir` | 输出目录 | `./out` |
| `--temp-dir` | 临时目录（克隆用） | 系统临时目录 |
| `--verbose`, `-v` | 启用详细日志 | `False` |
| `--parse-recipe` | 仅解析菜谱 | `False` |
| `--parse-ingredient` | 仅解析食材 | `False` |
| `--add-images` | 仅添加图片 | `False` |
| `--match-usda-id` | 流程A：匹配 USDA ID | `False` |
| `--match-nutrition` | 流程B：生成营养信息 | `False` |
| `--limit` | 限制解析的菜谱数量（测试用） | `None` |

## 📤 输出说明

### 输出目录结构

```
out/
├── images/                 # 菜谱图片
│   ├── gongbaojiding_0.jpg
│   └── ...
├── hongshaorou.json        # 红烧肉菜谱
├── gongbaojiding.json      # 宫保鸡丁菜谱
├── ...
├── ingredients.json        # 标准化食材列表（dict 格式，含 USDA ID）
├── ingredients_raw.json    # 原始食材列表
├── matched_ingredients.json  # 匹配的食材（包含 USDA ID）
├── nutritions.json         # 营养信息数据
├── units.json              # 单位标准化列表
```

### 菜谱 JSON 格式

> 介绍的是经 [HowToCook_json_organizer](https://github.com/DingJunyao/HowToCook_json_organizer) 校准后的格式。下同。

```json
{
  "name": "菜名",
  "source_file": "dishes/xxx/xxx.md",
  "category": "荤菜",
  "difficulty": "medium",
  "total_time_minutes": null,
  "servings": 1,
  "original_servings": 1,
  "images": [
    "images/gongbaojiding_0.jpg"
  ],
  "ingredients": [
    {
      "ingredient_name": "食材名",
      "quantity": 350.0,
      "unit": "g",
      "original_quantity": "",
      "is_approximate": false,
      "is_estimated": false,
      "is_optional": false,
      "note": "",
      "quantity_description": "",
      "quantity_range": null
    }
  ],
  "steps": [
    {
      "content": "步骤描述",
      "duration_minutes": null,
      "tips": ""
    }
  ],
  "tips": [
    "注意事项"
  ],
  "description": "菜谱简介"
}
```

#### 菜谱字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `name` | 菜名 | `"宫保鸡丁"` |
| `source_file` | 源 Markdown 文件路径 | `"dishes/meat_dish/宫保鸡丁/宫保鸡丁.md"` |
| `category` | 菜系分类 | `"荤菜"` |
| `difficulty` | 难度等级 | `"easy"`, `"medium"`, `"hard"` |
| `total_time_minutes` | 总烹饪时间（分钟） | `null` 或 `45` |
| `servings` | 份数 | `1` |
| `original_servings` | 原始菜谱份数 | `1` |
| `images` | 图片路径列表 | `["images/宫保鸡丁_0.jpg"]` |
| `ingredients` | 食材列表（见下表） | |
| `steps` | 步骤列表（见下表） | |
| `tips` | 注意事项列表 | `["辣椒依据个人口味酌量添加"]` |
| `description` | 菜谱简介 | `"老派川菜的简单做法分享"` |

#### 食材字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `ingredient_name` | 食材名称 | `"手枪腿"` |
| `quantity` | 食材数量（数值） | `350.0` |
| `unit` | 单位 | `"g"`, `"mL"`, `"个"` |
| `original_quantity` | 原始文本中的数量 | `""` |
| `is_approximate` | 是否为约量 | `false` |
| `is_estimated` | 是否为估算值 | `false` |
| `is_optional` | 是否为可选食材 | `false` |
| `note` | 备注 | `"或者鸡胸脯肉"` |
| `quantity_description` | 数量描述文本 | `""` |
| `quantity_range` | 数量范围 | `null` 或 `{"min": 10, "max": 20}` |

#### 步骤字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `content` | 步骤描述 | `"鸡丁用料酒腌制 15 分钟"` |
| `duration_minutes` | 耗时（分钟） | `null` 或 `15` |
| `tips` | 小贴士 | `""` 或 `"注意火候"` |

### 食材 JSON 格式

食材列表以字典形式组织，键名为标准化后的食材名称：

```json
{
  "西葫芦": {
    "name": "西葫芦",
    "aliases": [
      "笋瓜"
    ],
    "category": "蔬菜",
    "usda_id": 2685568,
    "usda_match_status": "matched"
  },
  "鸡蛋": {
    "name": "鸡蛋",
    "aliases": [],
    "category": "禽蛋",
    "usda_id": 171287,
    "usda_match_status": "matched"
  }
}
```

#### 食材字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `name` | 标准化食材名称 | `"西葫芦"` |
| `aliases` | 别名列表 | `["笋瓜"]` |
| `category` | 食材分类 | `"蔬菜"`, `"禽蛋"`, `"调料"`, `"油脂"`, `"主食/谷物"` |
| `usda_id` | USDA SR Legacy 数据库 ID | `2685568` |
| `usda_match_status` | USDA 匹配状态 | `"matched"`，未匹配时为 `"unmatched"` |

### 营养信息 JSON 格式

营养信息以数组形式组织，`nutrients` 字段为营养素数组：

```json
[
  {
    "usda_id": "2685568",
    "ingredient_name": "西葫芦",
    "usda_name": "Squash, summer, green, zucchini, includes skin, raw",
    "nutrients": [
      {
        "name": "铁",
        "name_en": "Iron, Fe",
        "value": 0.194,
        "unit": "毫克",
        "nrp_pct": 1.29,
        "standard": "中国GB标准"
      },
      {
        "name": "蛋白质",
        "name_en": "Protein",
        "value": 0.984,
        "unit": "g",
        "nrp_pct": 1.64,
        "standard": "中国GB标准"
      },
      {
        "name": "热量（Atwater 通用系数）",
        "name_en": "Energy (Atwater General Factors)",
        "value": 19.0,
        "unit": "千卡",
        "nrp_pct": 0.95,
        "standard": "中国GB标准"
      },
      {
        "name": "膳食纤维",
        "name_en": "Fiber, total dietary",
        "value": 0.752,
        "unit": "g",
        "nrp_pct": 3.01,
        "standard": "中国GB标准"
      }
    ]
  }
]
```

#### 营养信息顶层字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `usda_id` | USDA SR Legacy 数据库中的唯一标识符 | `"2685568"` |
| `ingredient_name` | 中文食材名称 | `"西葫芦"` |
| `usda_name` | USDA 数据库中的食物英文名称 | `"Squash, summer, green, zucchini, includes skin, raw"` |
| `nutrients` | 营养素数组 | 见下方字段结构 |

#### 营养素数组元素字段说明

每个营养素元素包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `name` | 中文营养素名称 | `"铁"`, `"蛋白质"`, `"钙"` |
| `name_en` | 英文营养素名称（USDA 命名） | `"Iron, Fe"`, `"Protein"` |
| `value` | 营养素含量值 | `0.194` |
| `unit` | 营养素单位（中文） | `"毫克"`, `"g"`, `"千卡"`, `"μg"` |
| `nrp_pct` | 营养素参考值百分比（NRV/DV%） | `1.29` |
| `standard` | 使用的标准 | `"中国GB标准"`, `"美国FDA标准"`, `"无标准"` |
| `note` | 备注（如有） | `"该营养素无对应的NRV/DV标准值"` |

> 注意：由于菜谱格式不统一，尽管使用 AI 解析，但结果可能仍然存在错误，如有需要，请自行检查并手动修改。
> 你也可以创建 PR，为该项目做贡献。

## 🧪 营养信息生成功能

新功能：现在项目支持生成食材的营养信息！

### 功能特点

- **双流程设计**：将匹配 USDA ID 和生成营养信息拆分为两个独立流程
- **多标准支持**：优先使用中国GB 28050-2011标准计算NRV%，如无对应标准则使用美国FDA标准计算DV%
- **全面营养素覆盖**：包含能量、宏量营养素（蛋白质、脂肪、碳水化合物）、矿物质和维生素等
- **智能匹配**：利用 match-ingredients 技能将食材与 USDA SR 数据库中的营养数据进行匹配
- **标准化输出**：生成格式统一的 JSON 文件，包含详细的营养成分及 NRV/DV 百分比
- **单位智能处理**：自动处理 Unicode 字符差异（µ vs μ）、单位转换（kJ ↔ kcal）、测量方法描述词（DFE, NE, RAE, α-TE）

### 使用方法

运行营养信息匹配只需添加 `--match-nutritions` 参数：

```bash
# 仅运行营养信息匹配
python parse_recipes.py --match-nutritions

# 或在完整流程中（营养信息生成会自动在最后运行）
python parse_recipes.py
```

### 输出文件

- `out/nutritions.json` - 包含所有食材的详细营养信息和NRV/DV值

### 核心流程

1. **数据获取**：从USDA SR数据库获取营养数据
2. **食材匹配**：使用match-ingredients技能将食材与USDA数据库匹配
3. **营养计算**：根据中国GB标准优先、美国FDA标准补充的原则计算NRV/DV值
4. **数据输出**：生成标准化的营养信息JSON文件

### 营养素含义说明

营养数据中的 `name`（中文名称）和 `name_en`（英文名称，USDA 命名）字段标识营养素种类。以下是主要营养素的参考信息：

#### 主要营养素（中国GB 28050-2011 标准）

| name（中文名称） | name_en（英文名称） | 标准值 | 说明 |
|----------------|-------------------|--------|------|
| 能量 | Energy | 2000 kcal | 每100g/100ml食物提供的热量 |
| 蛋白质 | Protein | 60 g | 构成人体组织的主要成分 |
| 脂肪 | Total lipid (fat) | 60 g | 提供能量和必需脂肪酸 |
| 碳水化合物 | Carbohydrate, by difference | 300 g | 主要的能量来源 |
| 膳食纤维 | Fiber, total dietary | 25 g | 不能被人体消化吸收的碳水化合物 |
| 糖 | Sugars, total | 50 g | 碳水化合物中的一种 |
| 饱和脂肪 | Fatty acids, total saturated | 20 g | 可能增加心血管疾病风险 |
| 钠 | Sodium, Na | 2000 mg | 调节体液平衡 |
| 胆固醇 | Cholesterol | 300 mg | 细胞膜重要成分 |
| 钙 | Calcium, Ca | 800 mg | 骨骼和牙齿健康必需 |
| 铁 | Iron, Fe | 15 mg | 血红蛋白合成必需 |
| 锌 | Zinc, Zn | 15 mg | 免疫系统功能必需 |
| 硒 | Selenium, Se | 50 μg | 抗氧化作用 |
| 维生素A | Vitamin A, RAE | 800 μg RAE | 视觉和免疫功能 |
| 维生素D | Vitamin D (D2 + D3) | 5 μg | 钙吸收必需 |
| 维生素E | Vitamin E (alpha-tocopherol) | 10 mg α-TE | 抗氧化作用 |
| 维生素C | Vitamin C, total ascorbic acid | 100 mg | 抗氧化和免疫功能 |
| 维生素B1（硫胺素） | Thiamin | 1.4 mg | 能量代谢 |
| 维生素B2（核黄素） | Riboflavin | 1.4 mg | 能量代谢 |
| 维生素B6 | Vitamin B-6 | 1.4 mg | 氨基酸代谢 |
| 维生素B12 | Vitamin B-12 | 2.4 μg | DNA合成 |
| 叶酸 | Folate, total | 400 μg DFE | 细胞分裂和DNA合成 |
| 烟酸 | Niacin | 14 mg NE | 能量代谢 |
| 泛酸 | Pantothenic acid | 6 mg | 能量代谢 |
| 生物素 | Biotin | 30 μg | 碳水化合物和脂肪代谢 |
| 维生素K | Vitamin K (phylloquinone) | 80 μg | 血液凝固和骨骼健康 |

#### 常见营养素说明

**NRV（Nutrient Reference Values，营养素参考值）**：根据中国GB 28050-2011标准，表示成年人每日需要摄入的各种营养素参考值。

**DV（Daily Values，每日值）**：根据美国FDA标准，表示成年人每日需要摄入的各种营养素参考值。

**nrp_pct**：营养素参考值百分比，表示该食物提供的营养素占每日推荐摄入量的百分比。

**单位说明**：
- **千卡/千焦**：能量单位（nutritions.json 中使用中文字单位，如 `"千卡"`、`"g"`、`"毫克"`）
- **g**：克
- **毫克**：毫克（1g = 1000mg）
- **μg**：微克（1mg = 1000μg）
- **DFE**：膳食叶酸当量（Dietary Folate Equivalent）
- **NE**：烟酸当量（Niacin Equivalent）
- **RAE**：视黄醇活性当量（Retinol Activity Equivalent）
- **α-TE**：α-生育酚当量（alpha-Tocopherol Equivalent）

**重要提示**：
1. 调料类食材（如盐、酱油）的某些营养素含量可能超过100%，这是正常的
2. nrp_pct = 0 表示该营养素在食物中含量极低或不存在
3. 标记为"无标准"的营养素是中国/美国标准未定义的营养素
4. 部分营养素可能显示"该营养素无对应的NRV/DV标准值"备注

> 关于完整的 147 种营养素详细说明（含脂肪酸分类），请参考：
> - [docs/营养素详细说明.md](docs/营养素详细说明.md)
> - [docs/营养素分析摘要.md](docs/营养素分析摘要.md)

## ⚙️ 配置说明

项目使用 `RecipeParserConfig` 类集中管理配置，可通过修改源代码调整：

- **仓库配置**：仓库 URL、菜品目录名
- **超时配置**：Claude 命令、Git 操作超时时间
- **重试配置**：最大重试次数
- **图片配置**：默认图片扩展名
- **输出配置**：默认输出目录、文件名

## 📁 项目结构

```
HowToCook_json/
├── README.md              # 项目说明文档
├── .gitignore            # Git 忽略规则
├── parse_recipes.py      # 主入口脚本
├── scripts/
│   ├── recipe_parser.py  # 核心解析器
│   ├── nutrition_generator.py # 营养信息生成器
│   └── recipe_schema.json # JSON Schema 定义
└── out/                  # 输出目录（自动生成）
    ├── images/           # 图片资源
    ├── *.json           # 菜谱文件
    ├── ingredients.json  # 食材列表（dict 格式，含 USDA ID）
    ├── ingredients_raw.json # 原始食材列表
    ├── matched_ingredients.json # 匹配 USDA ID 后的食材列表
    ├── nutritions.json   # 营养信息
    └── units.json        # 单位标准化列表
```

> 更多详细信息请参考：
> - [docs/营养素分析摘要.md](docs/营养素分析摘要.md) - 快速了解 147 种营养素分类和统计数据
> - [docs/营养素详细说明.md](docs/营养素详细说明.md) - 完整的 147 种营养素详细说明（含中英文对照）
> - [docs/详细脂肪酸营养素说明.md](docs/详细脂肪酸营养素说明.md) - 专业的脂肪酸分类和健康影响
> - [docs/营养匹配流程说明.md](docs/营养匹配流程说明.md) - 营养匹配流程使用指南
> - [docs/功能更新总结_流程拆分与营养素说明.md](docs/功能更新总结_流程拆分与营养素说明.md) - 功能更新历史

## 📝 许可证

本项目遵循原 HowToCook 项目的许可证。

## 🙏 致谢

原始菜谱数据来自 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)
