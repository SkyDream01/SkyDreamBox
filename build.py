# build.py
import os
import subprocess
import platform
import shutil
import sys
from pathlib import Path

# 引入项目常量，确保名称和版本号一致
from constants import APP_NAME, APP_VERSION

# --- 配置 ---
MAIN_SCRIPT = "main.py"
# EXE_NAME 用于 Nuitka 生成的 .exe 文件名 (建议保持英文以避免路径兼容性问题)
EXE_NAME = "SkyDreamBox"
# [修改] Windows 构建推荐使用 .ico 图标
ICON_FILE = "assets/logo.ico"
ASSETS_DIR = "assets"
OUTPUT_DIR = "dist"
# [修改] 最终的自解压安装包文件名 (包含版本号)
FINAL_SFX_NAME = f"{EXE_NAME}_v{APP_VERSION}_Setup.exe"

def create_sfx(source_dir, output_exe):
    """使用 7-Zip 创建自解压文件 (通过合并文件的方式)"""
    print("\n" + "="*70)
    print(f"--- 开始从 '{os.path.basename(source_dir)}' 文件夹创建自解压安装包 ---")

    # 尝试查找 7z 命令
    seven_zip_exe = shutil.which("7z") or shutil.which("7z.exe")
    if not seven_zip_exe:
        print("错误: '7z.exe' 未在系统 PATH 中找到。")
        print("请安装 7-Zip 并将其路径添加到环境变量中。")
        return

    # 1. 创建配置文件
    # folder_name 是解压后的根目录名 (例如 SkyDreamBox)
    folder_name = os.path.basename(source_dir)

    # [修改] 使用中文 APP_NAME 和版本号作为安装程序标题
    config_content = f""";!@Install@!UTF-8!
Title="{APP_NAME} v{APP_VERSION} 安装程序"
BeginPrompt="您准备好安装并运行 {APP_NAME} 吗？"
RunProgram="{os.path.join(folder_name, EXE_NAME + '.exe')}"
;!@InstallEnd@!
"""
    # 配置文件放在 dist 目录中
    config_file_path = os.path.join(OUTPUT_DIR, "sfx_config.txt")
    with open(config_file_path, 'w', encoding='utf-8') as f:
        f.write(config_content)

    # 2. 创建一个临时的 .7z 压缩包
    archive_file_name = "temp_archive.7z"
    archive_file_path = os.path.join(OUTPUT_DIR, archive_file_name)
    folder_to_archive = os.path.basename(source_dir) # 即 "SkyDreamBox"

    # 7z 压缩命令
    command_archive = [
        seven_zip_exe,
        "a",                # 添加文件
        "-y",               # 自动回答 Yes
        "-mx9",             # [新增] 使用最大压缩率
        archive_file_name,  # 目标文件名
        folder_to_archive,  # 源文件夹
    ]

    print("\n步骤 1/2: 创建临时的 7z 压缩包 (最大压缩率)...")
    try:
        # 在 dist 目录下执行，这样压缩包内的路径结构就是 SkyDreamBox/...
        subprocess.run(command_archive, check=True, cwd=OUTPUT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"临时压缩包 '{archive_file_name}' 创建成功。")
    except subprocess.CalledProcessError as e:
        print(f"\n创建 7z 压缩包失败! 错误: {e.stderr.decode('gbk', errors='ignore')}")
        if os.path.exists(config_file_path): os.remove(config_file_path)
        return

    # 3. 找到 SFX 模块 (7zS.sfx 是 GUI 版本，7z.sfx 是控制台版本)
    sfx_module = os.path.join(os.path.dirname(seven_zip_exe), "7zS.sfx")
    if not os.path.exists(sfx_module):
        sfx_module = os.path.join(os.path.dirname(seven_zip_exe), "7z.sfx")
        if not os.path.exists(sfx_module):
            print(f"错误: 找不到 7-Zip SFX 模块 (7zS.sfx 或 7z.sfx)。")
            # 清理
            if os.path.exists(config_file_path): os.remove(config_file_path)
            if os.path.exists(archive_file_path): os.remove(archive_file_path)
            return

    # 4. 合并文件生成最终的 EXE (SFX + Config + 7zArchive)
    print("步骤 2/2: 合成自解压安装包...")
    try:
        # 二进制合并
        with open(output_exe, 'wb') as outfile:
            for f_path in [sfx_module, config_file_path, archive_file_path]:
                with open(f_path, 'rb') as infile:
                    shutil.copyfileobj(infile, outfile)

        print("\n" + "="*70)
        print(f"构建完成！")
        print(f"自解压安装包: '{os.path.abspath(output_exe)}'")
        print("="*70)

    except IOError as e:
        print(f"\n创建自解压文件失败！IO错误: {e}")

    finally:
        # 清理临时文件
        if os.path.exists(config_file_path): os.remove(config_file_path)
        if os.path.exists(archive_file_path): os.remove(archive_file_path)

def build():
    print(f"--- 开始构建 {APP_NAME} v{APP_VERSION} (独立文件夹模式) ---")

    if not os.path.exists(MAIN_SCRIPT):
        print(f"错误: 主脚本 '{MAIN_SCRIPT}' 未找到！")
        return

    # 检查图标文件是否存在
    if not os.path.exists(ICON_FILE):
        print(f"警告: 图标文件 '{ICON_FILE}' 未找到，将使用默认图标。")

    nuitka_created_dir = os.path.join(OUTPUT_DIR, "main.dist")
    renamed_dir = os.path.join(OUTPUT_DIR, EXE_NAME)

    # Resolve every cleanup target before removing any build output.
    build_root = (Path(__file__).resolve().parent / OUTPUT_DIR).resolve()
    for target in (nuitka_created_dir, renamed_dir):
        resolved = Path(target).resolve()
        if resolved.parent != build_root or Path(target).is_symlink():
            raise ValueError(f"拒绝清理工作目录外的路径: {resolved}")
    for target in (nuitka_created_dir, renamed_dir):
        if os.path.exists(target):
            shutil.rmtree(target)

    # Nuitka 构建命令
    command = [
        sys.executable, "-m", "nuitka",
        MAIN_SCRIPT,
        "--standalone",
        "--plugin-enable=pyside6",
        "--include-qt-plugins=multimedia",
        f"--output-dir={OUTPUT_DIR}",
        f"--output-filename={EXE_NAME}.exe",
    ]

    if platform.system() == "Windows":
        print("配置 Windows 特定选项 (无控制台, 图标)...")
        command.append("--windows-console-mode=disable")
        if "--pefile" in sys.argv:
            # Supported by the verified Nuitka 2.7 toolchain; avoids the legacy
            # Dependency Walker scanner on Windows machines where it stalls.
            command.append("--experimental=force-dependencies-pefile")
        if os.path.exists(ICON_FILE):
             command.append(f"--windows-icon-from-ico={ICON_FILE}")

    if os.path.exists(ASSETS_DIR):
        print(f"添加资源文件夹: '{ASSETS_DIR}'")
        command.append(f"--include-data-dir={ASSETS_DIR}={ASSETS_DIR}")
    else:
        print(f"警告: 未找到资源文件夹 '{ASSETS_DIR}'，程序可能缺少图片资源。")

    if os.path.exists("LICENSE"):
        command.append("--include-data-files=LICENSE=LICENSE")

    print("\n" + "="*70)
    print("正在执行 Nuitka 编译，请耐心等待...")
    print("="*70)

    try:
        subprocess.run(command, check=True)
        print("="*70)
        print(f"Nuitka 构建成功！")

        # 处理构建产物目录
        if os.path.exists(nuitka_created_dir):
            print(f"重命名构建目录: '{os.path.basename(nuitka_created_dir)}' -> '{os.path.basename(renamed_dir)}'")
            os.rename(nuitka_created_dir, renamed_dir)
            build_output_dir = renamed_dir
        else:
            # 兼容不同版本 Nuitka 的输出行为
            build_output_dir = os.path.join(OUTPUT_DIR, f"{EXE_NAME}.dist")
            if not os.path.exists(build_output_dir):
                 print(f"错误：未找到预期的输出目录。")
                 return

        print(f"应用程序文件夹已生成: '{os.path.abspath(build_output_dir)}'")

        # 开始创建 SFX
        final_sfx_path = os.path.join(OUTPUT_DIR, FINAL_SFX_NAME)
        create_sfx(build_output_dir, final_sfx_path)

    except subprocess.CalledProcessError as e:
        print("="*70)
        # 尝试解码错误信息
        error_message = e.stderr.decode('gbk', errors='ignore') if e.stderr else str(e)
        print(f"构建失败！错误: {error_message}")
    except Exception as e:
        print(f"发生未预期的错误: {e}")

if __name__ == "__main__":
    build()
