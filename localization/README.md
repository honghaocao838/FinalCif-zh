# 本地化维护说明

本目录保存中文翻译表和把翻译应用到源码的脚本。翻译已经提交到 `finalcif/` 源码里，本目录用于上游更新后重新应用。

## 文件

| 文件 | 用途 |
|---|---|
| `translations/*.json` | 按模块的英文到中文对照（键是上游原文） |
| `translations/checkdef_zh*.json` | CheckCIF 警报中文解释，构建时合并为 `finalcif/datafiles/checkdef_zh.json` |
| `apply_translations.py` | 基于 AST 定位字符串字面量并替换，处理跨行拼接 |
| `patch_fstrings.py` | 跨 f-string 片段的整句改写（批量脚本无法安全处理的部分） |
| `patch_source.py` | 内置 check.def、CheckCIF 中文帮助、停用自动更新、加载 Qt 中文翻译 |
| `checkdef_zh.json` | 合并后的警报解释，供安装包使用 |

## 上游更新后的流程

```bash
git fetch upstream
git merge upstream/master
python localization/apply_translations.py
python localization/patch_fstrings.py
python localization/patch_source.py
python -m compileall -q finalcif
```

`apply_translations.py` 会报告未被匹配的原文（上游改动过），按报告补词条即可。`patch_fstrings.py` 与 `patch_source.py` 是幂等的，重复运行不会重复插入。

## 词表格式

```json
{
  "gui/dialogs.pyc": {
    "English text": "中文文本"
  }
}
```

模块名沿用原始发行版的 `.pyc` 路径，脚本会自动换成 `finalcif/....py`。

## 注意

- 不要翻译会写入 CIF 的字符串（CIF 必须为 ASCII）。
- `patch_fstrings.py` 里的整句改写按源码原文精确匹配，上游改动后需要同步更新。
- `check.def` 不纳入版本控制，安装包构建时自动下载。
