# EvidenceDesk

**面向研究资料与技术文档的知识库问答工作台。**

EvidenceDesk将分散的文本资料组织为可检索的知识库，支持上传文档、查找相关片段、查看原文，并在配置模型服务后生成带引用的回答。适用于研究方法查询、项目文档查阅和个人知识整理。

## 功能

- **文档管理**：上传UTF-8编码的TXT或Markdown，按浏览器会话隔离自定义文档。
- **知识检索**：支持BM25、TF-IDF余弦相似度及RRF融合，适用于关键词和术语查询。
- **来源追溯**：保留文档标题、片段编号和原文字符位置，可从引用打开全文。
- **两种回答模式**：默认返回原文摘录；配置模型服务后，可生成附带编号引用的综合回答。
- **异常处理**：零命中提示、模型超时降级、请求体限制和模型并发控制。
- **检索评测**：提供文档级Recall@3、MRR@3与无关问题零命中率评测。

## 快速开始

在项目根目录执行（验证环境为Python 3.12）：

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器访问 http://127.0.0.1:8000 ，API文档位于 http://127.0.0.1:8000/docs 。Windows用户也可在安装依赖后运行run.bat。默认原文检索不需要模型密钥。

## 使用流程

1. 选择内置问题，或添加自己的TXT/Markdown文档。
2. 输入问题，选择检索策略并提交。
3. 查看检索结果和右侧证据，点击标题阅读全文。
4. 如需综合回答，配置模型后开启对应选项并输入访问口令。

内置知识库由自编研究方法说明构成，涉及数据划分、信息泄漏、分类评测及异构图建模，不包含真实患者数据。详细操作见[使用说明](docs/USAGE.md)。

## 模型配置

通过服务端环境变量配置兼容Chat Completions的HTTPS服务：

| 变量 | 用途 |
|---|---|
| LLM_BASE_URL | 接口基地址，不含末尾 /chat/completions |
| LLM_MODEL | 服务商支持的模型名称 |
| LLM_API_KEY | 服务端调用密钥 |
| DEMO_ACCESS_TOKEN | 模型回答访问口令；沿用已有变量名 |
| COOKIE_SECURE | HTTPS部署时设为1，本地HTTP保持0或不设置 |
| DATA_DIR | SQLite数据库保存目录，默认runtime |

Windows命令提示符使用 `set 变量名=变量值`，Linux使用 `export 变量名=变量值`，设置后重启服务。`.env.example` 仅用于说明，应用不会自动读取.env。

启用模型时，当前问题与检索片段会发送至配置的服务。密钥不得提交到仓库。不同服务商对temperature、max_tokens的支持可能不同，应在配置后验证兼容性。

## 技术架构

| 模块 | 实现 |
|---|---|
| 前端 | HTML、CSS、原生JavaScript |
| 接口 | FastAPI、Uvicorn |
| 存储 | SQLite、会话Cookie |
| 分块 | 最多420字符，相邻片段重叠80字符 |
| 切分 | 中文双字片段、英文词 |
| 检索 | BM25 / TF-IDF / RRF |
| 模型接入 | HTTPS Chat Completions兼容接口 |

完整接口与设计说明见[架构文档](docs/ARCHITECTURE.md)。

## 测试与评测

```bash
python -m unittest discover -s tests -v
python -m app.evaluate
```

评测结果保存到docs/evaluation_results.json。当前集合包含8份自编文档、17个有相关文档的问题与3个无关问题，用于小规模回归。评测先去重同源片段，再计算前三篇文档的指标；网页返回前四个片段，两者口径不同。

该集合规模较小、问题与原文接近，不能用于推断真实业务准确率。当前结果未证明融合检索优于单路策略。模型生成内容的正确性不在这组检索指标的评估范围内。测试范围见[验证记录](docs/VERIFICATION.md)。

## 部署

提供Dockerfile和render.yaml。构建容器：

```bash
docker build -t evidencedesk .
docker run --rm -p 8000:8000 evidencedesk
```

托管平台启动命令：

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

配置细节见[部署文档](docs/DEPLOY.md)。需要保留上传记录时，应使用可写持久存储。平台临时磁盘可能在重启、休眠或重新部署时清空。

## 项目结构

| 目录 | 内容 |
|---|---|
| app/ | 接口、存储、检索与评测 |
| web/ | 网页界面及交互 |
| data/ | 内置文档和评测问题 |
| tests/ | 自动化测试 |
| docs/ | 使用、架构、部署与验证说明 |

## 当前限制

- 目前是词法检索；TF-IDF不是语义Embedding，尚未接入语义召回或神经重排序。
- 每次提问独立处理，页面历史不会作为模型的多轮上下文。
- 文档格式限TXT/Markdown；每会话最多5份，每份最多50000字符。
- 上传记录满24小时后在下一次数据库操作时清理；Cookie会话不提供账号登录或长期恢复。
- 索引在请求时构建，适合小规模知识库。大量文档需要增量索引及检索服务。
- 限流为单进程全局控制，不能替代生产环境的身份鉴权、网关和配额管理。
- 引用编号校验只检查编号是否有效，不保证生成内容忠实于证据；检索分数也不是置信度。
