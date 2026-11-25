# 完整启动流程：AutoDL RAG + 本地车书问答应用

> 以下保留为 W07 旧部署说明。当前版本的网关需要资产清单和 v2 证据格式，
> 请优先参考[当前启动与升级说明](reliability-upgrade.md)。无需 AutoDL 时，
> 在项目目录的 CMD 执行 `scripts\start.cmd`，打开 http://localhost:8020/app；
> 该环境明确使用模拟结果，不能作为真实 AI 验证。

> W07 采集证据时已在 AutoDL 启动后台网关。如果它仍在运行，只需保持或重新建立
> SSH 隧道，不要再启动第二份网关。两种启动模式及判定方法见 [operations.md](operations.md)。

适用场景：已有模型、索引、数据库和接口文件，需要在 AutoDL 实例或电脑重启后重新运行工程。

当前已验证的配置：

| 项目 | 值 |
|---|---|
| 本地工程 | `E:\Users\PC\Desktop\maie6000c` |
| AutoDL SSH | `root@region-9.autodl.pro`，端口 `16814` |
| 远程 RAG 目录 | `/root/autodl-tmp/RAG` |
| 远程 Python | `/root/miniconda3/envs/rag/bin/python` |
| 远程 LLM | `127.0.0.1:8000/v1` |
| 远程 RAG HTTP 接口 | `127.0.0.1:6001` |
| Windows SSH 转发 | `127.0.0.1:6001` |
| 本地网页 | `http://localhost:8000/app` |

SSH 地址和端口以 AutoDL 面板中实际显示的信息为准。以下命令使用本次已验证的连接信息；如果与你的面板不一致，请同时替换 SSH、scp 命令中的主机和端口。

## 1. 启动 AutoDL 实例

在 AutoDL 控制台启动原来的 GPU 实例，等待可以 SSH 登录。

## 2. 本机 CMD 窗口 A：登录远程并启动原有依赖

在 Windows 的 CMD 中执行：

```cmd
ssh -p 16814 root@region-9.autodl.pro
```

输入 SSH 密码。登录后，提示符变为远程的 `root@...`，接下来执行的是 **Linux 命令**：

```bash
cd /root/autodl-tmp/RAG
source config.ini
which python
```

`which python` 应输出：

```text
/root/miniconda3/envs/rag/bin/python
```

根据本地保存的原 RAG 配置，`source config.ini` 会激活 `rag` 环境、导出环境变量，并启动：

1. 语义切分服务，端口 6000。
2. vLLM 本地模型服务，端口 8000。
3. MongoDB，端口 27017。

脚本包含两次 `sleep 10`，还需等待实际模型加载完成。**回到命令提示符并不等于模型已就绪。** 可在同一远程窗口验证：

```bash
curl -fsS http://127.0.0.1:8000/v1/models
python -c "from src.client.mongodb_config import MongoConfig; print(MongoConfig.get_db().command('ping'))"
```

第一个命令应返回包含模型列表的 JSON；第二个应能连接 MongoDB，并返回包含 `ok: 1` 的结果。

若模型尚未就绪，查看日志，等待后再次检查：

```bash
tail -n 50 /root/autodl-tmp/RAG/log/qwen3-7b.log
tail -n 50 /root/autodl-tmp/RAG/log/semantic_chunk.log
```

`source config.ini` 会启动后台进程，**同一批服务正常运行时不要反复执行**，以免端口冲突或重复占用显存。本项目的检索代码通过 `data/saved_index/milvus.db` 连接本地 Milvus Lite，不需要在下面流程中再启动独立的 Milvus 容器。

工程网页使用新接口程序，因此这里无需运行 `python infer.py`。它与 HTTP 接口都会加载检索和重排模型，同时运行会增加显存占用。

## 3. 本机 CMD 窗口 B：启动 RAG HTTP 接口和 SSH 隧道

新开一个 **Windows CMD 窗口**，在 `C:\Users\...>` 提示符下执行下面一整行：

```cmd
ssh -t -p 16814 -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:6001:127.0.0.1:6001 root@region-9.autodl.pro "/root/miniconda3/envs/rag/bin/python /root/autodl-tmp/RAG/maie_rag_gateway.py --rag-dir /root/autodl-tmp/RAG --port 6001"
```

按提示输入 SSH 密码。此命令会同时建立端口转发、启动 RAG 接口，并加载检索及重排模型。看到以下信息后表示接口启动完成：

```text
Application startup complete
```

**保持窗口 B 打开。** 按 Ctrl+C 或关闭此窗口，会停止当前前台运行的 RAG 接口和 SSH 转发。窗口 B 不需要再次执行 `source config.ini`；窗口 A 已启动依赖，这里用已确认的 Python 绝对路径运行。

### 仅首次部署、接口文件丢失或更新后：上传一次

接口文件已上传过，正常重启不需要重复上传。如果远程报 `maie_rag_gateway.py` 不存在，或你更新了本地适配器，则在启动窗口 B 的命令之前运行：

```cmd
scp -P 16814 "E:\Users\PC\Desktop\maie6000c\scripts\rag_gateway.py" root@region-9.autodl.pro:/root/autodl-tmp/RAG/maie_rag_gateway.py
```

## 4. 本机 CMD 窗口 C：启动本地车书问答应用

先打开 Docker Desktop，等待 Docker 引擎可用。然后新开一个 Windows CMD，执行：

```cmd
cd /d "E:\Users\PC\Desktop\maie6000c"
docker --context default compose up -d --wait
docker --context default compose ps
```

`cd /d` 会同时切换盘符和目录，适合从 `C:\Users\PC>` 进入 E 盘工程。

已有 `.env` 已配置，正常重启无需覆盖。容器使用的远程地址为 `RAG_SERVICE_URL=http://host.docker.internal:6001`。API 会自动运行数据库增量迁移，并保留 PostgreSQL 数据卷中的历史记录。

预期有四个运行中的服务：`db`、`ai`、`api`、`worker`。前三个有健康检查，Worker 显示运行状态。

只有首次构建或修改了本地应用代码时，才改用：

```cmd
docker --context default compose up -d --build --wait
```

## 5. 验证连接并打开页面

仍在本机 CMD 窗口 C 执行：

```cmd
curl.exe -fsS http://localhost:8000/system/status
```

正常结果为：

```json
{"api":"ready","database":"ready","rag":"ready"}
```

在浏览器打开：

```text
http://localhost:8000/app
```

页面应显示“车书服务已连接”。它每 15 秒检查一次连接，服务刚启动时可能需要稍等。提问“Model 3 哨兵模式怎么用？”即可检查完整的页面、异步任务、远程模型和引用返回流程。

本机 `localhost:8000` 是本地网页/API；远程 `localhost:8000` 是 LLM 服务。两者位于不同电脑，端口不冲突；SSH 转发的是 6001。

## 6. 日常重启与故障定位

| 情况 | 操作 |
|---|---|
| 所有服务已经运行，只是重新打开网页 | 直接打开 `/app` |
| 只关闭了 SSH 窗口 B | 确认旧 RAG 接口已退出，再执行第 3 步；不重复启动原有依赖 |
| 本地电脑重启，AutoDL 依赖仍运行 | 执行第 3、4、5 步 |
| AutoDL 实例重新开机 | 从第 2 步启动远程依赖，再执行第 3、4、5 步 |
| 修改了本地应用代码 | 第 4 步添加 `--build` |
| 修改了 `scripts/rag_gateway.py` | 上传新文件，再重启远程接口；无需重建模型或索引 |

若显示 `rag: unavailable`：

1. 检查窗口 B 是否仍在运行，以及是否出现远程异常。
2. 在远程窗口 A 检查模型 `curl -fsS http://127.0.0.1:8000/v1/models`。
3. 在本机 CMD 检查隧道 `curl.exe -fsS http://127.0.0.1:6001/health/ready`，预期包含 `status: ready`。
4. 查看本地日志：

```cmd
cd /d "E:\Users\PC\Desktop\maie6000c"
docker --context default compose logs --tail 100 api ai worker
```

若出现 `Address already in use` 或转发失败，先确认是否已有窗口 B 或服务在使用 6001，不要同时重复运行启动命令。若显存不足，检查是否仍在运行旧的 `infer.py` 或重复启动了模型进程。

## 7. 停止工程

1. 在窗口 B 按 Ctrl+C，停止 RAG 接口和 SSH 隧道。
2. 在本机工程目录运行 `docker --context default compose stop`，停止本地服务并保留数据。
3. 若不再使用远程 GPU，可通过 AutoDL 控制台关闭实例；这会停止远程模型和数据库等进程。

正常停止或重启无需运行 `docker compose down -v`；该选项会删除本地数据库数据卷。
