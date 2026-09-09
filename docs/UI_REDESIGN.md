# Logo 与界面更新

Logo 使用内置 image_gen 工具生成，PNG 原图保存在 `assets/logo.png`，多尺寸 Windows 图标保存在 `assets/logo.ico`（16、24、32、48、64、128、256 像素）。应用侧栏和窗口、现有打包脚本使用同一套图标。

## 最终生成提示词

> Use case: logo-brand. Create a polished app icon for SkyDreamBox, a desktop video/audio processing toolbox. A single simple geometric sky-blue open box incorporating a white play triangle and a subtle rising sky/cloud shape. Deep midnight-blue rounded square tile, cyan to periwinkle accents, crisp restrained geometry, strong legibility at 32px, centered generously sized symbol. No text, no letters, no mockup, no surrounding objects. Square composition. Save the generated image for use as the project's PNG and Windows ICO icon.

## 界面

深蓝导航、浅色画布、白色卡片；素材、任务参数与队列采用统一间距和层级。空列表绘制引导文字，不阻挡拖放和选择。小窗口下素材与参数可滚动，队列表格保留最小可读高度。

## 验证

- `python -m unittest discover -s tests -v`：40 项测试通过，包含小窗口布局回归测试。
- `python tools/capture_workbench.py`：验证实际引擎检测、导入、队列转码、预览播放与定位，生成工作台、粗剪及 900 × 620 小窗口截图。
- 未执行 Nuitka / 安装程序打包。
