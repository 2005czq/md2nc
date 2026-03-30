# md2nc

将 Markdown 题面转换为 NowCoder HTML 题面的 Python 工具。

> [!caution]
>
> 功能完善中，未来将支持更多 Markdown 语法，欢迎 Pull Request。

## 快速开始 (Python 3.9+)

```bash
python md2nc.py [input] [--description PATH] [--input-html PATH] [--output-html PATH] [--notation PATH]
```

|      参数       |        含义        |        缺省        |
| :-------------: | :----------------: | :----------------: |
|     `input`     | 输入 Markdown 路径 |    `problem.md`    |
| `--description` |    描述输出路径    | `description.html` |
| `--input-html`  |  输入格式输出路径  |    `input.html`    |
| `--output-html` |  输出格式输出路径  |   `output.html`    |
|  `--notation`   | 说明/提示输出路径  |  `notation.html`   |

你可以在项目仓库中查看展示效果。

## 当前支持

- 区块结构：段落、引用块、无序列表、有序列表、嵌套列表、ATX 标题、围栏代码块、行内与行间 LaTeX 公式
- 行内语法：行内代码、粗体、斜体、高亮 `==text==`、删除线、链接、原生 HTML 标签透传
- 混合嵌套：列表中嵌套引用、引用中嵌套列表、嵌套层级中的块公式与代码块

## 开源许可

本项目遵循 [MIT 开源协议](./LICENSE)。
