# 《Flask Web 开发实战（第 1 版）》示例程序

在运行示例程序之前，确保你已经把仓库克隆到本地，并完成创建虚拟环境，安装依赖等操作，详见[获取示例程序](https://docs.helloflask.com/installation)。

每一章的示例程序放在 demos 目录下不同的子文件内，以第 1 章示例程序为例，你需要把工作目录切换到 demos/hello 目录内，然后执行 `uvicorn app:app --reload` 启动程序：

```
$ cd demos/hello
$ uvicorn app:app --reload
```

现在使用浏览器打开 http://localhost:8000

如果你在安装部分使用 [Pipenv](https://pipenv.pypa.io/en/latest/index.html)，则使用 `pipenv run uvicorn app:app --reload` 启动程序：

```
pipenv run uvicorn app:app --reload
```

部分示例程序还包含命令行命令（比如第 1 章的 `hello`、第 5 章的 `initdb`），使用 `python app.py` 执行：

```
$ python app.py hello  # 或 pipenv run python app.py hello
```

通过切换到不同的示例程序目录来运行不同章节的示例程序。比如，下面的命令将会运行第 4 章的示例程序：

```
$ cd demos/form
$ uvicorn app:app --reload  # 或 pipenv run uvicorn app:app --reload
```

*在书中，每一章的开头都会包含运行实例程序的提示。*
