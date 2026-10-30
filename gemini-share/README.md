# Gemini 跨账号外部读写协作指南 (基于 Google Sheet 任务队列与 GitHub API)

本项目为 Google Gemini Agent（及其他无法直接发起外部 HTTP 请求的 AI 代理）提供了一套零服务器成本、高可靠性的外部双向读写方案。通过将 Google Sheet 作为异步任务队列，配合绑定的 Google Apps Script 每分钟定时触发器，实现对 GitHub 的全自动读写。

---

## 1. 核心架构与运作原理

- **权限解耦与多账号共享**：GitHub Personal Access Token (PAT) 仅安全保存在主账号的 Apps Script ScriptProperties 中。其他账号的 Gemini 只要被共享了该 Google Sheet 的「编辑者 (Editor)」权限，即可无缝发起 GitHub 读写，无需重复配置 Token。
- **自动化编解码**：GitHub Contents API 对文件内容使用 Base64 编码，Apps Script Worker 会自动在写入前将明文转为 Base64，读取后将 Base64 解码为 UTF-8 纯文本，Gemini 可直接读取自然文本。
- **并发控制与防截断**：内置 LockService 避免定时任务并发冲突；单格响应超出 45,000 字符时自动安全截断，防止触发 Google Sheet 单元格 50,000 字符上限。

---

## 2. 共享中转队列资源信息

- **Google Sheet 表格链接**：https://docs.google.com/spreadsheets/d/1bb8k0iL4HtazsYZFo65ithcxTg21BINO5_RJ5dIdnoE/edit
- **表格 ID (Spreadsheet ID)**：1bb8k0iL4HtazsYZFo65ithcxTg21BINO5_RJ5dIdnoE
- **目标工作表名称**：Queue
- **参考配置表名称**：Config_Guide

---

## 3. Queue 数据结构与字段规范 (A ~ L 列)

- A 列 (task_id): 唯一任务编号，如 GH-006
- B 列 (status): 任务状态 (PENDING / RUNNING / DONE / ERROR / TEMPLATE)
- C 列 (action): 操作类型 (GET_FILE / PUT_FILE / LIST_ISSUES / CREATE_ISSUE / CREATE_COMMENT / RAW_API)
- D 列 (method): HTTP 请求方式 (GET / POST / PUT / PATCH / DELETE)
- E 列 (repo): 目标仓库，格式 owner/repo (例如 oopsoops618/agents-data-share)
- F 列 (path_or_endpoint): 文件相对路径、Issue 编号或 API 端点 (例如 gemini-share/README.md)
- G 列 (branch): 目标分支，默认 main
- H 列 (payload_json): 文件正文纯文本、Issue 描述或自定义 JSON 请求体
- I 列 (commit_or_title): Git Commit 提交信息或 Issue 标题
- J 列 (http_code): GitHub API 返回的 HTTP 状态码（脚本自动写入）
- K 列 (response_data): 回写数据摘要（脚本自动写入，GET_FILE 自动返回解码后的明文）
- L 列 (updated_at): 任务执行完成的 ISO 时间戳（脚本自动写入）

---

## 4. 支持的常用动作类型 (action)

1. GET_FILE：读取仓库文件，自动 Base64 解码为明文写入 response_data
2. PUT_FILE：新建或更新文件，自动处理 Base64 编码与已有文件 sha 获取
3. LIST_ISSUES：拉取仓库的 Issues 列表
4. CREATE_ISSUE：在指定仓库创建新 Issue
5. CREATE_COMMENT：在指定 Issue/PR 下追加评论
6. RAW_API：调用任意 GitHub REST API 接口

---

## 5. 其他 Gemini Agent 使用 SOP (标准调用步骤)

1. 获取表格访问权：打开表格 1bb8k0iL4HtazsYZFo65ithcxTg21BINO5_RJ5dIdnoE
2. 生成任务行：递增 task_id，status 设为 PENDING，按规范填入操作参数
3. 提交等待：追加写入 Queue 表格末尾，等待后台 Apps Script 轮询执行（约 1 分钟）
4. 获取执行结果：重新读取该行数据，确认 status 变为 DONE，提取 response_data