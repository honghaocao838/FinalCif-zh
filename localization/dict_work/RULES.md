# CIF 字典帮助翻译规则

输入文件是 JSON：键为 CIF 键名，值为一段 HTML 帮助文本，例如：

```
"<pre><h2>_cell_length_a</h2> Unit cell parameter a ...</pre>
 <br><p><h4>Type:</h4> number (int or float)</p>
 <br><p><h4>Limits:</h4> 0.0:∞ </p>"
```

## 必须遵守

1. 保持 JSON 键完全不变，不增不减。输出 UTF-8，`json.dump(..., ensure_ascii=False, indent=1)`。
2. 只翻译 HTML 中的自然语言文本。
3. 原样保留所有 HTML 标签、属性、实体：`<pre>` `</pre>` `<h2>` `</h2>` `<br>` `<p>` `<h4>` `</h4>` `&amp;` `&gt;` `&lt;` `&quot;` `&#...;`。
4. `<h2>` 内的 CIF 键名（以下划线开头）不得改动。
5. 把 `<h4>Type:</h4>` 译为 `<h4>类型：</h4>`，`<h4>Limits:</h4>` 译为 `<h4>取值范围：</h4>`。
6. Type 的描述要翻译，例如 `number (int or float)` 译为 `数字（整数或浮点数）`，`Text` 译为 `文本`，`string` 译为 `字符串`，`char` 译为 `字符`。
7. 保留 CIF 排版标记 `^` 和 `~`（上下标），保留公式、数学符号、单位、数值、参考文献和作者名。
8. 保留程序名、文件名、CIF 键名、空间群符号、原子标签、SHELXL 指令（如 AFIX、DFIX、SIMU、WGEN）。
9. 保留作为 CIF 取值出现的英文 token，例如 `single`、`double`、`yes`、`no`、`.`、`?`，不要翻译成中文。
10. 保留原有换行和段落结构，不要把 `<pre>` 内的大段文字合并成一行。
11. 术语统一：
    - atomic displacement parameter 原子位移参数（ADP 保留）
    - standard uncertainty (s.u.) 标准不确定度（s.u.）
    - occupancy 占有率
    - reflection 衍射点
    - refinement 精修
    - space group 空间群
    - unit cell 晶胞
    - asymmetric unit 不对称单元
    - data block 数据块
12. 不添加译者注、不省略内容、不总结。原文多长，译文对应完整。

## 自检（写文件前）

- 解析输出 JSON，确认键集合与输入一致。
- 每条检查 `<pre>` 与 `</pre>` 数量一致，`<h2>` 与 `</h2>` 数量一致，`<h4>` 与 `</h4>` 数量一致。
- 确认没有空值，没有残留整段英文正文（公式和键名除外）。
- 发现无法翻译的片段时保留英文原文，不要删除。
