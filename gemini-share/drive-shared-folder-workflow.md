# Gemini 跨账号向指定 Google Drive 共享文件夹归档图片/文件工作流指南

本文档提供两种将 Gemini 生成的无损 PNG / JPG 图片或文档自动归档至任意 Google Drive 共享文件夹（如 `CDS工作室`）的工作流：
- **模式 A（极简推荐：文件名暗号法 / 零表格写入）**：Gemini **只负责把带前缀名的图片传到个人网盘根目录，不调用任何写表格工具**，彻底避开 `sheets_agent` 的确认卡片！
- **模式 B（表格队列法：`COPY_TO_DRIVE`）**：适合在主账号（表格唯一所有者）下统一调度，或把表格在各账号下独立复制一份使用。

---

## 一、模式 A：文件名暗号法（零表格写入，彻底无确认卡）

### 1. 原理说明
实测表明，Gemini 调用 `drive:create_file`（不填 `parent_id`）将图片上传至**当前账号自己的个人网盘根目录**时，不会触发任何确认卡片；唯一触发「共享电子表格的建议编辑」卡片的是第二步调用 `sheets_agent` 修改多人共享表格。

因此，直接省去“写表格”这一步：
1. **Gemini 仅上传文件并带上暗号前缀**：
   - 归档到 `CDS工作室`：将上传文件名命名为 **`[TO_CDS] 文件名.png`**（例如 `[TO_CDS] sleeping_astronaut_cat.png`）。
   - 归档到任意其他共享文件夹：将上传文件名命名为 **`[TO_DRIVE_<目标文件夹ID>] 文件名.png`**（例如 `[TO_DRIVE_19w2sIfrgC_bgGZRfRzMnebwe1pRjzcm_] cat.png`）。
2. **后台脚本每分钟自动巡检**：
   - Apps Script 的 `scanDriveTaggedFiles()` 每分钟自动搜索网盘中名字含 `[TO_` 的文件；
   - 自动剥离 `[TO_...]` 前缀，将无损原图复制到对应共享文件夹，自动清理个人网盘根目录下的临时文件，并在 `Queue` 表末尾补一行 `AUTO-xxxxxx` 的 `DONE` 归档日志。

### 2. 模式 A 标准提示词模板（推荐日常直接使用）

> **提示词模板（零表格写入版）**：
> 请帮我生成一张【在此描述图片内容】的 PNG 图片，然后直接调用 `drive:create_file`（使用 `file://` 路径，**不要填写 `parent_id`**）将该图片上传到我个人网盘的根目录：
> - 如果目标是存入 CDS工作室，请将上传的 `title`（文件名）严格命名为：`[TO_CDS] creative_cat.png`
> - 如果目标是存入其他共享文件夹，请将 `title` 命名为：`[TO_DRIVE_目标文件夹ID] creative_cat.png`
> 
> 上传完成后直接告诉我就行，**不需要修改或写入任何 Google Sheet 表格**。

---

## 二、多账号部署架构说明（为什么建议每个账号部署/复制一份脚本）

由于每个 Google 账号的「个人网盘根目录」是相互隔离的（A 账号的脚本无法直接读取 B 账号私人根目录下的未共享文件），且多人共享同一张表格会触发「共享电子表格的建议编辑」卡片，多账号协作时有两种最佳实践：

1. **方案 1（每个账号各自拥有一份私有表格与脚本 —— 最稳妥）**：
   - 在每个账号（如 `gemini1` ~ `gemini4`）自己的云端硬盘里各自建一份**不对外共享**的 `GitHub_Task_Queue` 表格（或者哪怕不建表格，只在该账号的 [script.google.com](https://script.google.com) 新建一个独立脚本粘贴 `github_task_queue_worker.js` 并运行 `installEveryMinuteTrigger`）。
   - 这样每个账号的脚本既能直接读取自己网盘根目录下的 `[TO_CDS]` 暂存图片并搬运到 `CDS工作室`，写自己的私有表格时也**绝对不会弹出“共享电子表格”确认卡**。
2. **方案 2（共用一个中转投递文件夹）**：
   - 如果只想在主账号跑一个脚本，可以让其他账号把 `[TO_CDS]` 图片或表格放在与主账号共享的缓冲区，但需遵守平台对共享目录的确认机制。因此**方案 1（各账号独立运行触发器 + 模式 A 文件名暗号法）**是体验最丝滑的零点击组合。

---

## 三、模式 B：表格队列法 (`COPY_TO_DRIVE`)

当你在表格所有者账号下操作，或需要通过队列批量调度外部 URL / GitHub Raw 图片时，可在 `Queue` 表追加一行：
- `action`: `COPY_TO_DRIVE`
- `method`: `PUT`
- `path_or_endpoint`: 目标共享文件夹 ID（如 `19w2sIfrgC_bgGZRfRzMnebwe1pRjzcm_`）
- `commit_or_title`: 保存文件名（如 `creative_cat.png`）
- `payload_json`: 支持 `drive:<file_id>`（复制后自动清理根目录暂存）、`drive_keep:<file_id>`（保留原文件）、`https://...`（外部图片 URL）或 `draft:<draft_id>`。