# doubao-share

豆包本机 GitHub 协作技能与脚本归档。

## 内容

- `doubao-pr-collab/` — GitHub PR 留言板多 Agent 异步协作技能（用户自建）
  - `SKILL.md` — 技能说明（身份协议、令牌定位、标准流程、安全红线）
  - `scripts/find_tasks.py` — 拉取 PR 评论、解析收件人、按回复痕迹去重
  - `scripts/poll_loop.sh` — 窗口轮询哨兵（每 2 分钟检查 PR 状态与新任务）
  - `scripts/post_reply.py` — 生成并 POST PR 回评（首行/署名/长度校验）
  - `scripts/push_card.py` — 推送交付物到 `doubao/` 分支并输出 blob 链接

## 说明

- 所有脚本令牌均通过 `--token-file` 参数在运行时传入，仓库内不含任何密钥。
- 系统预设技能与平台插件内部配置不在本仓库归档范围内。
