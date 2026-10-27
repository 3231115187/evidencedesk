# EvidenceDesk · 可追溯知识库问答工作台

一个面向求职展示的完整可运行项目：上传文本 → 文档分块 → 词法检索 → 原文证据 → 可选大模型综合回答。

**当前交付为 v1.0 开发基线，未替你创建 GitHub 仓库或公网部署。** 默认不需要 API Key；配置模型后才启用生成式 RAG。示例材料均为自编教学内容，不含真实电子病历。适合围绕医疗数据研究、企业知识库与 AI 应用工程继续开发。

## 快速运行（Windows）

1. 解压后，把包含 `app`、`web`、`requirements.txt` 的 `evidencedesk` 文件夹放到 `D:\AI_projects\evidencedesk`。
2. 打开 Anaconda Prompt，执行：

```bat
conda activate rag_agent
cd /d D:\AI_projects\evidencedesk
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

3. 打开 http://127.0.0.1:8000 。按 Ctrl+C 停止。

如果没有 `rag_agent` 环境：先运行 `conda create -n evidence_demo python=3.12 -y`，然后 `conda activate evidence_demo`。也可用 Python 3.12 的 `python -m venv .venv`，再执行 `.venv\Scripts\activate`。

依赖安装过后可在已激活的环境中运行 `run.bat`。**不要直接双击 web/index.html**，页面通过后端接口加载文档。

## 面试官能看到什么

- 左侧：内置知识库、当前会话上传的 TXT / Markdown。
- 中间：示例问题、独立问题检索、原文摘录或可选模型回答。
- 右侧：命中文档、块编号、字符位置、检索分数；点击标题查看完整原文。
- 检索选择：BM25、TF-IDF余弦、RRF融合。
- 项目与架构面板：真实链路和明确的技术边界。
- `/docs`：FastAPI 自动生成的接口说明。

## 当前已经实现

| 能力 | 实现 |
|---|---|
| 文本分块 | 最多420字符，重叠80字符，记录原文起止位置 |
| 中文检索 | 双字片段；英文按词切分 |
| BM25 | k1=1.5、b=0.75 |
| TF-IDF | 对数词频、平滑IDF、余弦相似度 |
| RRF | 两路词法排名融合，k=60 |
| 文档存储 | SQLite、参数化查询、会话隔离、到期清理 |
| 回答 | 原文摘录 / 服务端可选模型调用 |
| 可靠性 | 零命中提示、引用编号范围检查、模型超时降级 |
| 演示限制 | 请求大小、文档数、全局请求频率、模型并发数限制 |
| 工程交付 | 测试、评测、Dockerfile、Render配置、GitHub Actions |

**不宣称已实现：** 语义Embedding、向量数据库、神经重排序、Agent、多轮记忆、生产级用户鉴权。TF-IDF是词法稀疏向量，不是语义向量。引用编号校验也不等于事实一致性验证。

## 可选：启用大模型回答

默认无需模型服务。若希望真正生成综合回答，在启动后端前，在同一个 Anaconda Prompt 设置：

```bat
set LLM_BASE_URL=https://你的服务商地址/v1
set LLM_MODEL=你的模型名称
set LLM_API_KEY=你的密钥
set DEMO_ACCESS_TOKEN=自己生成的长随机口令
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`LLM_BASE_URL` 应为兼容 Chat Completions 的 HTTPS 基地址，不要包含末尾的 `/chat/completions`。实现按常见兼容协议发送 messages、temperature 和 max_tokens；不同服务商可能需要适配参数。`.env.example` 只是说明文件，**程序不会自动加载 .env**。

页面勾选“使用大模型综合回答”，输入 `DEMO_ACCESS_TOKEN`。API Key只在服务端使用，网页不接收也不保存它。大模型会收到当前问题及命中的文档片段。未提供真实服务凭据，因此交付时只用模拟响应测试了生成分支、权限和失败降级，**未验证真实模型联网回答**。

## 测试和评测

```bat
python -m unittest discover -s tests -v
python -m app.evaluate
```

结果写入 `docs/evaluation_results.json`。当前合成回归集有20个问题：17个正例、3个无关问题，对应8份自编文档；前三篇文档去重后计算Recall@3、MRR@3，无关问题另算零命中率。网页展示前4个片段，评测统计文档级排名，两者口径不同。

本次三种方法在小集合上Recall@3和MRR@3均为1.0，**这说明题目简单且贴近原文，不说明算法达到真实业务100%准确率，也没有证明融合优于单路**。应扩充同义改写、长文档、冲突材料、多跳问题和难负例，并维护开发集与独立测试集。耗时只是本次环境的小样本结果，不能当作吞吐量或性能承诺。

## 上传到GitHub

按 [docs/DEPLOY.md](docs/DEPLOY.md) 操作。推荐仓库名 `evidencedesk`。

仓库首页应保留本README、真实评测结果和后续开发记录；部署成功后再补上真实的在线体验地址。不要写虚构用户数、性能提升、实习项目来源或上线经验。

## 项目结构

```text
evidencedesk/
  app/main.py          # FastAPI接口、调用控制、模型回答
  app/retrieval.py     # 分块、BM25、TF-IDF、RRF
  app/store.py         # SQLite文档存储和隔离
  app/evaluate.py      # 文档级检索评测
  web/                # 原生HTML、CSS、JavaScript
  data/               # 自编材料和合成评测问题
  tests/              # 自动化功能测试
  docs/               # 架构、部署、面试演示、验证记录
  .github/workflows/   # CI测试与评测
  Dockerfile
  render.yaml
  requirements.txt
```

## 局限与下一步

- 索引在请求时重建，适合小规模展示；大规模文档需缓存或独立检索服务。
- 词法检索对同义改写、语义推理、无关键词匹配的提问较弱。
- 文件格式仅TXT/Markdown，尚无PDF/OCR解析。
- 每次提问独立检索，界面历史不作为模型多轮上下文。
- Cookie会话用于演示隔离，不是账号系统；无长期会话恢复。
- 文档在服务器保存最多24小时，下一次数据库操作才触发删除；临时磁盘重启也会丢失。
- 请求频率限制为单进程演示级控制，部署建议单worker；生产环境应使用统一网关、身份鉴权、持久化限流及日志监控。
- 检索分数不表示置信度；只能对零命中做明确提示，非零命中仍可能不能回答问题。

参考：FastAPI测试 https://fastapi.tiangolo.com/tutorial/testing/ ；Render部署 https://render.com/docs/deploy-fastapi 。
