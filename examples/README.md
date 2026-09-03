# 《Flask 从入门到进阶》示例程序

在运行示例程序之前，确保你已经把仓库克隆到本地，并完成创建虚拟环境，安装依赖等操作，详见[获取示例程序](https://docs.helloflask.com/installation)。

每一章的示例程序放在 examples 目录下不同的子文件内，以第 1 章示例程序为例，你需要把工作目录切换到 examples/ch1 目录内，然后执行 `uvicorn app:app --reload` 启动程序：

```
cd examples/ch1
uvicorn app:app --reload
```

如果你在安装部分使用 [PDM](https://pdm-project.org/latest/#installation)，则使用 `pdm run uvicorn app:app --reload` 启动程序：

```
pdm run uvicorn app:app --reload
```

现在使用浏览器打开 http://localhost:8000

部分示例程序还包含命令行命令（比如第 1 章的 `hello`、第 5 章的 `init`），使用 `python app.py` 执行：

```
python app.py hello  # 或 pdm run python app.py hello
```

通过切换到不同的示例程序目录来运行不同章节的示例程序。比如，下面的命令将会运行第 4 章的示例程序：

```
cd examples/ch4
uvicorn app:app --reload  # 或 pdm run uvicorn app:app --reload
```

所有示例程序和章节对应关系如下：

- 第 1 章：`ch1`
- 第 2 章：`ch2`
- 第 3 章：`ch3`
- 第 4 章：`ch4`
- 第 5 章：`ch5`、`notebook`
- 第 7 章：`longtalk`、`album`
- 第 12 章：`assets`、`cache`

*在书中相应位置会包含运行示例程序的提示。*
