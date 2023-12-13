# init script

> 因为意识到了[写 bash 脚本](https://github.com/lxl66566/init-script/tree/bash)的愚蠢，改用 python。  
> 然后因为 root 下处理 AUR 过于麻烦，等荷尔蒙过去以后又开始怀疑我写一键脚本的意义。  
> ~~最后这个脚本变成了“好多键脚本”，需要自行新建用户，安装 git，生成 ssh 密钥，clone 后运行还得到处输 sudo 密码（笑）不过我也可能会考虑用 bash 引导，使其真正自动化。~~ 所以现在真正自动化了。

**脚本仅支持 ArchLinux, Debian, Ubuntu。**

> 想着适配 yum 系，结果发现要啥没啥，太累了。。我何必受这个罪呢。

**脚本未进行多样化测试，使用前请务必了解风险。**

**本人不承担使用之造成的任何后果。**

目前经过测试的平台有：_Debian 12_

## 使用

```sh
curl https://raw.githubusercontent.com/lxl66566/init-script/py/load.sh | bash
```

更改默认目录

```sh
mypath=/mypath curl https://raw.githubusercontent.com/lxl66566/init-script/py/load.sh | bash
```

debug 模式（显示详细信息）

```sh
debug=1 curl https://raw.githubusercontent.com/lxl66566/init-script/py/load.sh | bash
```
