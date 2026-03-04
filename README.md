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

## ✨ 功能特性

- 📝 **菜谱解析**：自动解析 HowToCook 项目的 Markdown 菜谱文件
- 🖼️ **图片提取**：从菜谱中提取并保存相关图片
- 🥬 **食材标准化**：统一食材名称和单位格式
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

解析所有菜谱、提取图片、标准化食材：

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
└── ingredients.json        # 标准化食材列表
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

> 注意：由于菜谱格式不统一，尽管使用 AI 解析，但结果可能仍然存在错误，如有需要，请自行检查并手动修改。
> 你也可以创建 PR，为该项目做贡献。

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
│   └── receipe_schema.json # JSON Schema 定义
└── out/                  # 输出目录（自动生成）
    ├── images/           # 图片资源
    ├── *.json           # 菜谱文件
    └── ingredients.json  # 食材列表
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

## 📝 许可证

本项目遵循原 HowToCook 项目的许可证。

## 🙏 致谢

原始菜谱数据来自 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)
