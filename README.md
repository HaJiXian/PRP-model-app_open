```
model_v_2.0:新版本，添加了知识库检索功能和大语言模型预测接口，完善了用户交互界面，优化了结果信息界面布局,添加了部分安全功能。
model_v_2.0/
  static/
      sources/
        1.gif 等待界面用图1
        2.gif 等待界面用图2
        3.gif 等待界面用图3
      script.js 前端逻辑文件
      style.css 前端界面样式表
  templates/
    index.html 问卷界面
    result.html 结果结局
    start.html 开始界面
    wait.html 等待界面
  .gitgnore 忽略无关文件（github上传用）
  app.py 后端文件
  RAG知识库实验用文档.txt 正如其名
  RF-mf_slct_r0.pkl 预测模型
  run.bat 程序运行脚本（直接通过app文件应该也可以起到同样的运行效果）
  setup.bat 环境安装脚本（自动安装，需要科学上网，或者修改其中路径源为清华镜像源等国内路径则可不用科学上网。————国外路径需要科学上网，国内路径不能开科学上网）
```
```
添加了换行显示
```
