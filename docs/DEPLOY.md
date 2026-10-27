# 上传GitHub与发布在线演示

这两件事不同：GitHub仓库展示源码；后端托管服务提供可运行的网址。**GitHub Pages不能直接运行本项目的Python后端。**

## 1. 本地验证

先按README运行，打开 http://127.0.0.1:8000 ，点击示例问题，再运行测试。这个地址只属于你本机，不能发给面试官当公网地址。

## 2. 上传GitHub

在你自己的GitHub账号创建空仓库 `evidencedesk`。不要预先勾选生成README，避免首次推送冲突。复制GitHub提供的仓库URL。

在 Anaconda Prompt 中执行：

```bat
cd /d D:\AI_projects\evidencedesk
git init
git add .
git status
```

检查待提交内容没有API Key、真实病历、个人文档和运行数据库；项目已提供.gitignore。然后：

```bat
git commit -m "feat: initial EvidenceDesk retrieval demo"
git branch -M main
git remote add origin https://github.com/你的用户名/evidencedesk.git
git push -u origin main
```

把占位URL换成实际仓库地址。首次推送可能需要你在自己的浏览器完成GitHub授权。若Git提示作者身份未配置，只在本仓库配置：

```bat
git config user.name "你的GitHub显示名"
git config user.email "你的GitHub提交邮箱"
```

再重新提交和推送。不要把GitHub令牌粘贴进代码或聊天。

## 3. 发布到支持Python的托管服务

可使用Render Web Service部署流程：https://render.com/docs/deploy-fastapi 。也可以自行使用Docker服务器。

在你自己的托管账号中连接该GitHub仓库，选择Python Web Service，设置：

| 配置 | 值 |
|---|---|
| Repository | 你的evidencedesk仓库 |
| Root Directory | 仓库根目录，留空 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Environment | `COOKIE_SECURE=1` |

仓库附有render.yaml，也可用平台的Blueprint方式读取配置。平台套餐和费用以你账号确认页为准；此项目未创建服务、未选择套餐、未产生部署费用。某些套餐存在休眠或临时磁盘限制，面试前应实际测试。

先保持不配置模型：所有访客仍能使用词法检索、看引用、上传测试文本。若启用模型，在托管服务的环境变量/密钥管理页面填写README中的四个模型变量。只把模型访问口令给需要试用的人，避免公开消耗模型额度。

部署成功后，平台会生成真实HTTPS地址。用无痕窗口打开并完成：点击示例问题 → 引用查看原文 → 上传无敏感信息的TXT → 新会话不能看到该上传 → 清空本会话上传。

将这个**真实地址**放到GitHub仓库About的Website字段、README开头和简历中。未部署前不要写“已上线”。

## 4. Docker方式

```bash
docker build -t evidencedesk .
docker run --rm -p 8000:8000 evidencedesk
```

容器自带示例材料。需要保留上传时，为`/app/runtime`配置可写持久卷；需要公网时由反向代理提供HTTPS，并设置`COOKIE_SECURE=1`。不要在没有TLS的公网中传输模型访问口令。

## 5. 常见问题

- 打开网页没文档：确认后端已运行，访问的是8000端口，不是双击HTML。
- 端口被占用：把启动命令改为`--port 8001`，浏览器也改为8001。
- 模型开关灰色：缺少LLM_BASE_URL、LLM_MODEL、LLM_API_KEY或DEMO_ACCESS_TOKEN之一，修改后需重启。
- 返回原文而非模型总结：默认模式本来就是原文；启用后失败会显示降级提示。
- HTTPS部署后会话异常：核对反向代理的转发头和实际请求协议，不能把不同域名的前端与后端随意混用。
- 推送后没有网页：GitHub上传不等于应用部署，需要完成第3步。
