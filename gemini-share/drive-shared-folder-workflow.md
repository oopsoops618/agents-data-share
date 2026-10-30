# Gemini 跨账号向指定 Google Drive 共享文件夹归档图片/文件工作流指南

本文档说明如何利用 **Gmail 草稿箱 (`gmail:create_draft`) + `GitHub_Task_Queue` 队列 (`COPY_TO_DRIVE` 动作)**，由后台 Apps Script 每分钟定时巡检并将图片或文件自动转存至任意指定的 Google Drive 共享文件夹（如 `CDS工作室` 或其他协作目录）。

---

## 一、流程可行性与核心技术细节

由于 Gemini 的 `gmail:create_draft` 工具仅接收纯文本参数（`subject`, `body`, `htmlBody`），**不支持直接挂载二进制附件 (`attachments`)**，因此无法直接往草稿里塞原始 `.png`/`.jpg` 文件并生成“图片附件 ID”。

为使该流程 100% 跑通，完整的技术闭环设计如下：

1. **沙箱图片转 Base64 写入草稿**：
   - Gemini 在本地沙箱生成或压缩图片（建议控制在 15KB~25KB 以内的 JPEG/PNG，使 Base64 长度在 20,000~33,000 字符以内，避免超出单次工具调用输出上限；若图片更大可拆分为多封草稿 `draft:id1,id2`）。
   - 调用 `gmail:create_draft`，将主题设为 `[DRIVE_RELAY] 文件名.jpg`，正文 `body` 填入图片的纯 Base64 字符串，拿到返回的 **`draft_id`**。
2. **向 `GitHub_Task_Queue` 提交 `COPY_TO_DRIVE` 任务**：
   - 在 `Queue` 表末尾追加一行 `PENDING` 任务：
     - `action`: 填 **`COPY_TO_DRIVE`**
     - `path_or_endpoint`: 填**目标共享文件夹的 Folder ID**（通用设计，不限于 CDS；例如 `CDS工作室` 为 `19w2sIfrgC_bgGZRfRzMnebwe1pRjzcm_`）
     - `commit_or_title`: 填**目标文件名**（如 `creative_cat.jpg`）
     - `payload_json`: 填 **`draft:<draft_id>`**（或填 `draft:latest` 自动抓取最新一封主题含 `[DRIVE_RELAY]` 的草稿）
3. **Apps Script 每分钟巡检还原并清理**：
   - 后台定时器扫描到 `COPY_TO_DRIVE` 任务后，通过 `GmailApp` 读取对应草稿正文中的 Base64 字符串，解码还原为二进制图片文件（`Blob`），直接调用 `DriveApp.getFolderById(folderId).createFile(blob)` 存入目标共享文件夹，随后自动删除该临时草稿，并将新文件的 `file_id` 与 `view_url` 回写到 `response_data`。

---

## 二、`COPY_TO_DRIVE` 支持的 4 种来源模式 (`payload_json`)

除了 Gmail 草稿中转外，`COPY_TO_DRIVE` 还同时兼容另外 3 种来源，按需选用：

| 来源模式 | `payload_json` 填写格式 | 适用场景说明 |
| :--- | :--- | :--- |
| **1. Gmail 草稿中转（默认推荐）** | `draft:<draft_id>` 或 `draft:latest`（支持多段拼接 `draft:id1,id2`） | 通过 `gmail:create_draft` 写入 Base64 文本后转存，转存成功后自动删除草稿 |
| **2. 单元格内联 Base64** | `base64:<Base64字符串>` 或 `data:image/jpeg;base64,...` | 适合 `<25KB` 的轻量图片（Base64 小于 35,000 字符），无需经过 Gmail 草稿，一步到位 |
| **3. 外部或 GitHub Raw URL** | `https://...` | 直接将网络图片或已上传到 GitHub 的 Raw 图片转存至目标共享网盘文件夹 |
| **4. 个人网盘文件 ID** | `drive:<file_id>` | 将个人网盘已有的文件复制到目标共享文件夹 |

---

## 三、写给 Gemini 的标准提示词模板 (Prompt Template)

当你需要任何账号下的 Gemini 生成图片并存入指定共享文件夹时，可直接使用以下提示词：

> **提示词模板**：
> 请帮我生成一张【在此描述图片内容】，并按以下流程存入共享文件夹（目标文件夹 ID：`19w2sIfrgC_bgGZRfRzMnebwe1pRjzcm_`，保存文件名：`creative_cat.jpg`）：
> 1. 在沙箱中将图片保存并优化为 20KB 以内的 JPEG，转为纯 Base64 字符串；
> 2. 调用 `gmail:create_draft` 创建一封草稿，主题设为 `[DRIVE_RELAY] creative_cat.jpg`，正文 `body` 仅填入该 Base64 字符串，记录返回的 `draft_id`；
> 3. 打开网盘中的 `GitHub_Task_Queue (外部读写任务队列)`（表格 ID：`1bb8k0iL4HtazsYZFo65ithcxTg21BINO5_RJ5dIdnoE`），在 `Queue` 表末尾追加一行任务：
>    - `status`: `PENDING`
>    - `action`: `COPY_TO_DRIVE`
>    - `method`: `PUT`
>    - `path_or_endpoint`: `19w2sIfrgC_bgGZRfRzMnebwe1pRjzcm_`（或其他目标共享文件夹 ID）
>    - `commit_or_title`: `creative_cat.jpg`
>    - `payload_json`: `draft:<刚才拿到的draft_id>`（若未拿到具体 ID 可填 `draft:latest`）