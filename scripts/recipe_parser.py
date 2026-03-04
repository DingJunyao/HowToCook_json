"""
菜谱解析自动化工具包

该包提供了完整的功能来解析 HowToCook 项目中的菜谱，
将其转换为系统可用的 JSON 格式，并标准化食材数据。
"""

import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
import argparse
import sys
from typing import List, Dict, Any, Optional
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RecipeParserConfig:
    """配置类，集中管理所有硬编码的配置项"""
    
    # 仓库配置
    REPO_URL = "https://github.com/Anduin2017/HowToCook.git"
    DISHES_DIR = "dishes"
    
    # 超时配置（秒）
    CLAUDE_COMMAND_TIMEOUT = 1800  # 30 minutes
    GIT_CLONE_TIMEOUT = 300  # 5 minutes
    GIT_LFS_PULL_TIMEOUT = 600  # 10 minutes
    GIT_LFS_CHECK_TIMEOUT = 30  # 30 seconds
    
    # 重试配置
    MAX_RETRIES = 3
    
    # 图片配置 - 默认扩展名仅在无法从原文件获取时使用
    DEFAULT_IMAGE_EXTENSION = ".jpg"  # 更通用的图片格式
    SUPPORTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
    
    # 输出配置
    DEFAULT_OUTPUT_DIR = "out"
    INGREDIENTS_RAW_FILE = "ingredients_raw.json"
    INGREDIENTS_FILE = "ingredients.json"
    
    # 解析配置
    REQUIRED_RECIPE_FIELDS = ['name', 'source_file', 'category', 'difficulty', 'servings', 'ingredients', 'steps']
    REQUIRED_INGREDIENT_FIELDS = ['ingredient_name', 'unit']
    
    # 跳过的外部 URL 前缀
    EXTERNAL_URL_PREFIXES = ('http://', 'https://', 'data:')


def get_json_schema(file_path: str) -> str:
    """
    Get JSON schema from a JSON file

    Args:
        file_path: Path to the JSON file

    Returns:
        JSON schema or None if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
            # compress json
            data = json.dumps(json.loads(data), ensure_ascii=False)
        return data
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}")


def run_claude_command(prompt: str, cwd: str = None, input_text: str = None) -> Optional[str]:
    """
    Execute claude command with given prompt

    Args:
        prompt: The prompt to send to Claude
        cwd: Working directory for the command
        input_text: Optional text to pass via stdin pipe

    Returns:
        The output from Claude or None if error
    """
    try:
        logger.info(f"Executing Claude command...")
        # Build command arguments
        cmd_args = ['claude', '-p', f'"{prompt}"']
        
        # Log the command (mask sensitive parts if needed)
        logger.info("args: " + ' '.join(cmd_args))
        # logger.info("input_text: " + input_text)
        
        # Run command with optional stdin input
        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            input=input_text,  # Pass content via stdin pipe
            cwd=cwd or os.getcwd(),
            timeout=RecipeParserConfig.CLAUDE_COMMAND_TIMEOUT
        )

        if result.returncode != 0:
            logger.error(f"Error running claude command: {result.stderr}")
            return None

        logger.debug(f"Claude command output: {result.stdout[:200]}...")
        return result.stdout.strip()
    except FileNotFoundError:
        logger.error("Error: 'claude' command not found. Please ensure Claude Code is installed and in PATH.")
        return None
    except subprocess.TimeoutExpired:
        logger.error("Error: Claude command timed out after 30 minutes.")
        return None
    except Exception as e:
        logger.error(f"Error running claude command: {str(e)}")
        return None


def check_git_lfs_installed() -> bool:
    """
    Check if Git LFS is installed on the system
    
    Returns:
        True if Git LFS is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ['git', 'lfs', 'version'],
            capture_output=True,
            text=True,
            timeout=RecipeParserConfig.GIT_LFS_CHECK_TIMEOUT
        )
        if result.returncode == 0:
            logger.info(f"Git LFS is installed: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        logger.error(f"Error checking Git LFS: {str(e)}")
        return False


def print_git_lfs_install_instructions():
    """
    Print installation instructions for Git LFS on different systems
    """
    print("\n" + "="*60)
    print("Git LFS is not installed. Please install it using one of the methods below:")
    print("="*60)
    print("\n【macOS】")
    print("  Using Homebrew:")
    print("    brew install git-lfs")
    print("    git lfs install")
    print("\n  Or download from: https://git-lfs.com/")
    print("\n【Linux (Debian/Ubuntu)】")
    print("  Using apt:")
    print("    curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash")
    print("    sudo apt-get install git-lfs")
    print("    git lfs install")
    print("\n【Linux (RHEL/CentOS/Fedora)】")
    print("  Using yum/dnf:")
    print("    curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | sudo bash")
    print("    sudo yum install git-lfs")
    print("    git lfs install")
    print("\n【Windows】")
    print("  Option 1 - Using winget:")
    print("    winget install --id GitHub.GitLFS")
    print("  Option 2 - Using Chocolatey:")
    print("    choco install git-lfs")
    print("  Option 3 - Download installer from: https://git-lfs.com/")
    print("\n【After Installation】")
    print("  Run: git lfs install")
    print("="*60 + "\n")


def clone_howtocook_repo(target_dir: str) -> bool:
    """
    Clone the HowToCook repository

    Args:
        target_dir: Directory to clone the repository to

    Returns:
        True if successful, False otherwise
    """
    # Check if Git LFS is installed
    if not check_git_lfs_installed():
        logger.error("Git LFS is not installed. Cannot proceed with repository cloning.")
        print_git_lfs_install_instructions()
        return False
    
    try:
        logger.info(f"Cloning HowToCook repository to {target_dir}")
        repo_url = RecipeParserConfig.REPO_URL

        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(target_dir) if os.path.dirname(target_dir) else target_dir, exist_ok=True)

        result = subprocess.run(
            ['git', 'clone', '--depth', '1', repo_url, target_dir],
            capture_output=True,
            text=True,
            timeout=RecipeParserConfig.GIT_CLONE_TIMEOUT
        )

        if result.returncode != 0:
            logger.error(f"Error cloning repository: {result.stderr}")
            return False

        logger.info(f"Successfully cloned HowToCook repository to {target_dir}")
        
        # Pull Git LFS files to get actual image content instead of pointer files
        logger.info("Pulling Git LFS files...")
        lfs_result = subprocess.run(
            ['git', 'lfs', 'pull'],
            cwd=target_dir,
            capture_output=True,
            text=True,
            timeout=RecipeParserConfig.GIT_LFS_PULL_TIMEOUT
        )
        
        if lfs_result.returncode != 0:
            logger.warning(f"Git LFS pull failed: {lfs_result.stderr}")
            logger.warning("Images may be pointer files instead of actual content")
        else:
            logger.info("Successfully pulled Git LFS files")
        
        return True
    except subprocess.TimeoutExpired:
        logger.error("Error: Git clone timed out after 10 minutes.")
        return False
    except Exception as e:
        logger.error(f"Error cloning repository: {str(e)}")
        return False


def find_markdown_files(howtocook_path: str) -> List[str]:
    """
    Find all markdown files in the dishes subdirectory of HowToCook repository

    Args:
        howtocook_path: Path to the HowToCook repository

    Returns:
        List of markdown file paths
    """
    logger.info(f"Searching for markdown files in dishes directory: {howtocook_path}/{RecipeParserConfig.DISHES_DIR}")
    md_files = []

    dishes_path = os.path.join(howtocook_path, RecipeParserConfig.DISHES_DIR)
    if not os.path.exists(dishes_path):
        logger.warning(f"Dishes directory not found at {dishes_path}")
        # As fallback, search in the entire repo but warn the user
        logger.info("Searching in entire repository as fallback...")
        for root, dirs, files in os.walk(howtocook_path):
            # Skip common non-dish directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.github']]
            for file in files:
                if file.lower().endswith('.md') and not file.startswith('.'):
                    full_path = os.path.join(root, file)
                    # Only include files that are under dishes directory
                    if RecipeParserConfig.DISHES_DIR in full_path.replace(howtocook_path, '').split(os.sep):
                        md_files.append(full_path)
    else:
        for root, dirs, files in os.walk(dishes_path):
            # Skip common non-dish directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.github']]
            for file in files:
                if file.lower().endswith('.md') and not file.startswith('.'):
                    md_files.append(os.path.join(root, file))

    logger.info(f"Found {len(md_files)} markdown files in dishes directory")
    return md_files


def extract_images_from_markdown(file_path: str) -> List[str]:
    """
    Extract image paths from a markdown file
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        List of image paths found in the markdown file
    """
    logger.info(f"Extracting images from markdown: {file_path}")
    image_paths = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Match markdown image syntax: ![alt](path)
        image_pattern = r'!\[.*?\]\((.*?)\)'
        matches = re.findall(image_pattern, content)
        
        for match in matches:
            # Skip external URLs (http, https) and data URLs
            if any(match.startswith(prefix) for prefix in RecipeParserConfig.EXTERNAL_URL_PREFIXES):
                logger.debug(f"Skipping external/data URL: {match}")
                continue
            image_paths.append(match)
        
        logger.info(f"Found {len(image_paths)} images in {file_path}")
        return image_paths
    except Exception as e:
        logger.error(f"Error extracting images from {file_path}: {str(e)}")
        return []


def copy_or_download_images(image_paths: List[str], howtocook_path: str, recipe_name: str, images_dir: str, md_file_dir: str) -> List[str]:
    """
    Copy or download images to the images directory
    
    Args:
        image_paths: List of image paths from markdown file
        howtocook_path: Path to the HowToCook repository
        recipe_name: Name of the recipe (for naming image files)
        images_dir: Directory to save images
        md_file_dir: Directory containing the markdown file (for resolving relative paths)
        
    Returns:
        List of saved image paths (relative to images_dir)
    """
    logger.info(f"Copying/downloading {len(image_paths)} images for recipe: {recipe_name}")
    saved_images = []
    
    # Create images directory if it doesn't exist
    os.makedirs(images_dir, exist_ok=True)
    
    for i, image_path in enumerate(image_paths):
        try:
            # Resolve relative path based on markdown file location
            if not os.path.isabs(image_path):
                # Image path is relative to the markdown file location
                # Convert to absolute path based on md file's directory
                potential_path = os.path.normpath(os.path.join(md_file_dir, image_path))
            else:
                potential_path = image_path
            
            # Check if the image file exists in the repository
            if os.path.exists(potential_path):
                # Check if file is a Git LFS pointer file (not actual image content)
                is_lfs_pointer = False
                try:
                    with open(potential_path, 'rb') as f:
                        first_bytes = f.read(100)
                        # Check for LFS pointer signature
                        if first_bytes.startswith(b'version https://git-lfs.github.com/spec/v1'):
                            is_lfs_pointer = True
                            logger.warning(f"Image file is a Git LFS pointer (not actual content): {potential_path}")
                except Exception:
                    pass
                
                # Skip LFS pointer files
                if is_lfs_pointer:
                    logger.warning(f"Skipping LFS pointer file: {image_path}")
                    continue
                
                # Get extension from original image path, preserve original extension
                original_ext = os.path.splitext(image_path)[1].lower()
                
                # Validate extension is a supported image format
                if original_ext and original_ext in RecipeParserConfig.SUPPORTED_IMAGE_EXTENSIONS:
                    ext = original_ext
                else:
                    # Try to detect extension from actual file if original path has no valid extension
                    ext = os.path.splitext(potential_path)[1].lower()
                    if not ext or ext not in RecipeParserConfig.SUPPORTED_IMAGE_EXTENSIONS:
                        # Fallback to default extension only if no valid extension found
                        ext = RecipeParserConfig.DEFAULT_IMAGE_EXTENSION
                        logger.warning(f"Could not determine image extension for {image_path}, using default: {ext}")
                
                new_filename = f"{recipe_name}_{i}{ext}"
                dest_path = os.path.join(images_dir, new_filename)
                
                shutil.copy2(potential_path, dest_path)
                saved_images.append(f"images/{new_filename}")
                logger.info(f"Copied image: {image_path} -> {dest_path} (extension: {ext})")
            else:
                logger.warning(f"Image file not found: {potential_path}")
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
    
    logger.info(f"Successfully saved {len(saved_images)} images for {recipe_name}")
    return saved_images


def add_images_to_recipes(output_dir: str, howtocook_path: str, project_root: str) -> int:
    """
    Add images to parsed recipe JSON files
    
    Args:
        output_dir: Directory containing parsed recipe JSON files
        howtocook_path: Path to the HowToCook repository
        project_root: Project root directory
        
    Returns:
        0 if successful, 1 if error
    """
    logger.info("Step: Adding images to recipes...")
    
    images_dir = os.path.join(output_dir, 'images')
    updated_count = 0
    
    if not os.path.exists(output_dir):
        logger.error(f"Output directory does not exist: {output_dir}")
        return 1
    
    # Find all JSON files in output directory
    for file_name in os.listdir(output_dir):
        if file_name.endswith('.json') and file_name != RecipeParserConfig.INGREDIENTS_FILE:
            json_path = os.path.join(output_dir, file_name)
            recipe_name = os.path.splitext(file_name)[0]
            
            try:
                # Load existing JSON data
                with open(json_path, 'r', encoding='utf-8') as f:
                    recipe_data = json.load(f)
                
                # Get source_file to find corresponding markdown file
                source_file = recipe_data.get('source_file', '')
                if not source_file:
                    logger.warning(f"No source_file in {json_path}, skipping...")
                    continue
                
                # Extract path after 'dishes/' to ensure stable path reference
                # source_file might be like "dishes/xxx/xxx.md" or contain unstable prefixes
                dishes_index = source_file.find(f"{RecipeParserConfig.DISHES_DIR}/")
                if dishes_index == -1:
                    logger.warning(f"Cannot find '{RecipeParserConfig.DISHES_DIR}/' in source_file: {source_file}")
                    continue
                
                # Only keep the part starting from 'dishes/'
                relative_dishes_path = source_file[dishes_index:]
                
                # Find the markdown file in HowToCook repo
                md_file_path = os.path.join(howtocook_path, relative_dishes_path)
                if not os.path.exists(md_file_path):
                    logger.warning(f"Markdown file not found: {md_file_path}")
                    continue
                
                # Get the directory containing the markdown file (for resolving relative image paths)
                md_file_dir = os.path.dirname(md_file_path)
                
                # Extract images from markdown
                image_paths = extract_images_from_markdown(md_file_path)
                
                if image_paths:
                    # Copy/download images (pass md_file_dir for resolving relative paths)
                    saved_images = copy_or_download_images(
                        image_paths, howtocook_path, recipe_name, images_dir, md_file_dir
                    )
                    
                    # Update JSON with image paths
                    recipe_data['images'] = saved_images
                    save_to_json(recipe_data, json_path)
                    updated_count += 1
                    logger.info(f"Updated {json_path} with {len(saved_images)} images")
                else:
                    # No images found, set empty list
                    recipe_data['images'] = []
                    save_to_json(recipe_data, json_path)
                    logger.info(f"No images found for {json_path}")
                    
            except Exception as e:
                logger.error(f"Error processing {json_path}: {str(e)}")
    
    logger.info(f"Updated {updated_count} recipe files with images")
    return 0


def parse_single_recipe(file_path: str, project_root: str, output_json_path: str = None, howtocook_path: str = None) -> bool:
    """
    Parse a single recipe file using the claude skill

    Args:
        file_path: Path to the recipe markdown file
        project_root: Project root directory
        output_json_path: Optional path to save the parsed JSON file

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Parsing recipe: {file_path}")

    # Read the markdown file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return False

    # Prepare prompt for claude
    relative_path = os.path.relpath(file_path, os.path.join(project_root, RecipeParserConfig.DISHES_DIR))
    prompt = f'/parse-single-receipe `{output_json_path}`'
    
    # Retry logic with max 3 attempts
    max_retries = RecipeParserConfig.MAX_RETRIES
    for attempt in range(1, max_retries + 1):
        logger.info(f"Attempt {attempt}/{max_retries} for recipe: {file_path}")
        
        # Call claude to parse the recipe, pass file content via stdin pipe
        result = run_claude_command(prompt, project_root, input_text=content)
        if not result:
            logger.warning(f"Attempt {attempt} failed: Claude command returned no result")
            if attempt < max_retries:
                # Delete invalid JSON file if exists before retry
                if output_json_path and os.path.exists(output_json_path):
                    try:
                        os.remove(output_json_path)
                        logger.info(f"Deleted invalid JSON file: {output_json_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {output_json_path}: {str(e)}")
                continue

        # 验证目标 JSON 文件是否符合要求
        if output_json_path and os.path.exists(output_json_path):
            try:
                with open(output_json_path, 'r', encoding='utf-8') as f:
                    recipe_data = json.load(f)
                
                # Ensure the source_file field is set correctly
                recipe_data['source_file'] = relative_path

                # Validate required fields exist
                required_fields = RecipeParserConfig.REQUIRED_RECIPE_FIELDS
                for field in required_fields:
                    if field not in recipe_data:
                        logger.warning(f"Attempt {attempt}: Missing required field '{field}' in parsed recipe for {file_path}")
                        if attempt < max_retries:
                            # Delete invalid JSON file if exists before retry
                            try:
                                os.remove(output_json_path)
                                logger.info(f"Deleted invalid JSON file: {output_json_path}")
                            except Exception as e:
                                logger.warning(f"Failed to delete {output_json_path}: {str(e)}")
                            break
                else:
                    # All required fields present
                    # Ensure ingredients and steps are not empty
                    if not recipe_data.get('ingredients') or not recipe_data.get('steps'):
                        logger.warning(f"Attempt {attempt}: Recipe {file_path} has no ingredients or steps")
                        if attempt < max_retries:
                            # Delete invalid JSON file if exists before retry
                            try:
                                os.remove(output_json_path)
                                logger.info(f"Deleted invalid JSON file: {output_json_path}")
                            except Exception as e:
                                logger.warning(f"Failed to delete {output_json_path}: {str(e)}")
                            continue
                    else:
                        # Validation passed - save updated data with source_file
                        save_to_json(recipe_data, output_json_path)
                        
                        # Add images if howtocook_path is provided
                        if howtocook_path and output_json_path:
                            recipe_name = os.path.splitext(os.path.basename(output_json_path))[0]
                            images_dir = os.path.join(os.path.dirname(output_json_path), 'images')
                            image_paths = extract_images_from_markdown(file_path)
                            if image_paths:
                                # Get the directory containing the markdown file
                                md_file_dir = os.path.dirname(file_path)
                                saved_images = copy_or_download_images(
                                    image_paths, howtocook_path, recipe_name, images_dir, md_file_dir
                                )
                                recipe_data['images'] = saved_images
                                save_to_json(recipe_data, output_json_path)
                            else:
                                recipe_data['images'] = []
                                save_to_json(recipe_data, output_json_path)
                        
                        logger.info(f"Successfully parsed and verified recipe: {recipe_data['name']}")
                        return True

            except json.JSONDecodeError as e:
                logger.warning(f"Attempt {attempt}: Invalid JSON in file {output_json_path}: {str(e)}")
                if attempt < max_retries:
                    try:
                        os.remove(output_json_path)
                        logger.info(f"Deleted invalid JSON file: {output_json_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {output_json_path}: {str(e)}")
                    continue
            except Exception as e:
                logger.warning(f"Attempt {attempt}: Unexpected error verifying recipe {file_path}: {str(e)}")
                if attempt < max_retries:
                    try:
                        os.remove(output_json_path)
                        logger.info(f"Deleted invalid JSON file: {output_json_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {output_json_path}: {str(e)}")
                    continue
        else:
            logger.warning(f"Attempt {attempt}: JSON file not created at {output_json_path}")
            if attempt < max_retries:
                continue

    # All retries exhausted
    logger.error(f"All {max_retries} attempts failed for recipe: {file_path}")
    # Clean up invalid JSON file if exists
    if output_json_path and os.path.exists(output_json_path):
        try:
            os.remove(output_json_path)
            logger.info(f"Deleted invalid JSON file after all retries: {output_json_path}")
        except Exception as e:
            logger.warning(f"Failed to delete {output_json_path}: {str(e)}")
    return False


def extract_ingredients_from_recipes(recipes: List[Dict]) -> List[str]:
    """
    Extract all unique ingredient names from parsed recipes

    Args:
        recipes: List of parsed recipe data

    Returns:
        List of unique ingredient names
    """
    logger.info("Extracting ingredients from parsed recipes...")
    ingredients_set = set()

    for i, recipe in enumerate(recipes):
        logger.debug(f"Processing recipe {i+1}/{len(recipes)}: {recipe.get('name', 'Unknown')}")
        for ingredient in recipe.get('ingredients', []):
            name = ingredient.get('ingredient_name')
            if name:
                ingredients_set.add(name)

    ingredients_list = list(ingredients_set)
    logger.info(f"Extracted {len(ingredients_list)} unique ingredients")
    return ingredients_list


def parse_ingredients_list(ingredients_list: List[Dict[str, str]], project_root: str, output_json_path: str = None) -> Optional[List[Dict[str, Any]]]:
    """
    Parse the ingredients list using claude skill

    Args:
        ingredients_list: List of ingredient dicts with name and unit to standardize
        project_root: Project root directory
        output_json_path: Optional path to save the parsed JSON file

    Returns:
        Standardized ingredients data or None if error
    """
    logger.info(f"Parsing {len(ingredients_list)} ingredients...")

    # Convert list to string format for prompt (each item is a dict with name and unit)
    ingredients_str = json.dumps(ingredients_list, ensure_ascii=False, indent=2)
    # save to out/ingredents_raw.json
    save_to_json(ingredients_list, os.path.join(project_root, RecipeParserConfig.DEFAULT_OUTPUT_DIR, RecipeParserConfig.INGREDIENTS_RAW_FILE))

    # Add output path to prompt if provided
    prompt = f'/parse-ingredients'
    if output_json_path:
        prompt = f'/parse-ingredients `{output_json_path}`'

    # Retry logic with max 3 attempts
    max_retries = RecipeParserConfig.MAX_RETRIES
    for attempt in range(1, max_retries + 1):
        logger.info(f"Attempt {attempt}/{max_retries} for ingredients parsing")
        
        # Call claude to parse ingredients, pass ingredients list via stdin pipe
        result = run_claude_command(prompt, project_root, input_text=ingredients_str)
        if not result:
            logger.warning(f"Attempt {attempt}: Claude command returned no result")
            if attempt < max_retries:
                # Delete invalid JSON file if exists before retry
                if output_json_path and os.path.exists(output_json_path):
                    try:
                        os.remove(output_json_path)
                        logger.info(f"Deleted invalid JSON file: {output_json_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {output_json_path}: {str(e)}")
                continue

        # 验证目标 JSON 文件是否符合要求
        if output_json_path and os.path.exists(output_json_path):
            try:
                with open(output_json_path, 'r', encoding='utf-8') as f:
                    ingredients_data = json.load(f)
                
                # Validate required fields exist in each ingredient
                required_fields = RecipeParserConfig.REQUIRED_INGREDIENT_FIELDS
                valid = True
                for ingredient in ingredients_data:
                    for field in required_fields:
                        if field not in ingredient:
                            logger.warning(f"Attempt {attempt}: Missing required field '{field}' in parsed ingredient")
                            valid = False
                            break
                    if not valid:
                        break
                
                if valid:
                    logger.info(f"Successfully parsed and verified {len(ingredients_data)} ingredients")
                    return ingredients_data
                else:
                    if attempt < max_retries:
                        try:
                            os.remove(output_json_path)
                            logger.info(f"Deleted invalid JSON file: {output_json_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete {output_json_path}: {str(e)}")
                        continue

            except json.JSONDecodeError as e:
                logger.warning(f"Attempt {attempt}: Invalid JSON in file {output_json_path}: {str(e)}")
                if attempt < max_retries:
                    try:
                        os.remove(output_json_path)
                        logger.info(f"Deleted invalid JSON file: {output_json_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {output_json_path}: {str(e)}")
                    continue
            except Exception as e:
                logger.warning(f"Attempt {attempt}: Unexpected error verifying ingredients: {str(e)}")
                if attempt < max_retries:
                    try:
                        os.remove(output_json_path)
                        logger.info(f"Deleted invalid JSON file: {output_json_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {output_json_path}: {str(e)}")
                    continue
        else:
            logger.warning(f"Attempt {attempt}: JSON file not created at {output_json_path}")
            if attempt < max_retries:
                continue

    # All retries exhausted
    logger.error(f"All {max_retries} attempts failed for ingredients parsing")
    # Clean up invalid JSON file if exists
    if output_json_path and os.path.exists(output_json_path):
        try:
            os.remove(output_json_path)
            logger.info(f"Deleted invalid JSON file after all retries: {output_json_path}")
        except Exception as e:
            logger.warning(f"Failed to delete {output_json_path}: {str(e)}")
    return None


def save_to_json(data: Any, output_path: str):
    """
    Save data to JSON file

    Args:
        data: Data to save
        output_path: Path to save the JSON file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved data to {output_path}")
    except Exception as e:
        logger.error(f"Error saving to {output_path}: {str(e)}")


def collect_ingredients_from_json_files(output_dir: str) -> List[Dict[str, str]]:
    """
    Collect all ingredients from parsed recipe JSON files

    Args:
        output_dir: Directory containing parsed recipe JSON files

    Returns:
        List of ingredient dicts with name and unit
    """
    logger.info(f"Collecting ingredients from JSON files in {output_dir}")
    ingredients_set = set()
    ingredients_list = []

    if not os.path.exists(output_dir):
        logger.warning(f"Output directory does not exist: {output_dir}")
        return []

    for file_name in os.listdir(output_dir):
        if file_name.endswith('.json'):
            file_path = os.path.join(output_dir, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    recipe_data = json.load(f)
                    for ingredient in recipe_data.get('ingredients', []):
                        name = ingredient.get('ingredient_name')
                        unit = ingredient.get('unit', '')
                        if name:
                            key = f"{name}|{unit}"
                            if key not in ingredients_set:
                                ingredients_set.add(key)
                                ingredients_list.append({
                                    'ingredient_name': name,
                                    'unit': unit
                                })
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {str(e)}")

    logger.info(f"Collected {len(ingredients_list)} unique ingredients")
    return ingredients_list


def main(args=None):
    """Main entry point for the recipe parsing automation.
    
    Args:
        args: Optional list of command line arguments. If None, uses sys.argv[1:]
    """
    parser = argparse.ArgumentParser(description='Parse HowToCook recipes and ingredients')
    parser.add_argument('--repo-path', help='Path to existing HowToCook repository', default=None)
    parser.add_argument('--output-dir', help='Directory to save parsed JSON files', default=RecipeParserConfig.DEFAULT_OUTPUT_DIR)
    parser.add_argument('--temp-dir', help='Temporary directory for cloning repo', default=None)
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--parse-recipe', action='store_true', help='Only parse recipes (steps 1-3, 6)')
    parser.add_argument('--parse-ingredient', action='store_true', help='Only parse ingredients (steps 4-6)')
    parser.add_argument('--add-images', action='store_true', help='Only add images to existing parsed recipes')

    args = parser.parse_args(args)

    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    project_root = os.path.abspath('.')
    output_dir = os.path.abspath(args.output_dir)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Determine execution mode
    parse_recipe_only = args.parse_recipe
    parse_ingredient_only = args.parse_ingredient
    add_images_only = args.add_images
    full_process = not parse_recipe_only and not parse_ingredient_only and not add_images_only

    # Determine HowToCook repository path
    howtocook_path = args.repo_path
    temp_clone = False

    # Steps 1-3 require repository access
    if full_process or parse_recipe_only or add_images_only:
        if not howtocook_path:
            # Create temporary directory for cloning
            temp_dir = args.temp_dir or tempfile.mkdtemp(prefix='howtocook_')
            howtocook_path = os.path.join(temp_dir, 'HowToCook')
            temp_clone = True

            # Step 1: Clone repository
            logger.info("Step 1: Cloning HowToCook repository...")
            if not clone_howtocook_repo(howtocook_path):
                logger.error("Failed to clone HowToCook repository")
                return 1
        else:
            howtocook_path = os.path.abspath(howtocook_path)
            if not os.path.exists(howtocook_path):
                logger.error(f"Repository path does not exist: {howtocook_path}")
                return 1

    # Handle --add-images mode
    if add_images_only:
        logger.info("Running in --add-images mode...")
        result = add_images_to_recipes(output_dir, howtocook_path, project_root)
        
        # Clean up
        logger.info("Step 6: Cleaning up...")
        if temp_clone and args.temp_dir:
            try:
                shutil.rmtree(os.path.dirname(howtocook_path))
                logger.info("Cleaned up temporary directory")
            except Exception as e:
                logger.warning(f"Warning: Could not clean up temporary directory: {str(e)}")
        
        return result

    if full_process or parse_recipe_only:
        # Step 2: Find all markdown files
        logger.info("Step 2: Finding markdown files...")
        md_files = find_markdown_files(howtocook_path)
        logger.info(f"Found {len(md_files)} markdown files")

        # Step 3: Parse each recipe file
        logger.info("Step 3: Parsing recipes...")
        success_count = 0
        for i, md_file in enumerate(md_files):
            logger.info(f"Processing file {i+1}/{len(md_files)}: {os.path.basename(md_file)}")
            # Generate output JSON path for each recipe
            recipe_name = os.path.splitext(os.path.basename(md_file))[0]
            output_json_path = os.path.join(output_dir, f'{recipe_name}.json')
            if parse_single_recipe(md_file, project_root, output_json_path, howtocook_path):
                success_count += 1

        logger.info(f"Parsed {success_count}/{len(md_files)} recipes successfully")

    # Steps 4-5: Extract and parse ingredients
    if full_process or parse_ingredient_only:
        # Step 4: Get ingredients list from parsed JSON files
        logger.info("Step 4: Collecting ingredients from parsed recipes...")
        ingredients_list = collect_ingredients_from_json_files(output_dir)

        if ingredients_list:
            # Step 5: Parse ingredients
            logger.info("Step 5: Parsing ingredients...")
            logger.info(f"ingredients list: {json.dumps(ingredients_list, ensure_ascii=False)}")
            ingredients_output_path = os.path.join(output_dir, RecipeParserConfig.INGREDIENTS_FILE)
            parsed_ingredients = parse_ingredients_list(ingredients_list, project_root, ingredients_output_path)
            
            if parsed_ingredients:
                logger.info(f"Successfully parsed {len(parsed_ingredients)} ingredients")
            else:
                logger.warning("Failed to parse ingredients")
        else:
            logger.warning("No ingredients found to parse")

    # Step 6: Clean up
    logger.info("Step 6: Cleaning up...")
    if temp_clone and args.temp_dir:
        try:
            shutil.rmtree(os.path.dirname(howtocook_path))
            logger.info("Cleaned up temporary directory")
        except Exception as e:
            logger.warning(f"Warning: Could not clean up temporary directory: {str(e)}")

    logger.info("\nProcessing complete!")
    logger.info(f"Output saved to: {output_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())