# init script

<details><summary>背景</summary>

> 因为意识到了[写 bash 脚本](https://github.com/lxl66566/init-script/tree/bash)的愚蠢，改用 python。  
> 然后因为 root 下处理 AUR 过于麻烦，等荷尔蒙过去以后又开始怀疑我写一键脚本的意义。  
> ~~最后这个脚本变成了“好多键脚本”，需要自行新建用户，安装 git，生成 ssh 密钥，clone 后运行还得到处输 sudo 密码（笑）不过我也可能会考虑用 bash 引导，使其真正自动化。~~ 所以现在真正自动化了。  
> 后来写着写着一发不可收拾，成为我的 python 学习项目了。
> 之后经历了一次大改动，模块化，函数式变为了面向对象，学习了包管理器设计思想。

</details>

## 介绍

这是我用于一键配置服务器的脚本，它可以：

- 一键安装（我的）常用软件
- 一键部署代理：目前支持 hysteria2, trojan-go, trojan
  - 用 caddy 反代我的博客伪装，自动更新证书
- 其他不重要的功能

作为 python 项目，它实现了：

- ~~自动获取 github latest release 的二进制文件，筛选合适的并下载安装~~ 已单独分离出一个项目：[bpm](https://github.com/lxl66566/bpm)
- pickle 简单缓存

## 使用

> [!CAUTION]  
> **脚本仅支持 ArchLinux, Debian, Ubuntu; python >= 3.10。** ~~想过适配 yum 系，系统也上了，结果发现要啥没啥，太累了。。我何必受这个罪呢。~~  
> **脚本需要在 root 下运行；使用脚本前请务必了解风险。本人不承担使用脚本造成的任何后果。**

目前经过测试的平台有：_ArchLinux_, _Debian 12_, _Ubuntu 22.04_

- 默认
  ```sh
  curl https://raw.githubusercontent.com/lxl66566/init-script/py/load.sh | bash
  ```
- 更改默认目录
  ```sh
  mypath=/mypath curl https://raw.githubusercontent.com/lxl66566/init-script/py/load.sh | bash
  ```
- debug 模式（显示详细信息）
  ```sh
  debug=1 curl https://raw.githubusercontent.com/lxl66566/init-script/py/load.sh | bash
  ```

## QA

- 装了 neovim 却不配置？
  - 插件把服务器搞崩过一次，所以不装插件了。
  - 不同人的使用习惯也不同，显然我不能强加我的 keybindings.
