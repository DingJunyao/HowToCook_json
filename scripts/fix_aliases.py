"""
修复 ingredients.json 中的 aliases 字段

移除 aliases 数组中与 ingredient_name 相同的条目
"""

import json
import sys
from pathlib import Path


def fix_aliases(json_path: str) -> bool:
    """
    修复 JSON 文件中的 aliases 字段

    Args:
        json_path: JSON 文件路径

    Returns:
        是否成功
    """
    try:
        # 读取 JSON 文件
        with open(json_path, 'r', encoding='utf-8') as f:
            ingredients = json.load(f)

        if not isinstance(ingredients, list):
            print("Error: JSON 文件内容不是数组")
            return False

        # 修复每个食材的 aliases
        fixed_count = 0
        for ingredient in ingredients:
            ingredient_name = ingredient.get('ingredient_name')
            aliases = ingredient.get('aliases', [])

            if not ingredient_name:
                continue

            # 过滤掉与 ingredient_name 相同的别名
            filtered_aliases = [alias for alias in aliases if alias != ingredient_name]

            # 如果有变化，更新数组
            if len(filtered_aliases) != len(aliases):
                ingredient['aliases'] = sorted(filtered_aliases)
                fixed_count += 1

        # 保存修复后的文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(ingredients, f, ensure_ascii=False, indent=2)

        print(f"成功修复 {fixed_count} 个食材的 aliases")
        return True

    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python fix_aliases.py <json文件路径>")
        print("示例: python fix_aliases.py out/ingredients.json")
        sys.exit(1)

    json_path = sys.argv[1]

    if not Path(json_path).exists():
        print(f"Error: 文件不存在: {json_path}")
        sys.exit(1)

    if fix_aliases(json_path):
        print(f"修复完成: {json_path}")
        sys.exit(0)
    else:
        print(f"修复失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
