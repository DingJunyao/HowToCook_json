# HowToCook 菜谱解析工具

将 HowToCook 项目中的菜谱 Markdown 文件解析为标准化的 JSON 格式，并提供食材标准化处理功能。

本项目也附带了解析结果，可以直接使用。

## 📋 目录

- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [使用方法](#使用方法)
- [输出说明](#输出说明)
- [配置说明](#配置说明)
- [项目结构](#项目结构)
- [营养信息生成功能](#营养信息生成功能)

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

### 完整解析流程

解析所有菜谱、提取图片、标准化食材，并生成营养信息：

```bash
python parse_recipes.py
```

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

### 流程B：生成营养信息

根据已匹配的 ID 生成营养信息，生成 `nutritions.json`：

```bash
python scripts/recipe_parser.py --match-nutrition
```

**注意：** 流程B 需要先运行流程A，生成 `matched_ingredients.json` 文件。

### 执行完整流程（流程A + 流程B）

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
├── ingredients.json        # 标准化食材列表
├── matched_ingredients.json  # 匹配的食材（包含 USDA ID）
├── nutritions.json         # 营养信息数据
└── nutrition_map.json      # 食材与营养数据库映射
```

### 菜谱 JSON 格式

```json
{
  "name": "菜名",
  "source_file": "dishes/xxx/xxx.md",
  "category": "菜系分类",
  "difficulty": "难度",
  "servings": 2,
  "ingredients": [
    {
      "ingredient_name": "食材名",
      "amount": "数量",
      "unit": "单位"
    }
  ],
  "steps": [
    {
      "step": 1,
      "description": "步骤描述"
    }
  ],
  "images": [
    "images/gongbaojiding_0.jpg"
  ]
}
```

### 食材 JSON 格式

```json
[
  {
    "ingredient_name": " standardized name",
    "aliases": ["alias1", "alias2"],
    "unit": "standardized unit"
  }
]
```

### 营养信息 JSON 格式

```json
[
  {
    "usda_id": "172193",
    "ingredient_name": "低脂牛奶",
    "usda_name": "Milk, reduced fat, fluid, 2% milkfat, with added nonfat milk solids, without added vitamin A",
    "nutrients": {
      "energy_kcal": {
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
      "carbohydrate": {
        "value": 4.8,
        "unit": "g",
        "nrp_pct": 1.6,
        "standard": "中国GB标准"
      },
      "fat": {
        "value": 2.1,
        "unit": "g",
        "nrp_pct": 3.5,
        "standard": "中国GB标准"
      },
      "calcium": {
        "value": 120,
        "unit": "mg",
        "nrp_pct": 15.0,
        "standard": "中国GB标准"
      }
    }
  }
]
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `usda_id` | USDA SR Legacy 数据库中的唯一标识符 |
| `ingredient_name` | 中文食材名称（来自匹配结果） |
| `usda_name` | USDA 数据库中的食物英文名称 |
| `nutrients` | 营养素详细信息字典 |

### 营养素字段结构

每个营养素包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `value` | 营养素含量值 | `50` |
| `unit` | 营养素单位 | `"kcal"`, `"g"`, `"mg"`, `"μg"` |
| `nrp_pct` | 营养素参考值百分比（NRV/DV%） | `2.5` |
| `standard` | 使用的标准（中国GB标准或美国FDA标准） | `"中国GB标准"` |
| `note` | 备注（如有单位转换或其他说明） | `"单位已从 kJ 转换为 kcal"` |
```

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

- **多标准支持**：优先使用中国GB 28050-2011标准计算NRV%，如无对应标准则使用美国FDA标准计算DV%
- **全面营养素覆盖**：包含能量、宏量营养素（蛋白质、脂肪、碳水化合物）、矿物质和维生素等
- **智能匹配**：利用match-ingredients技能将食材与USDA SR数据库中的营养数据进行匹配
- **标准化输出**：生成格式统一的JSON文件，包含详细的营养成分及NRV/DV百分比

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
- `out/nutrition_map.json` - 食材与USDA营养数据的匹配关系

### 核心流程

1. **数据获取**：从USDA SR数据库获取营养数据
2. **食材匹配**：使用match-ingredients技能将食材与USDA数据库匹配
3. **营养计算**：根据中国GB标准优先、美国FDA标准补充的原则计算NRV/DV值
4. **数据输出**：生成标准化的营养信息JSON文件

### 营养素含义说明

#### 主要营养素（中国GB 28050-2011 标准）

| 营养素键名 | 中文名称 | 标准值 | 单位 | 说明 |
|-----------|---------|--------|------|------|
| `energy_kcal` | 能量 | 2000 | kcal | 每100g/100ml食物提供的热量 |
| `energy_kj` | 能量 | 8400 | kJ | 每公斤焦耳 |
| `protein` | 蛋白质 | 60 | g | 构成人体组织的主要成分 |
| `fat` | 脂肪 | 60 | g | 提供能量和必需脂肪酸 |
| `carbohydrate` | 碳水化合物 | 300 | g | 主要的能量来源 |
| `sugar` | 糖 | 50 | g | 碳水化合物中的一种 |
| `fiber` | 膳食纤维 | 25 | g | 不能被人体消化吸收的碳水化合物 |
| `saturated_fat` | 饱和脂肪 | 20 | g | 可能增加心血管疾病风险 |
| `sodium` | 钠 | 2000 | mg | 调节体液平衡 |
| `cholesterol` | 胆固醇 | 300 | mg | 细胞膜重要成分 |
| `calcium` | 钙 | 800 | mg | 骨骼和牙齿健康必需 |
| `iron` | 铁 | 15 | mg | 血红蛋白合成必需 |
| `zinc` | 锌 | 15 | mg | 免疫系统功能必需 |
| `selenium` | 硒 | 50 | μg | 抗氧化作用 |
| `vitamin_a_rae` | 维生素A | 800 | μg RAE | 视觉和免疫功能 |
| `vitamin_d` | 维生素D | 5 | μg | 钙吸收必需 |
| `vitamin_e` | 维生素E | 10 | mg α-TE | 抗氧化作用 |
| `vitamin_c` | 维生素C | 100 | mg | 抗氧化和免疫功能 |
| `vitamin_b1` | 维生素B1（硫胺素） | 1.4 | mg | 能量代谢 |
| `vitamin_b2` | 维生素B2（核黄素） | 1.4 | mg | 能量代谢 |
| `vitamin_b6` | 维生素B6 | 1.4 | mg | 氨基酸代谢 |
| `vitamin_b12` | 维生素B12 | 2.4 | μg | DNA合成 |
| `folate` | 叶酸 | 400 | μg DFE | 细胞分裂和DNA合成 |
| `niacin` | 烟酸 | 14 | mg NE | 能量代谢 |
| `pantothenic_acid` | 泛酸 | 6 | mg | 能量代谢 |
| `biotin` | 生物素 | 30 | μg | 碳水化合物和脂肪代谢 |
| `vitamin_k` | 维生素K | 80 | μg | 血液凝固和骨骼健康 |

#### 常见营养素说明

**NRV（Nutrient Reference Values，营养素参考值）**：根据中国GB 28050-2011标准，表示成年人每日需要摄入的各种营养素参考值。

**DV（Daily Values，每日值）**：根据美国FDA标准，表示成年人每日需要摄入的各种营养素参考值。

**nrp_pct**：营养素参考值百分比，表示该食物提供的营养素占每日推荐摄入量的百分比。

**单位说明**：
- **kcal/kJ**：能量单位
- **g**：克
- **mg**：毫克（1g = 1000mg）
- **μg**：微克（1mg = 1000μg）
- **DFE**：膳食叶酸当量（Dietary Folate Equivalent）
- **NE**：烟酸当量（Niacin Equivalent）
- **RAE**：视黄醇活性当量（Retinol Activity Equivalent）
- **α-TE**：α-生育酚当量（alpha-Tocopherol Equivalent）

**重要提示**：
1. 调料类食材（如盐、酱油）的某些营养素含量可能超过100%，这是正常的
2. nrp_pct = 0 表示该营养素在食物中含量极低或不存在
3. 标记为"无标准"的营养素是中国/美国标准未定义的营养素
4. 部分营养素可能显示"单位已从 X 转换为 Y"，表示进行了单位转换

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
    ├── ingredients.json  # 食材列表
    ├── nutritions.json   # 营养信息
    └── nutrition_map.json # 食材营养映射
```

## 🔍 常见问题

### Q: Git LFS 未安装怎么办？
A: 运行脚本会自动检测并提示安装，请按照提示操作。

### Q: 解析失败会自动重试吗？
A: 是的，默认重试 3 次，可在配置中调整。

### Q: 如何跳过图片下载？
A: 使用 `--parse-recipe` 或 `--parse-ingredient` 参数。

### Q: 可以解析 Fork 的 HowToCook 仓库吗？
A: 可以，使用 `--repo-path` 指定本地路径即可。

### Q: 如何生成营养信息？
A: 使用 `--match-nutrition` 参数单独运行营养信息生成，或者在完整流程中自动运行。

---

### 详细脂肪酸营养素说明

由于 USDA 数据库包含非常详细的脂肪酸分类，`nutritions.json` 中包含大量以 `mufa_`、`pufa_` 和 `sfa_` 开头的营养素键名。这些是专业的脂肪酸分类术语：

#### 主要脂肪酸类型

**MUFA (单不饱和脂肪酸)** - Monounsaturated Fatty Acids
- `mufa_16:1` - 棕榈酸（16:1，棕榈油主要成分）
- `mufa_18:1` / `mufa_18:1_c` - 油酸（18:1，植物油主要成分）

**PUFA (多不饱和脂肪酸)** - Polyunsaturated Fatty Acids
- `pufa_18:2_n_3_cc` - DHA（二十二碳六烯酸顺式，深海鱼，对大脑健康重要）
- `pufa_20:5` - EPA（二十碳五烯酸，深海鱼）
- `pufa_22:6_n_3` - DPA（二十二碳六烯酸n-3，藻油）

**SFA (饱和脂肪酸)** - Saturated Fatty Acids
- `sfa_14:0` - 肉豆蔻酸（14:0，椰子油主要成分）
- `sfa_12:0` - 月桂酸（12:0，植物油）
- `sfa_16:0` - 棕榈酸（16:0，动物脂肪）

#### 键名规则

- `:_n_3` 或 `:_n_6_cc`：碳原子位置的顺式/反式或同分异构体
- `:_t` 或 `:_c`：反式或顺式结构
- `:1`, `:0`：碳原子数量（14:1 表示14个碳原子）

#### 常见食物示例

| 食物 | 特点 | 主要脂肪酸 |
|------|------|----------|
| 深海鱼 | 高 ω-3 | EPA、DHA |
| 亚麻籽油 | 高 ω-3 | α-亚麻酸 |
| 橄榄油 | 高 MUFA | 油酸 |
| 椰子油 | 高 ω-6 | 亚油酸 |
| 椰油 | 高 SFA | 棕榈酸 |
| 椰子油 | 低饱和脂肪 | 平衡脂肪酸 |

#### 健康建议

- **增加 ω-3（EPA/DHA）**：适量食用深海鱼、亚麻籽油
- **控制 SFA**：减少动物脂肪摄入，多用植物油
- **保持 ω-3/ω-6 比例**：现代饮食约 1:1-1:4，地中海饮食可达 1:2

> 更多详细信息请参考：
> - [docs/营养素分析摘要.md](docs/营养素分析摘要.md) - 快速了解 147 种营养素分类和统计数据
> - [docs/营养素详细说明.md](docs/营养素详细说明.md) - 完整的 147 种营养素详细说明（含中英文对照）
> - [docs/详细脂肪酸营养素说明.md](docs/详细脂肪酸营养素说明.md) - 专业的脂肪酸分类和健康影响
> - [docs/营养匹配流程说明.md](docs/营养匹配流程说明.md) - 营养匹配流程使用指南
> - [docs/功能更新总结_流程拆分与营养素说明.md](docs/功能更新总结_流程拆分与营养素说明.md) - 功能更新历史

---

## 🔍 常见问题

## 📝 许可证

本项目遵循原 HowToCook 项目的许可证。

## 🙏 致谢

原始菜谱数据来自 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)
