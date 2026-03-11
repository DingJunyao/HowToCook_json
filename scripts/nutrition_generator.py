#!/usr/bin/env python3
"""
营养信息生成功能
从USDA SR数据获取营养数据，计算NRV/DV值，并生成营养信息JSON文件
"""

import os
import json
import sys
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import tempfile
import subprocess
import re


class NutritionDataProcessor:
    """营养数据处理器"""

    def __init__(self, output_dir: str = "out"):
        self.output_dir = output_dir

        # 配置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # 中国GB 28050-2011 NRV参考值
        self.chinese_nrv_values = {
            "energy_kcal": {"value": 2000, "unit": "kcal", "name": "能量"},
            "energy_kj": {"value": 8400, "unit": "kJ", "name": "能量"},
            "protein": {"value": 60, "unit": "g", "name": "蛋白质"},
            "fat": {"value": 60, "unit": "g", "name": "脂肪"},  # ≤60g
            "saturated_fat": {"value": 20, "unit": "g", "name": "饱和脂肪"},
            "carbohydrate": {"value": 300, "unit": "g", "name": "碳水化合物"},
            "sugar": {"value": 50, "unit": "g", "name": "糖"},
            "sodium": {"value": 2000, "unit": "mg", "name": "钠"},
            "cholesterol": {"value": 300, "unit": "mg", "name": "胆固醇"},
            "calcium": {"value": 800, "unit": "mg", "name": "钙"},
            "iron": {"value": 15, "unit": "mg", "name": "铁"},
            "zinc": {"value": 15, "unit": "mg", "name": "锌"},
            "selenium": {"value": 50, "unit": "μg", "name": "硒"},
            "vitamin_a_rae": {"value": 800, "unit": "μg RAE", "name": "维生素A"},
            "vitamin_d": {"value": 5, "unit": "μg", "name": "维生素D"},
            "vitamin_e": {"value": 10, "unit": "mg α-TE", "name": "维生素E"},
            "vitamin_b1": {"value": 1.4, "unit": "mg", "name": "维生素B1"},
            "vitamin_b2": {"value": 1.4, "unit": "mg", "name": "维生素B2"},
            "vitamin_b6": {"value": 1.4, "unit": "mg", "name": "维生素B6"},
            "vitamin_b12": {"value": 2.4, "unit": "μg", "name": "维生素B12"},
            "vitamin_c": {"value": 100, "unit": "mg", "name": "维生素C"},
            "folate": {"value": 400, "unit": "μg DFE", "name": "叶酸"},
            "niacin": {"value": 14, "unit": "mg NE", "name": "烟酸"},
            "pantothenic_acid": {"value": 6, "unit": "mg", "name": "泛酸"},
            "biotin": {"value": 30, "unit": "μg", "name": "生物素"},
            "vitamin_k": {"value": 80, "unit": "μg", "name": "维生素K"}
        }

        # 美国FDA Daily Value (DV)参考值
        self.usa_dv_values = {
            "energy_kcal": {"value": 2000, "unit": "kcal", "name": "能量"},
            "energy_kj": {"value": 8400, "unit": "kJ", "name": "能量"},
            "total_fat": {"value": 78, "unit": "g", "name": "总脂肪"},
            "saturated_fat": {"value": 20, "unit": "g", "name": "饱和脂肪"},
            "cholesterol": {"value": 300, "unit": "mg", "name": "胆固醇"},
            "sodium": {"value": 2400, "unit": "mg", "name": "钠"},
            "total_carbohydrate": {"value": 300, "unit": "g", "name": "总碳水化合物"},
            "dietary_fiber": {"value": 25, "unit": "g", "name": "膳食纤维"},
            "total_sugars": {"value": 50, "unit": "g", "name": "总糖"},
            "protein": {"value": 50, "unit": "g", "name": "蛋白质"},
            "vitamin_a_rae": {"value": 900, "unit": "μg RAE", "name": "维生素A"},
            "vitamin_c": {"value": 90, "unit": "mg", "name": "维生素C"},
            "vitamin_d": {"value": 20, "unit": "μg", "name": "维生素D"},
            "vitamin_e": {"value": 15, "unit": "mg", "name": "维生素E"},
            "vitamin_k": {"value": 120, "unit": "μg", "name": "维生素K"},
            "calcium": {"value": 1300, "unit": "mg", "name": "钙"},
            "iron": {"value": 18, "unit": "mg", "name": "铁"},
            "magnesium": {"value": 420, "unit": "mg", "name": "镁"},
            "phosphorus": {"value": 1250, "unit": "mg", "name": "磷"},
            "potassium": {"value": 4700, "unit": "mg", "name": "钾"},
            "zinc": {"value": 11, "unit": "mg", "name": "锌"}
        }

    def download_usda_data(self) -> Optional[Dict]:
        """
        从USDA下载SR数据到临时文件，然后加载营养数据
        使用SR Legacy的JSON格式数据
        """
        self.logger.info("正在从USDA获取SR数据...")

        # 创建临时目录来存放下载的数据
        with tempfile.TemporaryDirectory() as temp_dir:
            # USDA SR Legacy数据集的JSON下载链接 (根据网页获取的链接)
            sr_legacy_json_url = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_json_2018-04.zip"

            try:
                import requests
                import zipfile

                self.logger.info(f"正在从 {sr_legacy_json_url} 下载USDA SR JSON数据...")

                # 下载文件
                response = requests.get(sr_legacy_json_url, stream=True)
                response.raise_for_status()

                zip_path = os.path.join(temp_dir, "usda_sr_legacy_json.zip")

                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                self.logger.info(f"已下载SR JSON数据到临时目录: {zip_path}")

                # 解压文件
                self.logger.info("正在解压JSON文件...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                self.logger.info("解压完成")

                # 查找解压后的JSON数据文件 - 现在我们知道文件名格式了
                json_file_path = None
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower().endswith('.json') and 'food' in file.lower() and 'json' in file.lower():
                            json_file_path = os.path.join(root, file)
                            break
                    if json_file_path:
                        break

                if not json_file_path:
                    self.logger.error("未找到食物JSON文件")
                    return None

                # 读取JSON文件
                self.logger.info(f"正在处理食物数据文件: {json_file_path}")

                with open(json_file_path, 'r', encoding='utf-8') as f:
                    food_data = json.load(f)

                # 检查数据格式 - 如果是包含多个表的结构，按相应方式处理
                # 否则认为是简单的食物列表
                foods = []

                if isinstance(food_data, dict):
                    # 检查是否是包含不同表格的结构
                    if 'FoundationFoods' in food_data:
                        raw_foods = food_data['FoundationFoods']
                    elif 'SurveyFoods' in food_data:
                        raw_foods = food_data['SurveyFoods']
                    elif 'SR legacy' in food_data or 'SrLegacyFoods' in food_data:
                        raw_foods = food_data.get('SR legacy', food_data.get('SrLegacyFoods', []))
                    elif 'Foods' in food_data:
                        raw_foods = food_data['Foods']
                    elif 'food' in food_data:
                        raw_foods = food_data['food']
                    else:
                        # 假设整个对象的值是一个食物列表
                        # 遍历字典的值来查找可能的食物列表
                        raw_foods = None
                        for key, value in food_data.items():
                            if isinstance(value, list) and len(value) > 0:
                                if isinstance(value[0], dict) and ('description' in value[0] or 'name' in value[0] or 'food_id' in value[0] or 'fdc_id' in value[0]):
                                    raw_foods = value
                                    break
                        if raw_foods is None:
                            # 如果没找到明显的食物列表，假设整个值就是要处理的数据
                            raw_foods = food_data

                elif isinstance(food_data, list):
                    # 直接是一个食物列表
                    raw_foods = food_data
                else:
                    self.logger.error("无法识别的JSON数据格式 - 数据既不是字典也不是列表")
                    return None

                # 确保 raw_foods 是列表
                if not isinstance(raw_foods, list):
                    if isinstance(raw_foods, dict) and 'foods' in raw_foods:
                        raw_foods = raw_foods['foods']
                    elif isinstance(raw_foods, dict) and 'items' in raw_foods:
                        raw_foods = raw_foods['items']
                    elif isinstance(raw_foods, dict):
                        # 尝试将字典的值作为列表，如果有合适的候选
                        possible_lists = [v for v in raw_foods.values() if isinstance(v, list)]
                        if possible_lists:
                            # 选择最长的列表
                            raw_foods = max(possible_lists, key=len)
                        else:
                            # 将整个字典包装成单元素列表
                            raw_foods = [raw_foods]
                    elif hasattr(raw_foods, '__iter__') and not isinstance(raw_foods, str):
                        try:
                            raw_foods = list(raw_foods)
                        except Exception:
                            self.logger.error("无法将数据转换为列表格式")
                            return None
                    else:
                        self.logger.error("无法识别的JSON数据格式")
                        return None

                self.logger.info(f"正在处理 {len(raw_foods)} 条食物记录...")

                for food in raw_foods:
                    # 检查food是否为字典类型
                    if not isinstance(food, dict):
                        self.logger.warning(f"跳过非字典类型的记录: {type(food)}")
                        continue

                    # 根据实际数据结构构建食物对象
                    # 尝试多种可能的字段名
                    food_id = (
                        food.get('fdcId')
                    )

                    food_name = (
                        food.get('description') or
                        food.get('Description') or
                        food.get('foodDescription') or
                        food.get('name', 'Unknown Food')
                    )

                    food_description = (
                        food.get('short_description') or
                        food.get('ShortDescription') or
                        food.get('description', '') or
                        ''
                    )

                    # 处理营养素信息 - 尝试不同格式
                    nutrients = []

                    # 检查是否有营养素相关字段
                    if 'food_nutrients' in food:
                        # 格式可能是 food_nutrients 数组
                        for nutrient_data in food['food_nutrients']:
                            if isinstance(nutrient_data, dict):
                                nutrients.append({
                                    "name": nutrient_data.get('nutrient_name', nutrient_data.get('name', 'Unknown Nutrient')),
                                    "value": nutrient_data.get('amount', nutrient_data.get('value', 0)),
                                    "unit": nutrient_data.get('unit', nutrient_data.get('unit_name', 'g')),
                                    "fdc_id": food_id
                                })
                    elif 'nutrients' in food:
                        # 格式可能是 nutrients 数组
                        for nutrient_data in food['nutrients']:
                            if isinstance(nutrient_data, dict):
                                nutrients.append({
                                    "name": nutrient_data.get('name', 'Unknown Nutrient'),
                                    "value": nutrient_data.get('amount', nutrient_data.get('value', 0)),
                                    "unit": nutrient_data.get('unit', nutrient_data.get('unit_name', 'g')),
                                    "fdc_id": food_id
                                })
                    elif 'FoodNutrients' in food:
                        # 另一种可能的格式
                        for nutrient_data in food['FoodNutrients']:
                            if isinstance(nutrient_data, dict):
                                nutrients.append({
                                    "name": nutrient_data.get('Nutrient', {}).get('name', 'Unknown Nutrient') if isinstance(nutrient_data.get('Nutrient'), dict) else nutrient_data.get('Nutrient', 'Unknown Nutrient'),
                                    "value": nutrient_data.get('Amount', nutrient_data.get('amount', 0)),
                                    "unit": nutrient_data.get('Nutrient', {}).get('unit', 'g') if isinstance(nutrient_data.get('Nutrient'), dict) else 'g',
                                    "fdc_id": food_id
                                })
                    elif 'foodNutrients' in food:
                        # 小写变体
                        for nutrient_data in food['foodNutrients']:
                            if isinstance(nutrient_data, dict):
                                nutrients.append({
                                    "name": nutrient_data.get('nutrient', {}).get('name', 'Unknown Nutrient') if isinstance(nutrient_data.get('nutrient'), dict) else nutrient_data.get('nutrient', 'Unknown Nutrient'),
                                    "value": nutrient_data.get('amount', nutrient_data.get('value', 0)),
                                    "unit": nutrient_data.get('unit', 'g'),
                                    "fdc_id": food_id
                                })

                    # 构建食物对象
                    food_obj = {
                        "id": str(food_id),
                        "name": food_name,
                        "description": food_description,
                        "nutrients": nutrients
                    }
                    foods.append(food_obj)

                # 准备返回的数据结构
                result = {"usda_food_list": foods}

                self.logger.info(f"成功处理了 {len(foods)} 个食物项目的营养数据")
                return result

            except requests.exceptions.RequestException as e:
                self.logger.error(f"下载失败: {e}")
                # 尝试备用链接 - 使用2021年版本的链接
                backup_url = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_json_2021-10-28.zip"
                self.logger.info(f"尝试使用备用链接: {backup_url}")

                try:
                    response = requests.get(backup_url, stream=True)
                    response.raise_for_status()

                    zip_path = os.path.join(temp_dir, "usda_sr_legacy_json_backup.zip")

                    with open(zip_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    self.logger.info(f"已下载备用JSON数据到临时目录: {zip_path}")

                    # 解压文件
                    self.logger.info("正在解压JSON文件...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)

                    self.logger.info("解压完成")

                    # 查找解压后的JSON数据文件
                    json_file_path = None
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.lower().endswith('.json') and 'food' in file.lower() and 'json' in file.lower():
                                json_file_path = os.path.join(root, file)
                                break
                        if json_file_path:
                            break

                    if not json_file_path:
                        self.logger.error("未找到食物JSON文件（备用链接）")
                        return None

                    # 读取JSON文件
                    self.logger.info(f"正在处理食物数据文件: {json_file_path}")

                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        food_data = json.load(f)

                    # 检查数据格式 - 如果是包含多个表的结构，按相应方式处理
                    # 否则认为是简单的食物列表
                    foods = []

                    if isinstance(food_data, dict):
                        # 检查是否是包含不同表格的结构
                        if 'FoundationFoods' in food_data:
                            raw_foods = food_data['FoundationFoods']
                        elif 'SurveyFoods' in food_data:
                            raw_foods = food_data['SurveyFoods']
                        elif 'SR legacy' in food_data or 'SrLegacyFoods' in food_data:
                            raw_foods = food_data.get('SR legacy', food_data.get('SrLegacyFoods', []))
                        elif 'Foods' in food_data:
                            raw_foods = food_data['Foods']
                        elif 'food' in food_data:
                            raw_foods = food_data['food']
                        else:
                            # 假设整个对象的值是一个食物列表
                            # 遍历字典的值来查找可能的食物列表
                            raw_foods = None
                            for key, value in food_data.items():
                                if isinstance(value, list) and len(value) > 0:
                                    if isinstance(value[0], dict) and ('description' in value[0] or 'name' in value[0] or 'food_id' in value[0] or 'fdc_id' in value[0]):
                                        raw_foods = value
                                        break
                            if raw_foods is None:
                                # 如果没找到明显的食物列表，假设整个值就是要处理的数据
                                raw_foods = food_data

                    elif isinstance(food_data, list):
                        # 直接是一个食物列表
                        raw_foods = food_data
                    else:
                        self.logger.error("无法识别的JSON数据格式 - 数据既不是字典也不是列表（备用链接）")
                        return None

                    # 确保 raw_foods 是列表
                    if not isinstance(raw_foods, list):
                        if isinstance(raw_foods, dict) and 'foods' in raw_foods:
                            raw_foods = raw_foods['foods']
                        elif isinstance(raw_foods, dict) and 'items' in raw_foods:
                            raw_foods = raw_foods['items']
                        elif isinstance(raw_foods, dict):
                            # 尝试将字典的值作为列表，如果有合适的候选
                            possible_lists = [v for v in raw_foods.values() if isinstance(v, list)]
                            if possible_lists:
                                # 选择最长的列表
                                raw_foods = max(possible_lists, key=len)
                            else:
                                # 将整个字典包装成单元素列表
                                raw_foods = [raw_foods]
                        elif hasattr(raw_foods, '__iter__') and not isinstance(raw_foods, str):
                            try:
                                raw_foods = list(raw_foods)
                            except Exception:
                                self.logger.error("无法将数据转换为列表格式（备用链接）")
                                return None
                        else:
                            self.logger.error("无法识别的JSON数据格式（备用链接）")
                            return None

                    self.logger.info(f"正在处理 {len(raw_foods)} 条食物记录...")

                    for food in raw_foods:
                        # 检查food是否为字典类型
                        if not isinstance(food, dict):
                            self.logger.warning(f"跳过非字典类型的记录: {type(food)}")
                            continue

                        # 根据实际数据结构构建食物对象
                        # 尝试多种可能的字段名
                        food_id = (
                            food.get('food_id') or
                            food.get('fdc_id') or
                            food.get('id') or
                            str(hash(str(food)))  # 最后手段，用哈希值
                        )

                        food_name = (
                            food.get('description') or
                            food.get('Description') or
                            food.get('foodDescription') or
                            food.get('name', 'Unknown Food')
                        )

                        food_description = (
                            food.get('short_description') or
                            food.get('ShortDescription') or
                            food.get('description', '') or
                            ''
                        )

                        # 处理营养素信息 - 尝试不同格式
                        nutrients = []

                        # 检查是否有营养素相关字段
                        if 'food_nutrients' in food:
                            # 格式可能是 food_nutrients 数组
                            for nutrient_data in food['food_nutrients']:
                                if isinstance(nutrient_data, dict):
                                    nutrients.append({
                                        "name": nutrient_data.get('nutrient_name', nutrient_data.get('name', 'Unknown Nutrient')),
                                        "value": nutrient_data.get('amount', nutrient_data.get('value', 0)),
                                        "unit": nutrient_data.get('unit', nutrient_data.get('unit_name', 'g')),
                                        "fdc_id": food_id
                                    })
                        elif 'nutrients' in food:
                            # 格式可能是 nutrients 数组
                            for nutrient_data in food['nutrients']:
                                if isinstance(nutrient_data, dict):
                                    nutrients.append({
                                        "name": nutrient_data.get('name', 'Unknown Nutrient'),
                                        "value": nutrient_data.get('amount', nutrient_data.get('value', 0)),
                                        "unit": nutrient_data.get('unit', nutrient_data.get('unit_name', 'g')),
                                        "fdc_id": food_id
                                    })
                        elif 'FoodNutrients' in food:
                            # 另一种可能的格式
                            for nutrient_data in food['FoodNutrients']:
                                if isinstance(nutrient_data, dict):
                                    nutrients.append({
                                        "name": nutrient_data.get('Nutrient', {}).get('name', 'Unknown Nutrient') if isinstance(nutrient_data.get('Nutrient'), dict) else nutrient_data.get('Nutrient', 'Unknown Nutrient'),
                                        "value": nutrient_data.get('Amount', nutrient_data.get('amount', 0)),
                                        "unit": nutrient_data.get('Nutrient', {}).get('unit', 'g') if isinstance(nutrient_data.get('Nutrient'), dict) else 'g',
                                        "fdc_id": food_id
                                    })
                        elif 'foodNutrients' in food:
                            # 小写变体
                            for nutrient_data in food['foodNutrients']:
                                if isinstance(nutrient_data, dict):
                                    nutrients.append({
                                        "name": nutrient_data.get('nutrient', {}).get('name', 'Unknown Nutrient') if isinstance(nutrient_data.get('nutrient'), dict) else nutrient_data.get('nutrient', 'Unknown Nutrient'),
                                        "value": nutrient_data.get('amount', nutrient_data.get('value', 0)),
                                        "unit": nutrient_data.get('unit', 'g'),
                                        "fdc_id": food_id
                                    })

                        # 构建食物对象
                        food_obj = {
                            "id": str(food_id),
                            "name": food_name,
                            "description": food_description,
                            "nutrients": nutrients
                        }
                        foods.append(food_obj)

                    # 准备返回的数据结构
                    result = {"usda_food_list": foods}

                    self.logger.info(f"成功处理了 {len(foods)} 个食物项目的营养数据（使用备用JSON数据）")
                    return result

                except Exception as backup_e:
                    self.logger.error(f"备用JSON数据下载也失败: {backup_e}")
                    # 最后的备用方案：尝试CSV数据
                    csv_url = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2021-10-28.zip"
                    self.logger.info(f"最后尝试使用CSV数据: {csv_url}")

                    try:
                        response = requests.get(csv_url, stream=True)
                        response.raise_for_status()

                        zip_path = os.path.join(temp_dir, "usda_sr_legacy_csv.zip")

                        with open(zip_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)

                        self.logger.info(f"已下载CSV数据到临时目录: {zip_path}")

                        # 解压文件
                        self.logger.info("正在解压CSV文件...")
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)

                        self.logger.info("解压完成")

                        # 查找并读取主要数据文件
                        import pandas as pd
                        data_files = []
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                if file.endswith('.csv') and 'food' in file.lower():
                                    data_files.append(os.path.join(root, file))

                        if not data_files:
                            self.logger.error("未找到解压后的数据文件")
                            return None

                        # 读取CSV文件
                        food_csv_path = data_files[0]  # 使用第一个找到的食物CSV文件
                        self.logger.info(f"正在处理CSV文件: {food_csv_path}")

                        df = pd.read_csv(food_csv_path)

                        # 处理成我们需要的格式
                        foods = []

                        self.logger.info(f"正在处理 {len(df)} 条食物记录...")

                        for _, row in df.iterrows():
                            # 构建食物对象
                            food_obj = {
                                "id": str(row.get('fdc_id', row.get('food_id', ''))),
                                "name": row.get('description', ''),
                                "description": row.get('short_description', ''),
                                "nutrients": []
                            }
                            foods.append(food_obj)

                        # 准备返回的数据结构
                        result = {"usda_food_list": foods}

                        self.logger.info(f"成功处理了 {len(foods)} 个食物项目的营养数据（使用CSV数据）")
                        return result
                    except Exception as csv_e:
                        self.logger.error(f"所有数据源均失败: {csv_e}")
                        return None

            except ImportError:
                self.logger.error("缺少必要的库 (requests, zipfile)，请安装: pip install requests")
                return None
            except Exception as e:
                self.logger.error(f"处理USDA数据时出现错误: {e}")
                return None

    def preprocess_usda_data(self, usda_data: Dict) -> List[Dict]:
        """
        预处理USDA数据为便于匹配的格式
        """
        self.logger.info("正在预处理USDA数据...")

        processed_data = []
        for food in usda_data.get("usda_food_list", []):
            processed_item = {
                "id": food["id"],
                "name": food["name"],
                "description": food.get("description", ""),
                "nutrients": {}
            }

            # 将营养素数据整理为字典格式
            for nutrient in food.get("nutrients", []):
                # 简化营养素名称作为键
                nutrient_key = self.simplify_nutrient_name(nutrient["name"])
                if nutrient_key:
                    processed_item["nutrients"][nutrient_key] = {
                        "value": nutrient["value"],
                        "unit": nutrient["unit"],
                        "fdc_id": nutrient.get("fdc_id", "")
                    }

            processed_data.append(processed_item)

        return processed_data

    def simplify_nutrient_name(self, nutrient_name: str) -> str:
        """
        简化营养素名称以便匹配
        """
        nutrient_mapping = {
            "Energy": "energy_kcal",
            "Energy (Atwater General Factors)": "energy_kcal",
            "Protein": "protein",
            "Total lipid (fat)": "fat",
            "Carbohydrate, by difference": "carbohydrate",
            "Fiber, total dietary": "fiber",
            "Calcium, Ca": "calcium",
            "Iron, Fe": "iron",
            "Sodium, Na": "sodium",
            "Potassium, K": "potassium",
            "Magnesium, Mg": "magnesium",
            "Phosphorus, P": "phosphorus",
            "Zinc, Zn": "zinc",
            "Copper, Cu": "copper",
            "Manganese, Mn": "manganese",
            "Selenium, Se": "selenium",
            "Cholesterol": "cholesterol",
            "Vitamin A, RAE": "vitamin_a_rae",
            "Vitamin C, total ascorbic acid": "vitamin_c",
            "Vitamin D (D2 + D3), micrograms": "vitamin_d",
            "Vitamin D (D2 + D3)": "vitamin_d",
            "Vitamin E (alpha-tocopherol)": "vitamin_e",
            "Vitamin K (phylloquinone)": "vitamin_k",
            "Folate, total": "folate",
            "Niacin": "niacin",
            "Riboflavin": "vitamin_b2",
            "Thiamin": "vitamin_b1",
            "Vitamin B-12": "vitamin_b12",
            "Vitamin B-6": "vitamin_b6",
            "Pantothenic acid": "pantothenic_acid",
            "Biotin": "biotin",
            "Fatty acids, total saturated": "saturated_fat",
            "Fatty acids, total monounsaturated": "monounsaturated_fat",
            "Fatty acids, total polyunsaturated": "polyunsaturated_fat",
            "Sugars, total including NLEA": "sugar"
        }

        return nutrient_mapping.get(nutrient_name, nutrient_name.lower().replace(" ", "_").replace(",", "").replace("-", "_"))

    def load_ingredients(self) -> List[Dict]:
        """
        加载当前食材数据
        """
        self.logger.info("正在加载当前食材数据...")

        ingredients_path = os.path.join(self.output_dir, "ingredients.json")
        if not os.path.exists(ingredients_path):
            self.logger.error(f"食材文件不存在: {ingredients_path}")
            return []

        try:
            with open(ingredients_path, 'r', encoding='utf-8') as f:
                ingredients = json.load(f)
            self.logger.info(f"已加载 {len(ingredients)} 个食材")
            return ingredients
        except Exception as e:
            self.logger.error(f"加载食材文件失败: {str(e)}")
            return []

    def match_ingredients_with_usda_via_skill(self, ingredients: List[Dict], usda_data: List[Dict]) -> List[Dict]:
        """
        必须且只能通过调用 Claude Code 的 match-ingredients 技能来匹配食材与USDA数据，不得使用其他任何方式匹配
        """
        self.logger.info("正在通过Claude Code match-ingredients技能匹配食材与USDA数据...")

        # 检查是否在Claude Code环境中运行
        if 'CLAUDECODE' in os.environ:
            self.logger.error("检测到在Claude Code环境中运行，无法启动新的Claude Code会话进行食材匹配。")
            self.logger.error("请在普通终端环境中运行此脚本以使用Claude Code技能进行匹配。")
            return []

        # 创建临时目录存储中间文件
        with tempfile.TemporaryDirectory() as temp_dir:
            # 保存食材数据到临时文件
            temp_ingredients_path = os.path.join(temp_dir, "temp_ingredients.json")
            with open(temp_ingredients_path, 'w', encoding='utf-8') as f:
                json.dump(ingredients, f, ensure_ascii=False, indent=2)

            # 为USDA数据创建只有ID和名称的格式
            usda_names_only = []
            for item in usda_data:
                usda_names_only.append({
                    "id": item["id"],
                    "name": item["name"]
                })

            # 保存USDA数据到临时文件
            temp_usda_path = os.path.join(temp_dir, "temp_usda_names.json")
            with open(temp_usda_path, 'w', encoding='utf-8') as f:
                json.dump(usda_names_only, f, ensure_ascii=False, indent=2)

            # 定义输出文件路径
            output_file_path = os.path.join(temp_dir, "matched_ingredients.json")

            # 调用Claude Code的match-ingredients技能，指定输出文件路径
            try:
                # 调用技能并指定输出文件路径
                # log cmdline
                self.logger.info(f"正在调用Claude Code的match-ingredients技能...")
                self.logger.info(f"claude -p /match-ingredients `{temp_ingredients_path}` `{temp_usda_path}` `{output_file_path}`")
                # 调用Claude Code的match-ingredients技能，指定输出文件路径
                # 注意：Claude Code会使用技能定义中指定的逻辑来处理，确保遵循语义匹配规则
                result = subprocess.run([
                    'claude', '-p', f'/match-ingredients `{temp_ingredients_path}` `{temp_usda_path}` `{output_file_path}`'
                ], capture_output=True, text=True, timeout=3600)  # 增加超时时间

                if result.returncode != 0:
                    self.logger.error(f"match-ingredients技能执行失败: {result.stderr}")
                    return []

                # 检查输出文件是否存在
                if not os.path.exists(output_file_path):
                    # 如果输出文件不存在，可能是因为使用了默认的输出路径
                    default_output_path = os.path.join(temp_dir, "..", "out", "matched_ingredients.json")
                    if os.path.exists(default_output_path):
                        output_file_path = default_output_path
                    else:
                        # 检查当前项目目录的out目录
                        proj_default_path = os.path.join(self.output_dir, "matched_ingredients.json")
                        if os.path.exists(proj_default_path):
                            output_file_path = proj_default_path
                        else:
                            self.logger.error(f"match-ingredients技能未生成输出文件: {output_file_path}, {default_output_path}, {proj_default_path}")
                            return []

                # 读取生成的输出文件
                with open(output_file_path, 'r', encoding='utf-8') as f:
                    matched_data = json.load(f)

                # 验证输出格式是否正确
                if not isinstance(matched_data, list):
                    self.logger.error(f"输出文件格式不正确，期望列表格式，得到 {type(matched_data)}")
                    return []

                # 验证每项是否包含必需的字段
                for item in matched_data:
                    if not isinstance(item, dict):
                        self.logger.error(f"输出文件中包含非字典项: {item}")
                        return []
                    if 'ingredient_name' not in item:
                        self.logger.error(f"输出项目缺少ingredient_name字段: {item}")
                        return []
                    # 注意：根据技能规范，如果找不到匹配项，usda_id应该是null而不是缺失
                    if 'usda_id' not in item:
                        self.logger.error(f"输出项目缺少usda_id字段: {item}")
                        return []
                    if 'usda_name' not in item:
                        self.logger.error(f"输出项目缺少usda_name字段: {item}")
                        return []

                # 保存匹配结果到out目录
                nutrition_map_path = os.path.join(self.output_dir, "nutrition_map.json")
                os.makedirs(self.output_dir, exist_ok=True)
                with open(nutrition_map_path, 'w', encoding='utf-8') as f:
                    json.dump(matched_data, f, ensure_ascii=False, indent=2)

                self.logger.info(f"匹配结果已保存到: {nutrition_map_path}")
                self.logger.info(f"成功匹配了 {len(matched_data)} 个食材")
                return matched_data

            except subprocess.TimeoutExpired:
                self.logger.error("match-ingredients技能执行超时")
                return []
            except FileNotFoundError:
                self.logger.error("未找到claude命令，请确保Claude Code已安装并配置")
                return []
            except json.JSONDecodeError as e:
                self.logger.error(f"解析输出文件时出现JSON错误: {str(e)}")
                return []
            except Exception as e:
                self.logger.error(f"调用match-ingredients技能时出错: {str(e)}")
                return []

    def calculate_nrv_values(self, nutrients: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        计算营养素的NRV/DV值
        优先使用中国GB标准，如无则使用美国FDA标准
        """
        calculated_nutrients = {}

        for nutrient_key, nutrient_info in nutrients.items():
            value = nutrient_info.get("value", 0)
            unit = nutrient_info.get("unit", "")

            # 首先尝试使用中国标准
            chinese_nrv = self.chinese_nrv_values.get(nutrient_key)
            if chinese_nrv:
                # 检查单位是否匹配
                if chinese_nrv["unit"] == unit:
                    nrp_pct = round((value / chinese_nrv["value"]) * 100, 2)
                    calculated_nutrients[nutrient_key] = {
                        "value": value,
                        "unit": unit,
                        "nrp_pct": nrp_pct,
                        "standard": "中国GB标准"
                    }
                else:
                    # 单位不匹配，尝试进行单位转换（这里简化处理）
                    calculated_nutrients[nutrient_key] = {
                        "value": value,
                        "unit": unit,
                        "nrp_pct": 0,  # 无法计算百分比，因为单位不匹配
                        "standard": "中国GB标准",
                        "note": "单位不匹配，无法计算百分比"
                    }
            else:
                # 尝试使用美国标准
                usa_dv = self.usa_dv_values.get(nutrient_key)
                if usa_dv:
                    if usa_dv["unit"] == unit:
                        nrp_pct = round((value / usa_dv["value"]) * 100, 2)
                        calculated_nutrients[nutrient_key] = {
                            "value": value,
                            "unit": unit,
                            "nrp_pct": nrp_pct,
                            "standard": "美国FDA标准"
                        }
                    else:
                        # 单位不匹配
                        calculated_nutrients[nutrient_key] = {
                            "value": value,
                            "unit": unit,
                            "nrp_pct": 0,
                            "standard": "美国FDA标准",
                            "note": "单位不匹配，无法计算百分比"
                        }
                else:
                    # 两种标准都没有该营养素，但仍保存原始数据
                    calculated_nutrients[nutrient_key] = {
                        "value": value,
                        "unit": unit,
                        "nrp_pct": 0,
                        "standard": "无标准",
                        "note": "该营养素无对应的NRV/DV标准值"
                    }

        return calculated_nutrients

    def generate_nutrition_data(self) -> bool:
        """
        生成营养信息数据的主要方法
        """
        self.logger.info("开始生成营养信息数据...")

        # 步骤1: 下载USDA营养数据（必须成功，否则终止）
        usda_data_full = self.download_usda_data()
        if not usda_data_full:
            self.logger.error("无法获取USDA SR营养数据，程序终止")
            return False

        # 步骤2: 预处理USDA数据
        usda_processed = self.preprocess_usda_data(usda_data_full)

        # 步骤3: 加载当前食材
        ingredients = self.load_ingredients()
        if not ingredients:
            self.logger.error("无法加载食材数据，程序终止")
            return False

        # 步骤4: 通过Claude Code技能匹配食材与USDA数据（这是唯一允许的方式）
        matched_ingredients = self.match_ingredients_with_usda_via_skill(ingredients, usda_processed)
        if not matched_ingredients:
            self.logger.error("食材匹配失败，程序终止")
            return False

        # 步骤5: 生成最终的营养信息
        nutrition_data = []

        for matched_item in matched_ingredients:
            usda_id = matched_item["usda_id"]

            # 查找对应的USDA营养数据
            usda_item = None
            for item in usda_processed:
                if item["id"] == usda_id:
                    usda_item = item
                    break

            if usda_item:
                # 计算NRV/DV值
                calculated_nutrients = self.calculate_nrv_values(usda_item["nutrients"])

                nutrition_entry = {
                    "usda_id": usda_item["id"],
                    "ingredient_name": matched_item["ingredient_name"],
                    "usda_name": usda_item["name"],
                    "nutrients": calculated_nutrients
                }
                nutrition_data.append(nutrition_entry)

        # 步骤6: 保存营养信息结果到out目录
        nutrition_output_path = os.path.join(self.output_dir, "nutritions.json")
        os.makedirs(self.output_dir, exist_ok=True)

        with open(nutrition_output_path, 'w', encoding='utf-8') as f:
            json.dump(nutrition_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"营养信息数据已生成: {nutrition_output_path}")
        self.logger.info(f"总共处理了 {len(nutrition_data)} 个食材的营养信息")

        return True

    def run(self):
        """
        运行营养信息生成流程
        """
        try:
            success = self.generate_nutrition_data()
            if success:
                self.logger.info("营养信息生成完成！")
                return 0
            else:
                self.logger.error("营养信息生成失败！")
                return 1
        except Exception as e:
            self.logger.error(f"运行过程中发生错误: {str(e)}")
            return 1


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='生成营养信息数据')
    parser.add_argument('--output-dir', default='out', help='输出目录')
    args = parser.parse_args()

    processor = NutritionDataProcessor(output_dir=args.output_dir)
    return processor.run()


if __name__ == "__main__":
    sys.exit(main())