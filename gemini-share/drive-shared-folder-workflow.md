# Gemini 跨账号向指定 Google Drive 共享文件夹归档图片/文件工作流指南

本文档说明如何利用 **个人网盘根目录暂存 (`drive:create_file`) + `GitHub_Task_Queue` 队列 (`COPY_TO_DRIVE` 动作)**，由后台 Apps Script 每分钟定时巡检并将无损 PNG 图片或任意文件自动归档至指定的 Google Drive 共享文件夹（如 `CDS工作室` 或任何其他协作目录）。

---

## 一、核心工作流设计（个人网盘根目录中转法）

无需手动转换 Base64，原生支持任意大小的无损 `.png`、`.jpg`、`.webp`、`.pdf` 等文件：

1. **上传至个人网盘根目录（获取 `file_id`）**：
   - Gemini 在沙箱中生成图片或文件（如 `creative_cat.png`）。
   - 调用 `drive:create_file`（传入 `base64_content: "file:///沙箱路径/creative_cat.png"`, `mime_type: "image/png"`, `title: "creative_cat.png"`），**不填写 `parent_id`**（默认直接存入当前账号自己的网盘根目录，不直接写入外部他人共享文件夹），记录返回的 **`file_id`**。
2. **向 `GitHub_Task_Queue` 提交 `COPY_TO_DRIVE` 任务**：
   - 在 [GitHub_Task_Queue (外部读写任务队列)](https://docs.google.com/spreadsheets/d/1bb8k0iL4HtazsYZFo65ithcxTg21BINO5_RJ5dIdnoE/edit) 的 `Queue` 表末尾追加一行 `PENDING` 任务：
     - `action`: 填 **`COPY_TO_DRIVE`**
     - `method`: 填 **`PUT`**
     - `path_or_endpoint`: 填**目标共享文件夹的 Folder ID**（通用设计，不限于 CDS；例如 `CDS工作室` 为 `19w2sIfrgC_bgGZRfRzMnebwe1pRjzcm_`）
     - `commit_or_title`: 填**目标保存文件名**（如 `creative_cat.png`）
     - `payload_json`: 填 **`drive:<刚才拿到的file_id>`**（若希望复制后在个人网盘根目录也保留一份原文件，可填 `drive_keep:<file_id>`）
3. **Apps Script 每分钟巡检复制并自动清理根目录**：
   - 后台定时器扫描到 `COPY_TO_DRIVE` 任务后，通过 `DriveApp.getFileById(fileId).makeCopy(fileName, targetFolder)` 将无损原文件直接复制到目标共享文件夹。
   - 复制成功后，脚本会自动将个人网盘根目录下的临时暂存文件移入回收站（`setTrashed(true)`），保持个人网盘根目录整洁，并将共享文件夹中新文件的 `file_id` 与 `view_url` 回写到 `response_data`。

---

## 二、`COPY_TO_DRIVE` 支持的来源格式 (`payload_json`)

| 优先级 | 来源模式 | `payload_json` 填写格式 | 适用场景说明 |
| :---: | :--- | :--- | :--- |
| **首选** | **个人网盘根目录文件 ID** | `drive:<file_id>`（自动清理根目录暂存）或 `drive_keep:<file_id>`（保留原文件） | **无需转 Base64**，支持任意大小的无损 PNG / 高清大图与各类文档 |
| 备选 1 | **外部或 GitHub Raw URL** | `https://...` | 直接将网络图片或已上传到 GitHub 的 Raw 图片转存至目标共享网盘文件夹 |
| 备选 2 | **Gmail 草稿中转** | `draft:<draft_id>` 或 `draft:latest` | 兼容通过 Gmail 草稿正文传输小体积 Base64 数据的场景，转存后自动删除草稿 |
| 备选 3 | **单元格内联 Base64** | `base64:<Base64字符串>` | 适合 `<25KB` 的微型图标或小图 |

---

## 三、写给 Gemini 的标准提示词模板 (Prompt Template)

平时需要任何账号下的 Gemini 生成 PNG 图片并存入指定共享文件夹时，直接复制以下提示词即可：

> **提示词模板**：
> 请帮我生成一张【在此描述图片内容】的 PNG 图片，并按以下两步归档到共享文件夹（目标文件夹 ID：`19w2sIfrgC_bgGZRfRzMnebwe1pRjzcm_`，保存文件名：`creative_cat.png`）：
> 1. 调用 `drive:create_file`（使用 `file://` 路径，**不要填写 `parent_id`**）将该 PNG 图片先上传到我个人网盘的根目录，记录返回的 `file_id`；
> 2. 打开网盘中的 `GitHub_Task_Queue (外部读写任务队列)`（表格 ID：`1bb8k0iL4HtazsYZFo65ithcxTg21BINO5_RJ5dIdnoE`），在 `Queue` 表末尾追加一行任务：
>    - `status`: `PENDING`
>    - `action`: `COPY_TO_DRIVE`
>    - `method`: `PUT`
>    - `path_or_endpoint`: `19w2sIfrgC_bgGZRfRzMnebwe1pRjzcm_`（或其他目标共享文件夹 ID）
>    - `commit_or_title`: `creative_cat.png`
>    - `payload_json`: `drive:<刚才拿到的file_id>`