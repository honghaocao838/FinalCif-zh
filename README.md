# FinalCif 中文版

FinalCif v180 的中文本地化分支，基于上游 [dkratzert/FinalCif](https://github.com/dkratzert/FinalCif)，遵循同一 Beer-Ware 许可。

界面、提示、对话框与 CheckCIF 警报解释均已汉化；生成的 CIF 内容保持英文。

## 下载与安装

在 [Releases](https://github.com/honghaocao838/FinalCif-zh/releases) 下载 `FinalCif-zh-v180-setup-x64.exe`，双击安装。安装到当前用户目录，不需要管理员权限。支持 Windows 10/11 x64。

启动后可直接打开 `.cif`、`.res`、`.hkl` 文件，或把它们拖到窗口上。

## 功能

- 界面完整汉化：主窗口、标签页、按钮、列头、输入提示、tooltip、菜单项、状态栏消息、警告与询问框。
- Qt 标准控件汉化：确定、取消、是、否、关闭，以及标准文件对话框。
- 主表列说明：表头上方常驻说明条，列标题与左侧 CIF 键提供悬停解释。
- CheckCIF 警报解释：点击 PLAT 警报查看解释。官方 `check.def` 随安装包提供，离线可用；58 条常用警报附中文，其余显示官方英文原文。
- 关闭上游自动更新：避免英文版覆盖中文版。更新通过本仓库 Releases 发布。

## 与上游的差异

| 项目 | 说明 |
|---|---|
| 界面文字 | 全部改为中文 |
| 主表说明 | 新增列说明条与表头 tooltip |
| CheckCIF 帮助 | 中文在前、英文原文在后；`check.def` 内置 |
| 自动更新 | 已停用 |
| 版本号 | 保持 180，与上游一致 |

未翻译的内容：保存的 CIF（CIF 要求 ASCII）、报告正文与模板、CIF 键名与公式符号、PLATON 版权声明、模板数据名称、CheckCIF 报告中服务器返回的英文警报正文。

## 从源码运行

需要 Python 3.12 或更高版本。

```bash
git clone https://github.com/honghaocao838/FinalCif-zh.git
cd FinalCif
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python finalcif\finalcif_start.py
```

## 本地化维护

`localization/` 目录存放翻译表与脚本：

- `translations/*.json`：按模块的英文到中文对照。
- `apply_translations.py`：把词表应用到源码（基于 AST 定位字符串字面量）。
- `patch_fstrings.py`：处理跨 f-string 片段的整句改写。
- `patch_source.py`：内置 check.def、CheckCIF 中文帮助、关闭自动更新、加载 Qt 中文翻译。
- `checkdef_zh.json`：CheckCIF 警报中文解释（58 条）。

上游更新后，先合并上游改动，再依次运行以上三个脚本并检查 `compileall`。

## 构建安装包

需要 [Inno Setup 6](https://jrsoftware.org/isdl.php) 和一份官方 FinalCif v180 安装目录（提供 Python 运行时与依赖）。

```powershell
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 `
    -FinalCifInstall "C:\Program Files\FinalCif" `
    -InnoSetup "C:\Program Files (x86)\Inno Setup 6"
```

脚本会复制运行时、用本仓库的 `finalcif` 包替换程序代码、打包 PLATON 与 check.def，并调用 `ISCC.exe` 生成安装包。

## 许可与致谢

- 原版 FinalCif：Daniel Kratzert，Beer-Ware（Revision 42），见 `LICENSE.md`。
- 中文汉化：H.C（2026），同样以 Beer-Ware 发布，见 `LICENSE.md`。
- PLATON：Anthony L. Spek，学术用途免费，见 `THIRD_PARTY_NOTICES.md`。
- fastmolwidget：MIT。
- Qt for Python（PySide6）：LGPLv3。

## 联系

H.C，honghaocao838@gmail.com。问题请发邮件或在仓库开 Issue。
