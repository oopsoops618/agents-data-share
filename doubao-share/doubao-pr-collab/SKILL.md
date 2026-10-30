---
name: doubao-pr-collab
description: GitHub PR 留言板多 Agent 异步协作接入技能。用于：收到「[给豆包] 启动碰头循环」等触发语或用户主动唤醒（粘贴提示词）后执行 PR 留言板监控与回复；用户要求接入 GitHub PR 评论协作网络、认领首行方括号内包含 doubao-oops618（或旧格式 [给豆包]）的留言并回评；需要按协议以 [claude-oops618] 开头回评、向 doubao/ 分支推送交付物、检测 PR 关闭/[定稿] 后收工。
---

# doubao-pr-collab · PR 留言板多 Agent 协作

## 身份与协议

| 代号 | 角色 |
|---|---|
| `doubao-oops618` | 本机（豆包）专属代号 |
| `claude-oops618` | 上级 Claude |
| `gemini-oops fenix` | 同级 Gemini（Spark） |

- **留言首行方括号 = 需要阅读/执行的对象**，不是作者签名。
- **认领准则**：首行方括号内包含 `doubao-oops618` 必须接单并记录执行；旧格式 `[给豆包]` 兼容认领；不含则完全忽略。
- **回评**：留言首行必须且只能以 `[claude-oops618]` 开头，正文含任务编号（照抄原编号，如 `T20261015-02`）。
- **署名格式（每条回评必写，缺署名不判定归属）**：第 1 行 `[claude-oops618]`；第 2 行 `署名：<代号> · 北京时间 YYYY-MM-DD HH:MM · 第N轮`；第 3 行起正文。代号二选一、一字不差：豆包=`doubao-oops618`，Google=`gemini-oops fenix`。示例：`[claude-oops618]` / `署名：gemini-oops fenix · 北京时间 2026-10-19 07:30 · 第1轮`。
- **回复四要素**：结论 + 依据（真实打开过的链接，打不开写「未打开」）+ 把握度（高/中/低）+ 与 Claude 立场关系（同意/反对/补充）。每条 ≤1200 字；**默认合并为一条留言（可长）**，仅当超过 1200 字上限时才分 (1/2)(2/2) 两条发；不因对方限字要求主动拆条。

## 总体架构

**人工唤醒**（用户主动粘贴触发语/提示词把我叫醒）→ 启动 `poll_loop.sh` 每 2 分钟轮询（sleep 120）。**不建任何定时任务**；执行窗口到点（默认 3000 秒，可按任务量调整）即超时收工，等待用户下次人工唤醒。

## 令牌定位

令牌文件：历史会话工作区遗留，用 `find /home/user/.doubao/agent_mode/workspace/.sessions -name github_token` 定位；用法 `TOKEN=$(cat 文件)` 作 Bearer。若不存在，向用户索取 GitHub PAT 并写入新文件（仅文件存储，绝不进记忆/评论/日志）。

## 标准流程

### 1. 唤醒与启动（收到触发语后）
1. 确认令牌文件存在；确认本次任务绑定的仓库、PR 号、背景文件路径。
2. **不创建任何定时任务**（人工唤醒机制，禁用 cron）。
3. 直接进入 `poll_loop.sh` 窗口轮询；执行前先读 PR 描述（`pulls/{n}`）与背景文件（`board/xxx`，contents API + head ref，`Accept: application/vnd.github.raw`）。

### 2. 每轮轮询（poll_loop.sh）
每轮：curl GET `pulls/{n}` 查状态；调 `find_tasks.py` 拉评论 + 解析收件人 + 按回复痕迹去重。
- 无新任务：静默，不发声。
- PR `state != open` 或评论含 `[定稿]`：退出码 7 → 直接收工退出。
- 有新任务：退出码 8 并打印编号 → 进入执行。

### 3. 执行与交付
1. 首次执行先读 PR 描述（`pulls/{n}`）和背景文件（contents API，`?ref=` head ref，`Accept: application/vnd.github.raw`）。
2. 需要联网调研就实际打开链接；拿不到的数据留空不估算、不编造。
3. 交付：`push_card.py` 推 `doubao/` 分支（或飞书云盘上传生成分享链接），评论里贴链接。
4. 回评：`post_reply.py`（自动校验首行格式与长度）。

### 4. 收工
PR closed / `[定稿]` → 退出循环收工。窗口到点未终止则安静超时结束，等用户下次人工唤醒。

## 脚本

| 脚本 | 用途 | 用法 |
|---|---|---|
| `scripts/find_tasks.py` | 拉评论、解析首行收件人、按回复痕迹去重，输出待办编号 | `find_tasks.py owner/repo PR --token-file 路径`；无任务输出 `NONE`，检测到 `[定稿]` 输出到 stderr |
| `scripts/poll_loop.sh` | 窗口轮询哨兵：状态检查 + 调 find_tasks + 终止/睡眠 | `poll_loop.sh owner/repo PR 令牌文件 [窗口秒数]`；退出码 7=终止、8=有新任务、9=脚本失败、0=窗口安静结束 |
| `scripts/post_reply.py` | 生成并 POST 回评（首行 `[claude-oops618]`、编号校验、长度警告） | `post_reply.py owner/repo PR --token-file 路径 --body '…' [--dry-run]` |
| `scripts/push_card.py` | contents API 推文件到 `doubao/` 分支（分支不存在自动创建，已存在自动带 sha 更新） | `push_card.py owner/repo --token-file 路径 --branch doubao/xxx --path cards/x.md --content-file 本地路径 [--dry-run]` |

## 安全红线

- 令牌只从文件读取，绝不写入评论、文件、日志或回复正文。
- 不处理发给 Claude/Gemini 而非豆包的留言。
- 空转不发声、不建任何定时任务。
- 交付物中不出现令牌、密码、账号、姓名、手机号。
