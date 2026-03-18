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

## 开源许可

本项目遵循 [MIT 开源协议](./LICENSE)。