# Omarchy File Previewer

简体中文 | [English](README.md)

https://github.com/user-attachments/assets/a7b1f2da-a173-4cde-a321-61574c0c9bbf

让 Nautilus 的图片空格预览和双击打开共用 **imv**，支持键盘操作，并在鼠标移动时保持键盘焦点。

## 依赖

- Omarchy，及其 Hyprland 0.56 Lua 配置、Nautilus 50、Sushi 50 和 imv 5。
- `python-gobject`、`gjs` 和 `desktop-file-utils`，Omarchy 通常已经包含这些依赖。

## 交互

- 在 Nautilus 中选中图片后按 `Space`，或双击图片，即可用 imv 打开。
- 图片窗口默认居中浮动，打开后立即获取键盘焦点，鼠标移出窗口时保持焦点。
- 鼠标移到左右屏幕边缘时，仍可正常唤出 `omarchy-side-panel`；悬停侧边栏不影响图片快捷键。主动点击其他窗口时正常切换焦点。
- 单张打开时，自动载入同目录图片，按文件名自然排序（`1`、`2`、`10`）。多选打开时只浏览选中的图片。
- 文本、PDF、视频等非图片文件继续使用原有的 Sushi 空格预览。
- 保留现有 imv 配置；本插件的按键覆盖只用于经插件打开的窗口。

| 按键 | 功能 |
| --- | --- |
| `j` / `k` | 下一张 / 上一张图片 |
| `h` / `l` | 已停用，不移动图片 |
| `-` / `=` | 缩小 / 放大图片 |
| `0` | 恢复 1:1 原始大小 |
| `↑` `↓` `←` `→` | 在屏幕上移动窗口，每次 40 像素 |
| `Esc` / `q` | 关闭图片窗口 |

## 安装

克隆仓库并安装：

```bash
git clone https://github.com/manateelazycat/omarchy-file-previewer.git
cd omarchy-file-previewer
python install.py
```

保持此目录路径不变，两个用户级入口会引用这里的代码：

- `~/.local/share/applications/imv.desktop`
- `~/.local/share/dbus-1/services/org.gnome.NautilusPreviewer.service`

默认图片应用的 ID 仍是 `imv.desktop`。安装器会备份原有入口到 `~/.local/state/omarchy-file-previewer/install.json`，可以重复运行。无需修改系统文件、全局鼠标设置或 Hyprland 用户配置文件，也无需重启文件管理器。

如果安装时旧 Sushi 服务已经运行，它会在原有预览窗口关闭、服务闲置退出后使用新入口。网络 URI 的预览继续交给 Sushi，本插件的目录切图针对本地图片。

## 卸载

```bash
python install.py --uninstall
```

恢复安装前的入口。安装后被用户手动编辑过的文件会保留，并输出对应路径。

## 开发

```bash
python -m unittest discover -s tests -p 'test_*.py'
python tests/nested.py
```

集成测试需要 Weston、`wtype`、`grim`、C 编译器和 Wayland 开发头文件。如果 Weston 解包在临时目录中，可用 `WESTON_PREFIX=/path/to/unpacked/usr python tests/nested.py`。

测试在无界面的 Weston 中嵌套 Hyprland，创建专用虚拟输出，并使用独立的 Wayland socket、D-Bus、配置、缓存和数据目录。实际操作 Nautilus 的空格和双击，验证切图、缩放、焦点、窗口移动、非图片预览及卸载恢复。

检测到 `~/omarchy-side-panel` 时，还会加载其真实侧边栏组件，验证预览期间的左右边缘触发、键盘焦点和主动窗口切换；可用 `SIDE_PANEL_SOURCE` 指定其他源码路径。不会向当前桌面发送测试输入。截图和日志保存在忽略版本管理的 `test-results/`。

焦点和移动规则使用 [Hyprland 窗口规则](https://wiki.hypr.land/Configuring/Basics/Window-Rules/) 和 [Lua dispatcher](https://wiki.hypr.land/configuring/core/dispatchers/) 接口。窗口布局仅匹配插件专用的 imv app ID；悬停焦点保护仅在图片窗口获取焦点时启用，切换或关闭后恢复原有规则。

## 协议

Omarchy File Previewer 仅按 GNU General Public License v3.0（`GPL-3.0-only`）发布。详见 [LICENSE](LICENSE)。
