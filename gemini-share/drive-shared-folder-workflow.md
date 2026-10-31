# Gemini 跨账号向指定 Google Drive 共享文件夹归档图片/文件工作流指南 (纯表格队列架构)

本文档说明如何通过统一的 **Google Sheet 异步任务队列 (`COPY_TO_DRIVE` 动作)**，由后台 Apps Script 每分钟定时巡检，将无损 PNG 图片或任意文件自动归档至指定的 Google Drive 共享文件夹（如 `CDS工作室` 或任何其他协作目录）。

---

## 一、为什么坚持统一采用「表格任务队列」？

1. **严格的状态机与幂等防重**：
   任务遵循 `PENDING` -> `RUNNING` -> `DONE` / `ERROR` 完整生命周期。
   - 只有状态为 `PENDING` 的任务才会被消费；
   - 执行开始时立即置为 `RUNNING`，防止上一分钟未跑完时并发重复消费；
   - 执行完成后记录时间戳与 HTTP 状态码，**彻底杜绝重复存储**。
2. **端到端可追溯与可排查**：
   每一笔搬运、归档、新建文件的目标路径、原图大小、执行时间、报错信息都在 `Queue` 表中一目了然。
3. **架构统一**：
   无论是向 GitHub 提交代码、读取仓库文件、上传图片，还是跨云端硬盘文件夹复制文件，全套动作全部收敛于同一张表。

---

## 二、多账号零弹窗最佳实践（每个账号复制一份独立私有表格）

在之前的实测中，另一个账号之所以会弹出「共享电子表格的建议编辑（更改归属于您）」卡片，是因为那个账号是以**外部协作者 (Editor)** 身份修改别人拥有的共享表格，触发了 Google Workspace 的协同审计提示。

**彻底杜绝任何确认弹窗的标准做法**：
1. **各账号独立建表（私有化）**：
   为每个日常使用的 Google 账号（如 `gemini1` ~ `gemini4`）在其个人网盘中各自创建一份独立的 `GitHub_Task_Queue` 表格，**不将此表格共享给其他账号**。
2. **各账号部署一份独立触发器**：
   在各自表格的 Apps Script 中粘贴 `github_task_queue_worker.js`，并运行一次 `installEveryMinuteTrigger`。
3. **效果**：
   - 每个账号的 Gemini 修改的是**自己名下的私有表格**，属于本人高信誉操作，**绝无“更改归属于您”的协同建议卡**；
   - 每个账号的脚本能够无障碍读取自己个人网盘根目录下的图片并搬运至目标共享文件夹（如 `CDS工作室`），搬运完成后自动清理根目录临时文件；
   - 所有任务状态井然有序，完全自主可控。

---

## 三、核心工作流步骤（无损 PNG 直传）

1. **生成图片并上传至个人网盘根目录**：
   - Gemini 在沙箱中生成无损 PNG 原图（如 `creative_cat.png`）。
   - 调用 `drive:create_file`（使用 `file://` 路径，**不填写 `parent_id`**，不直接写入外部共享文件夹），记录返回的 `file_id`。
2. **向私有任务队列提交 `COPY_TO_DRIVE` 任务**：
   - 在该账号的 `GitHub_Task_Queue` 表格追加一行：
     - `task_id`: `GH-xxx`
     - `status`: `PENDING`
     - `action`: `COPY_TO_DRIVE`
     - `method`: `PUT`
     - `path_or_endpoint`: 目标共享文件夹 ID（例如 `CDS工作室` 填 `19w2sIfrgC_bgGZRfRzMnebwe1pRjzcm_`）
     - `commit_or_title`: 保存的文件名（例如 `creative_cat.png`）
     - `payload_json`: `drive:<刚才拿到的file_id>`
3. **后台脚本自动复制并清理**：
   - 后台定时器扫描到 `PENDING` 任务后，通过 `file.makeCopy()` 将无损原图复制到目标文件夹，自动将个人网盘根目录的暂存文件移入回收站（保持根目录整洁），并把结果回写为 `DONE`。

---

## 四、写给 Gemini 的标准提示词模板

在任何独立配置好的账号下，对 Gemini 发送以下指令即可实现全程无人值守：

> **提示词模板**：
> 请帮我生成一张【在此描述图片内容】的 PNG 图片，并按以下两步归档到共享文件夹（目标文件夹 ID：`19w2sIfrgC_bgGZRfRzMnebwe1pRjzcm_`，保存文件名：`creative_cat.png`）：
> 1. 调用 `drive:create_file`（使用 `file://` 路径，**不要填写 `parent_id`**）将该 PNG 图片上传到我个人网盘的根目录，记录返回的 `file_id`；
> 2. 打开我网盘中的 `GitHub_Task_Queue` 表格，在 `Queue` 表末尾追加一行任务：
>    - `status`: `PENDING`
>    - `action`: `COPY_TO_DRIVE`
>    - `method`: `PUT`
>    - `path_or_endpoint`: `19w2sIfrgC_bgGZRfRzMnebwe1pRjzcm_`
>    - `commit_or_title`: `creative_cat.png`
>    - `payload_json`: `drive:<刚才拿到的file_id>`
> 
> 请直接完成上述两步写入，完成后告知我任务 ID 即可。