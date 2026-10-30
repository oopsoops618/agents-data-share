# GitHub Task Queue 代理通用技能规范 (SKILL.md)

本文件定义了 Google Gemini Agent（及兼容此模式的各类 AI 代理）通过 Google Sheet 异步任务队列与 Apps Script 定时器突破环境网络隔离、对 GitHub 执行双向读写的标准技能规范。

---

## 一、技能元数据 (Skill Metadata)

- **技能名称**：`github-task-queue`
- **主要用途**：突破网络限制，全自动读写与操作外部 GitHub 仓库
- **触发场景**：用户提到「GitHub 队列」「操作 GitHub」「提交到 GitHub」「从 GitHub 读取」「上传图片到 GitHub」「跑一下 GitHub 任务」等需求时自动触发。
- **依赖工具**：Google Drive（读写中转表格与存取图片）

---

## 二、底层运行基础设施

- **中转表格**：[GitHub_Task_Queue (外部读写任务队列)](https://docs.google.com/spreadsheets/d/1bb8k0iL4HtazsYZFo65ithcxTg21BINO5_RJ5dIdnoE/edit)
- **表格 ID**：`1bb8k0iL4HtazsYZFo65ithcxTg21BINO5_RJ5dIdnoE`
- **核心工作表**：`Queue`（任务调度队列）、`Config_Guide`（规范手册）
- **后台 Worker**：Google Apps Script（已安全托管 GitHub Token，每 1 分钟自动轮询一次）

---

## 三、队列动作指令集 (Action Reference)

1. `GET_FILE`：读取 GitHub 仓库文件（自动将 Base64 解码为 UTF-8 明文并返回 SHA）
2. `PUT_FILE`：创建或更新文本/代码文件（自动探测现有 SHA 并执行 Base64 编码提交）
3. `PUT_IMAGE`：上传图片或二进制文件（通过 `drive:FILE_ID` 或外部 URL，彻底突破表格单格 50,000 字符上限）
4. `LIST_ISSUES`：拉取仓库的 Issues 列表（支持 `?state=open` 等过滤参数）
5. `CREATE_ISSUE`：在目标仓库创建新 Issue（支持标题与 Markdown 正文）
6. `CREATE_COMMENT`：在指定 Issue/PR 下追加评论
7. `RAW_API`：调用任意 GitHub REST API（如查询当前账号、触发 Workflow 等）

---

## 四、Agent 自动化执行 SOP (Standard Operating Procedure)

1. **查号取序**：读取 `Queue` 表，查阅当前已有任务的最大编号，递增生成下一个 `task_id`（如 `GH-010`）。
2. **装载指令**：在 `Queue` 末尾追加一行，参数对齐 A~I 列，将 `status` 设为 `PENDING`。
3. **调度等待**：提示用户后台定时器每分钟自动扫描；用户亦可在 Apps Script 点击 `processTaskQueue` 即时消费。
4. **回读闭环**：重新读取该行，确认 `status` 变为 `DONE`（或检查 `ERROR` 详情），提取 `response_data` 输出给用户。