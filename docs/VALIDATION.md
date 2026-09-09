# 重构验证记录

验证环境：Windows，Python 3.13.15，PySide6 6.11.0，FFmpeg 2026-08-30-git-818cecc6e1，Nuitka 2.7.11。

## 源码与功能

- `python -m unittest discover -s tests -v`：39 项通过，无跳过。
- 最后一次 QSV 速度选项调整后，`python -m unittest discover -s tests -p test_workbench.py -v`：31 项新架构测试通过；旧版 8 项测试保留。
- 视频输出检查编码、分辨率和时长；音频验证 AAC、WAV、FLAC、ALAC，包括 AAC 裸流的实际解码时长。
- 验证字幕软封装、画面烧录，以及含中文、空格、引号和滤镜特殊字符的字幕路径。
- 验证精确剪切、关键帧剪切、多段分别导出及顺序合并。
- MP4、MKV、FLV 无损封装和 M4A 音频抽取，对比源文件与输出的媒体包 SHA-256 内容，确认未重新编码。
- 队列验证参数快照、修改单项、排序、失败继续、取消、启动失败、恢复中断任务、临时目录隔离、覆盖回滚与冲突保护。
- Qt 验证批量导入、拖放、配对提示、表单方案回填、导航、缺少引擎仍可进入设置以及小窗口尺寸。

## 原生窗口

- `python tools/capture_workbench.py`：通过真实队列压制、视频预览、定位、播放、暂停和关闭检查。
- `python main.py --verify-install dist/source-verification`：通过引擎探测、队列处理、Qt 多媒体解码及关闭收尾；机器可读结果位于输出目录的 `verification.json`。
- 检查 1200×800 和 900×620 逻辑尺寸，截图使用本机 Windows 150% DPI。参数区域可滚动，输出与队列操作保持可访问。
- 截图：[工作台](screenshots/workbench.png)、[粗剪](screenshots/trim.png)、[小窗口](screenshots/small-window.png)。

## Windows 交付包（2026-09-09）

- `python build.py --pefile`：成功生成 `dist/SkyDreamBox/SkyDreamBox.exe` 及 `dist/SkyDreamBox_v3.0.0_Setup.exe`，包含 Qt 平台/多媒体插件与项目许可证。
- 打包后的 `SkyDreamBox.exe --verify-install dist/package-verification`：退出码 0，`verification.json` 中 `success` 为 `true`，完成引擎探测、队列压制、视频解码/定位/播放/暂停及窗口关闭验证。
- `7z t dist/SkyDreamBox_v3.0.0_Setup.exe`：`Everything is Ok`，归档含 73 个文件，自解压包大小 26,902,917 字节。
- FFmpeg 和 FFprobe 仍需通过设置或 `PATH` 提供。构建产物及机器可读自检结果保留在忽略的 `dist/` 下。

## 验证边界

软件压制与音频处理使用真实 FFmpeg 素材完成集成验证。NVENC、QSV、AMF 的参数映射有回归测试，程序会额外进行设备可用性检测；未将这些测试等同于所有 GPU 和驱动组合的实际压制验证。

无损剪切本身不保证任意时间点的帧精度；裸 AAC 时长由容器探测估算。异常断电场景通过持久化状态和遗留目录模拟，不代表实际断电实验。
