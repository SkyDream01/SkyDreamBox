# build.py
import os
import subprocess
import platform
import shutil

# --- 配置 ---
MAIN_SCRIPT = "main.py"
# EXE_NAME 用于 Nuitka 生成的 .exe 文件、重命名的文件夹以及 SFX 的标题
EXE_NAME = "SkyDreamBox" 
ICON_FILE = "assets/logo.ico"
ASSETS_DIR = "assets"
OUTPUT_DIR = "dist"
# 最终的自解压安装包文件名
FINAL_SFX_NAME = "SkyDreamBox_Installer.exe"

def create_sfx(source_dir, output_exe):
    """使用 7-Zip 创建自解压文件 (通过合并文件的方式)"""
    print("\n" + "="*70)
    print(f"--- 开始从 '{os.path.basename(source_dir)}' 文件夹创建自解压安装包 ---")

    seven_zip_exe = shutil.which("7z") or shutil.which("7z.exe")
    if not seven_zip_exe:
        print("错误: '7z.exe' 未在系统 PATH 中找到。")
        print("请安装 7-Zip 并将其路径添加到环境变量中。")
        return

    # 1. 创建配置文件
    # 因为我们打包的是整个文件夹，所以解压后运行的程序路径是 "文件夹名\程序名"
    folder_name = os.path.basename(source_dir)
    config_content = f""";!@Install@!UTF-8!
Title="{EXE_NAME} 安装程序"
BeginPrompt="您想将 {EXE_NAME} 解压并运行吗？"
RunProgram="{os.path.join(folder_name, EXE_NAME + '.exe')}"
;!@InstallEnd@!
"""
    # 配置文件放在 dist 目录中
    config_file_path = os.path.join(OUTPUT_DIR, "sfx_config.txt")
    with open(config_file_path, 'w', encoding='utf-8') as f:
        f.write(config_content)

    # 2. 创建一个临时的 .7z 压缩包
    # 为了只打包 SkyDreamBox 文件夹，我们需要在 dist 目录内执行压缩命令
    archive_file_name = "temp_archive.7z"
    archive_file_path = os.path.join(OUTPUT_DIR, archive_file_name)
    folder_to_archive = os.path.basename(source_dir) # 这就是 "SkyDreamBox"

    command_archive = [
        seven_zip_exe,
        "a",
        "-y",
        archive_file_name, # 在 cwd (dist) 中的相对路径
        folder_to_archive,   # 在 cwd (dist) 中的相对路径
    ]
    
    print("\n步骤 1/2: 创建临时的 7z 压缩包...")
    try:
        # 关键改动：将工作目录切换到 dist，这样 7z 就会打包 SkyDreamBox 文件夹本身
        subprocess.run(command_archive, check=True, cwd=OUTPUT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"临时压缩包 '{archive_file_name}' 创建成功。")
    except subprocess.CalledProcessError as e:
        print(f"\n创建 7z 压缩包失败! 错误: {e.stderr.decode('gbk', errors='ignore')}")
        if os.path.exists(config_file_path): os.remove(config_file_path)
        return

    # 3. 找到 SFX 模块
    sfx_module = os.path.join(os.path.dirname(seven_zip_exe), "7zS.sfx")
    if not os.path.exists(sfx_module):
        sfx_module = os.path.join(os.path.dirname(seven_zip_exe), "7z.sfx")
        if not os.path.exists(sfx_module):
            print(f"错误: 找不到 7-Zip SFX 模块 (7zS.sfx 或 7z.sfx)。")
            if os.path.exists(config_file_path): os.remove(config_file_path)
            if os.path.exists(archive_file_path): os.remove(archive_file_path)
            return
            
    # 4. 合并文件生成最终的 EXE
    print("步骤 2/2: 合成自解压安装包...")
    try:
        if platform.system() == "Windows":
            final_command = f'copy /b "{sfx_module}" + "{config_file_path}" + "{archive_file_path}" "{output_exe}"'
            subprocess.run(final_command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            with open(output_exe, 'wb') as outfile:
                for f_path in [sfx_module, config_file_path, archive_file_path]:
                    with open(f_path, 'rb') as infile:
                        shutil.copyfileobj(infile, outfile)

        print("\n自解压安装包创建成功！")
        print(f"文件位于: '{os.path.abspath(output_exe)}'")

    except subprocess.CalledProcessError as e:
        print(f"\n创建自解压文件失败！错误: {e.stderr.decode('gbk', errors='ignore')}")

    finally:
        # 清理临时文件
        if os.path.exists(config_file_path): os.remove(config_file_path)
        if os.path.exists(archive_file_path): os.remove(archive_file_path)

def build():
    print(f"--- 开始构建 {EXE_NAME} (独立文件夹模式) ---")

    if not os.path.exists(MAIN_SCRIPT):
        print(f"错误: 主脚本 '{MAIN_SCRIPT}' 未找到！")
        return
        
    nuitka_created_dir = os.path.join(OUTPUT_DIR, "main.dist")
    renamed_dir = os.path.join(OUTPUT_DIR, EXE_NAME)

    if os.path.exists(nuitka_created_dir):
        shutil.rmtree(nuitka_created_dir)
    if os.path.exists(renamed_dir):
        shutil.rmtree(renamed_dir)

    command = [
        "python", "-m", "nuitka",
        MAIN_SCRIPT,
        "--standalone",
        "--plugin-enable=pyside6",
        f"--output-dir={OUTPUT_DIR}",
        f"--output-filename={EXE_NAME}.exe",
    ]

    if platform.system() == "Windows":
        print("为 Windows 添加无控制台和图标选项。")
        command.extend([
            "--windows-disable-console",
            f"--windows-icon-from-ico={ICON_FILE}",
        ])

    if os.path.exists(ASSETS_DIR):
        print(f"找到并添加资源文件夹: '{ASSETS_DIR}'")
        command.append(f"--include-data-dir={ASSETS_DIR}={ASSETS_DIR}")
    else:
        print(f"警告: 未找到资源文件夹 '{ASSETS_DIR}'，图片将无法显示。")

    print("\n将执行的 Nuitka 命令:")
    print(" ".join(command))
    print("\n" + "="*70)
    print("Nuitka 正在编译，请耐心等待...")
    print("="*70)

    try:
        subprocess.run(command, check=True)
        print("="*70)
        print(f"Nuitka 构建成功！")
        
        if os.path.exists(nuitka_created_dir):
            print(f"将文件夹 '{os.path.basename(nuitka_created_dir)}' 重命名为 '{os.path.basename(renamed_dir)}'")
            os.rename(nuitka_created_dir, renamed_dir)
            build_output_dir = renamed_dir
        else:
            build_output_dir = os.path.join(OUTPUT_DIR, f"{EXE_NAME}.dist")
            if not os.path.exists(build_output_dir):
                 print(f"错误：未找到预期的输出目录 '{nuitka_created_dir}' 或 '{build_output_dir}'。")
                 return
        
        print(f"应用程序已生成在 '{os.path.abspath(build_output_dir)}' 文件夹中。")
        
        final_sfx_path = os.path.join(OUTPUT_DIR, FINAL_SFX_NAME)
        create_sfx(build_output_dir, final_sfx_path)

    except subprocess.CalledProcessError as e:
        print("="*70)
        # 尝试用 gbk 解码 windows 命令行输出的中文错误
        error_message = e.stderr.decode('gbk', errors='ignore') if e.stderr else str(e)
        print(f"构建失败！错误: {error_message}")

if __name__ == "__main__":
    build()