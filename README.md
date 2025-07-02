# 天梦工具箱 (SkyDreamBox)



天梦工具箱是一个基于 Python、PyQt5 和 FFmpeg 构建的模块化图形用户界面（GUI）工具。它旨在为 FFmpeg 强大的音视频处理功能提供一个直观、易于使用的操作界面，让用户无需记忆复杂的命令行参数即可完成常用的音视频处理任务。

\## ✨ 功能特性

本工具箱将不同的功能划分到独立的选项卡中，界面清晰，操作便捷。

- **视频处理**:
  - 转换视频格式 (MP4, MKV, AVI, MOV等)。
  - 更改视频编码器 (libx264, libx265, NVIDIA GPU 加速等)。
  - 调整视频质量 (CRF), 分辨率, 帧率 (FPS) 和比特率。
  - 为视频添加并封装硬字幕。
  - 独立设置音频编码与比特率。
- **音频处理**:
  - 转换音频格式 (MP3, FLAC, AAC, WAV等)。
  - 支持多种音频编码器，包括有损和无损压缩。
  - 为无损编码（如FLAC）设置压缩等级。
  - 调整音频比特率。
- **封装与解封装**:
  - **封装 (Muxing)**: 将独立的视频流、音频流和字幕流合并（封装）到一个媒体文件中。
  - **解封装 (Demuxing)**: 从一个媒体文件中抽取视频流或音频流，并保存为独立文件。
- **常用操作**:
  - **视频截取**: 无需重新编码，快速地从视频中截取指定时间段的内容。
  - **图声合成**: 将一张静态图片和一个音频文件合成为一个视频文件。
- **专业命令**:
  - 为高级用户提供一个直接输入和执行原生 FFmpeg 命令的窗口。
- **实时反馈**:
  - 提供媒体文件详细信息预览。
  - 实时显示 FFmpeg 的输出日志。
  - 图形化进度条和实时处理速度、剩余时间等状态显示。



## 📋 系统需求



1. **Python 3**: 建议使用 Python 3.10 或更高版本。
2. **FFmpeg**: **必需的外部依赖**。您必须在您的操作系统中安装 FFmpeg，并确保其路径已添加到系统环境变量中，以便程序可以从任何位置调用 `ffmpeg` 和 `ffprobe` 命令。
3. **Python 库**: 所需的 Python 库已在 `requirements.txt` 文件中列出。



## ⚙️ 安装与运行



1. **克隆或下载项目**

   Bash

   ```
   git clone https://github.com/your-username/SkyDreamBox.git
   cd SkyDreamBox
   ```

2. 安装 FFmpeg

   请访问 FFmpeg 官网 并根据您的操作系统（Windows, macOS, Linux）下载并安装它。请确保将 ffmpeg 和 ffprobe 添加到系统环境变量中。

   您可以在终端或命令提示符中运行以下命令来检查是否安装成功：

   Bash

   ```
   ffmpeg -version
   ffprobe -version
   ```

3. 安装 Python 依赖

   项目目录下已提供 requirements.txt 文件。使用 pip 安装所有必需的库：

   Bash

   ```
   pip install -r requirements.txt
   ```

   这将会安装 `PyQt5`。

4. 运行程序

   执行 main.py 脚本来启动天梦工具箱：

   Bash

   ```
   python main.py
   ```

   或者在某些系统中，您可能需要使用：

   Bash

   ```
   python3 main.py
   ```



## 🛠️ 文件结构



项目代码经过重构，实现了模块化，结构如下：

```
SkyDreamBox/
├── ui/
│   ├── __init__.py
│   ├── main_window_ui.py
│   ├── video_tab_ui.py
│   ├── audio_tab_ui.py
│   ├── muxing_tab_ui.py
│   ├── demuxing_tab_ui.py
│   ├── common_ops_tab_ui.py
│   └── pro_tab_ui.py
├── assets/
│   └── logo.png
├── main.py
├── ui_tabs.py
├── process_handler.py
├── utils.py
├── about.py
├── requirements.txt
└── README.md
```



## 📜 开源许可



本项目采用 GNU 许可证。详情请参阅 `LICENSE` 文件。

------

作者: Tensin
