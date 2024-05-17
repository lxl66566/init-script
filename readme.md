# init script

<details><summary>背景</summary>

> 因为意识到了[写 bash 脚本](https://github.com/lxl66566/init-script/tree/bash)的愚蠢，改用 python。  
> 然后因为 root 下处理 AUR 过于麻烦，等荷尔蒙过去以后又开始怀疑我写一键脚本的意义。  
> ~~最后这个脚本变成了“好多键脚本”，需要自行新建用户，安装 git，生成 ssh 密钥，clone 后运行还得到处输 sudo 密码（笑）不过我也可能会考虑用 bash 引导，使其真正自动化。~~ 所以现在真正自动化了。  
> 后来写着写着一发不可收拾，成为我的 python 学习项目了。
> 之后经历了一次大改动，模块化，函数式变为了面向对象，学习了包管理器设计思想。

同时这个项目也是 [bpm](https://github.com/lxl66566/bpm) 的原身和灵感来源。

</details>

## 介绍

这是我用于一键配置服务器的脚本，它可以：

- 一键安装（我的）常用软件
- 一键部署代理：目前支持 hysteria2, trojan-go, trojan, openppp2
  - 用 caddy 反代我的博客伪装，自动更新证书
- 其他不重要的功能

## 使用

> [!CAUTION]  
> **脚本仅支持 ArchLinux, Debian 系; python >= 3.10。** ~~想过适配 yum 系，系统也上了，结果发现要啥没啥，太累了。。我何必受这个罪呢。~~  
> **脚本需要在 root 下运行；使用脚本前请务必了解风险。本人不承担使用脚本造成的任何后果。**  
> 目前经过测试的平台有：_ArchLinux_, _Debian 12_, _Ubuntu 22.04_

- 默认
  ```sh
  curl https://raw.githubusercontent.com/lxl66566/init-script/py/load.sh -o load.sh && chmod +x load.sh && ./load.sh
  ```
- 更改默认目录
  ```sh
  export mypath=/mypath && curl https://raw.githubusercontent.com/lxl66566/init-script/py/load.sh -o load.sh && chmod +x load.sh && ./load.sh
  ```

其中，`export mypath=/mypath` 修改了环境变量。类似地，您可以修改环境变量使程序拥有不同的运行表现：

```sh
mypath=/mypath  # 更改默认目录，所有缓存、证书、代码仓库将全部放在此目录下。
debug=1         # debug 模式，显示调试信息。
DISABLE_TUI=1   # 使用传统面板，而非 tui 面板。如果 tui 面板在您的系统上工作异常，请使用此选项。
```

除了通过环境变量修改，还有一部分配置选项放在 `init-script/var.py` 中，您可以自行更改配置。

如果您需要修改源码后运行，请在项目目录下执行 `python3 -m init-script`。

### 代理

这里部署的代理大部分需要域名，请自行解析。代理的[默认开启端口](https://github.com/lxl66566/init-script/blob/c1cb3c466a5719f7e2dd8d344b2dc12b5a478cd0/init-script/var.py#L15-L20)：

```json
"openppp2": 29777,
"hysteria": 30000,
"trojan-go": 40000,
"trojan": 50000,
```

其中，只有 `openppp2` 无需域名。若您未输入域名，其他代理将不会被安装&部署。

[如何使用？](https://absx.pages.dev/articles/proxy/)

如果代理无法连接，且对应服务已启动成功，请检查服务器防火墙。

## QA

- 装了 neovim 却不配置？
  - 插件把服务器搞崩过一次，所以不装插件了。
  - 不同人的使用习惯也不同，显然我不能强加我的 keybindings.
