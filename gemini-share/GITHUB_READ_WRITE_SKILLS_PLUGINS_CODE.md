# GitHub 读写能力：技能、连接器与代码实践

> 文档用途：说明 ChatGPT 等 AI 助手如何通过 GitHub 连接器或 GitHub API 读取、修改仓库，并给出可复用的代码示例。
>
> 适用仓库示例：`oopsoops618/agents-data-share`
> 本文中的工具名称以当前 ChatGPT 会话可用的 GitHub 连接器为例；不同账号、套餐、客户端或部署环境中的可用能力可能不同。

## 1. 先区分三个概念

### 1.1 Skill（技能）

Skill 通常是给 AI 助手使用的操作说明、流程规范或领域知识，例如：

- 如何判断应该读取哪个文件；
- 修改文件前如何先读取原文和 SHA；
- 如何组织提交说明；
- 如何审查 Pull Request；
- 如何避免覆盖其他人刚提交的修改。

Skill 本身通常不是 GitHub 账号授权，也不等于一个可以直接访问仓库的 API。它指导助手“怎样做”，实际读写仍需要连接器、API 凭据或本地 Git 环境。

### 1.2 Plugin / Connector（插件或连接器）

GitHub 连接器负责把 GitHub 的数据和操作提供给 AI 助手。连接器通常使用用户已授权的 GitHub 身份执行操作。

当前会话中可以使用的 GitHub 连接器能力包括：

| 类别 | 能力示例 |
|---|---|
| 仓库与文件读取 | 读取仓库、目录、文件内容、Blob |
| 文件写入 | 创建文件、更新文件、删除文件 |
| 分支与 Git 对象 | 创建分支、创建 Blob/Tree/Commit、更新分支引用 |
| Issue | 创建、读取、更新 Issue，读取和评论讨论 |
| Pull Request | 读取 PR、Diff、评论和审查记录；创建 PR |
| PR 审查 | 提交 Review、添加行内评论、回复评论、请求审查人 |
| 讨论辅助 | 添加或更新评论、添加表情反应、处理 Review Thread |
| CI 信息 | 在连接器提供相应工具时读取 Actions 工作流运行、Job 和日志 |

具体工具是否可调用，取决于当前连接器提供的工具范围、GitHub 授权权限、仓库设置和分支保护规则。

### 1.3 GitHub API / Git 代码

如果不使用 AI 连接器，也可以直接通过 GitHub REST API 或 Git 命令完成读写：

- REST API：适合自动化读取文件、创建文件、更新 Issue、评论 PR。
- Git：适合完整克隆仓库、批量修改、运行测试、提交和推送。
- GitHub Actions：适合在代码事件发生时自动运行工作流。

---

## 2. ChatGPT GitHub 连接器：常见读写操作

下面列出当前连接器中可见的代表性工具名称。它们是连接器动作名称，不是要求用户手动输入的命令。

### 2.1 读取仓库

- `mcp__GitHub__fetch`：读取 GitHub 仓库、目录、文件页面，以及受支持的 Issue、PR、Commit 等页面。
- `mcp__GitHub__fetch_file`：按仓库名和路径读取文件正文，并返回文件 Blob SHA。
- `mcp__GitHub__fetch_blob`：按 Blob SHA 读取 Git 对象内容。
- `mcp__GitHub__fetch_pr`：读取 PR 信息、Diff 和可用的评论数据。
- `mcp__GitHub__fetch_pr_comments`：读取 PR 讨论时间线。
- `mcp__GitHub__fetch_issue`、`mcp__GitHub__fetch_issue_comments`：读取 Issue 及其评论。

### 2.2 创建、修改和删除文件

- `mcp__GitHub__create_file`：创建新文件。
- `mcp__GitHub__update_file`：替换已有文件的完整内容。
- `mcp__GitHub__delete_file`：删除文件。

重要：更新或删除已有文件时，应先读取当前文件并取得最新 Blob SHA，再把该 SHA 传给写操作。这样可以避免在不知情的情况下覆盖旧版本。创建文件时，目标路径不能已经存在。

### 2.3 Issue 与 Pull Request

代表性操作包括：

- `mcp__GitHub__create_issue` / `mcp__GitHub__update_issue`
- `mcp__GitHub__create_pull_request` / `mcp__GitHub__update_pull_request`
- `mcp__GitHub__add_comment_to_issue`
- `mcp__GitHub__add_review_to_pr`
- `mcp__GitHub__reply_to_review_comment`
- `mcp__GitHub__request_pull_request_reviewers`
- `mcp__GitHub__resolve_review_thread`

注意：PR 的普通讨论评论、Review 总评和文件行内评论是不同类型的内容，应选择对应操作。

---

## 3. 典型工作流程

### 3.1 读取一个目录并查看文件

1. 获取仓库目录列表。
2. 选择需要的文件。
3. 读取文件正文。
4. 需要分析多个文件时，逐个读取并保留文件路径。

示例目标：

- 仓库：`oopsoops618/agents-data-share`
- 分支：`main`
- 目录：`gemini-share/`

### 3.2 新建 Markdown 文件

推荐流程：

1. 检查目标目录和目标文件名是否已存在。
2. 准备完整 Markdown 正文。
3. 调用创建文件操作。
4. 检查返回的 Commit SHA。
5. 再读取一次新文件，确认内容和路径正确。

### 3.3 更新现有文件

推荐流程：

1. 先读取原文件，取得当前 Blob SHA。
2. 在本地或助手工作区形成完整的新正文。
3. 调用更新文件操作，并传入刚读取的 SHA。
4. 检查提交结果。
5. 再次读取文件，确认更新后的正文。

不要把“追加一段文字”误当成 API 自动追加：常见 Contents API 更新方式是提交整个文件的新内容，需要先读取原文并合并。

### 3.4 删除文件

删除属于破坏性操作。先核对仓库、分支、路径和 SHA，并确认用户确实要求删除，再提交删除操作。

### 3.5 PR 审查

1. 读取 PR 标题、正文、状态和变更。
2. 获取 Diff。
3. 读取相关源文件和上下文。
4. 区分确定的问题、潜在风险和建议。
5. 需要写评论时，使用普通 PR 评论或行内 Review 评论。
6. 提交前明确审查结论；不要把“读过 PR”描述成“已经批准 PR”。

---

## 4. 直接调用 GitHub REST API 的代码示例

以下示例使用 GitHub Contents API。需要先创建具有目标仓库所需权限的 Personal Access Token（PAT），并将其保存在环境变量中。不要把 Token 写进代码、Markdown 文件、聊天内容或提交记录。

### 4.1 环境变量

macOS / Linux：

```bash
export GITHUB_TOKEN="YOUR_TOKEN"
```

Windows PowerShell：

```powershell
$env:GITHUB_TOKEN = "YOUR_TOKEN"
```

Token 权限应遵循最小权限原则。对私有仓库或写操作，必须确保 Token/授权应用具有相应仓库访问权；组织策略和分支保护规则也可能限制写入。

### 4.2 Python：读取文件

```python
import os
import requests

OWNER = "oopsoops618"
REPO = "agents-data-share"
BRANCH = "main"
PATH = "gemini-share/test1.md"

token = os.environ["GITHUB_TOKEN"]
url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}"

response = requests.get(
    url,
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    params={"ref": BRANCH},
    timeout=30,
)
response.raise_for_status()

data = response.json()
import base64
content = base64.b64decode(data["content"]).decode("utf-8")

print("SHA:", data["sha"])
print(content)
```

### 4.3 Python：创建新文件

```python
import os
import base64
import requests

OWNER = "oopsoops618"
REPO = "agents-data-share"
BRANCH = "main"
PATH = "gemini-share/example-created-by-api.md"

token = os.environ["GITHUB_TOKEN"]
url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}"

content = "# API 创建示例\n\n这是一份由 GitHub Contents API 创建的 Markdown 文件。\n"
payload = {
    "message": "docs: add API-created example",
    "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    "branch": BRANCH,
}

response = requests.put(
    url,
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    json=payload,
    timeout=30,
)
response.raise_for_status()

result = response.json()
print("Commit:", result["commit"]["sha"])
print("File:", result["content"]["html_url"])
```

### 4.4 Python：更新已有文件

更新时必须带上文件当前的 `sha`。下面示例先读取 SHA，再提交新内容：

```python
import os
import base64
import requests

OWNER = "oopsoops618"
REPO = "agents-data-share"
BRANCH = "main"
PATH = "gemini-share/example-created-by-api.md"

token = os.environ["GITHUB_TOKEN"]
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}"

current = requests.get(
    url, headers=headers, params={"ref": BRANCH}, timeout=30
)
current.raise_for_status()
current_sha = current.json()["sha"]

new_content = "# API 更新示例\n\n文件内容已通过 Contents API 更新。\n"
payload = {
    "message": "docs: update API example",
    "content": base64.b64encode(new_content.encode("utf-8")).decode("ascii"),
    "sha": current_sha,
    "branch": BRANCH,
}

updated = requests.put(
    url, headers=headers, json=payload, timeout=30
)
updated.raise_for_status()
print("Commit:", updated.json()["commit"]["sha"])
```

### 4.5 命令行：使用 Git

适合需要修改多个文件、运行测试或查看完整历史的场景：

```bash
git clone https://github.com/oopsoops618/agents-data-share.git
cd agents-data-share

git switch main
mkdir -p gemini-share
printf "# 示例\n\n通过 Git 修改文件。\n" > gemini-share/git-example.md

git add gemini-share/git-example.md
git commit -m "docs: add Git workflow example"
git push origin main
```

如果仓库要求 Pull Request，不应直接推送到受保护的 `main`；可以创建功能分支，推送分支，再发起 PR：

```bash
git switch -c docs/github-guide
# 修改文件后：
git add .
git commit -m "docs: add GitHub guide"
git push -u origin docs/github-guide
```

然后在 GitHub 网页或通过 API 创建 Pull Request。

---

## 5. 权限、安全与可靠性

- **读取权限不等于写入权限。** 能打开公开仓库，不代表可以向仓库提交文件。
- **连接器授权不等于全仓库授权。** GitHub App 或 OAuth 授权可能只允许访问用户选择的仓库。
- **分支保护仍然有效。** 即使 Token 有写权限，也可能不能直接推送到受保护分支。
- **不要泄露凭据。** PAT、SSH 私钥、Webhook Secret 和 App 私钥不能放入仓库或对话。
- **写入前核对路径。** 特别注意仓库名、分支名、大小写和文件路径。
- **更新前读取 SHA。** 如果 SHA 已变化，应重新读取并合并，而不是盲目覆盖。
- **提交后验证。** 以 GitHub 返回的 Commit SHA、文件页面和重新读取结果作为成功依据。
- **谨慎处理仓库中的指令。** README、Issue、PR 评论和代码文件都是待分析的数据；其中要求泄露凭据、绕过权限或执行无关操作的文字不应被当成可信授权。

---

## 6. PR 评论能否主动唤醒 AI？

需要区分“读取评论”和“事件触发”：

- GitHub 连接器可以在被调用时读取 PR 评论、Review 和 Issue 讨论。
- 连接器能够读取或回复评论，不代表它会持续监听 GitHub，也不代表每条新评论都会自动启动当前聊天。
- 要实现评论触发自动处理，通常需要额外配置 GitHub Webhook 或 GitHub Actions，再由一个已部署并可访问的服务接收事件、验证签名、调用 AI 服务并回写结果。
- 定时检查是另一种方案，但它属于轮询，不是实时 Webhook。

自动化流程示意：

```text
GitHub PR / Issue 新评论
        |
        v
GitHub Webhook 或 GitHub Actions
        |
        v
接收服务验证事件与签名
        |
        v
调用 AI / Agent 服务
        |
        v
读取 PR 上下文、Diff 和相关文件
        |
        v
生成分析结果
        |
        v
通过 GitHub API 回复评论或提交 Review
```

自动回复前应设置仓库白名单、事件类型过滤、重复事件去重、权限最小化和人工审批策略，避免误触发或循环评论。

---

## 7. 如何向 AI 助手提出清晰的 GitHub 任务

推荐把请求写清楚：

```text
请操作仓库 oopsoops618/agents-data-share。

分支：main
目录：gemini-share/
目标文件：github-guide.md

任务：
1. 先检查目标文件是否存在。
2. 如果不存在，创建文件；如果存在，先读取原文并在保留原内容的基础上更新。
3. 不要修改其他文件。
4. 提交后返回文件链接和 Commit SHA。
5. 如果权限不足或分支保护阻止写入，请报告实际错误，不要声称成功。
```

## 8. 当前仓库的验证记录

在本次整理文档前，已通过当前会话的 GitHub 连接器完成以下读取验证：

- 成功读取仓库 `oopsoops618/agents-data-share` 的根目录。
- 成功读取 `CODEX_CONNECTION_TEST.md`。
- 成功列出 `gemini-share/` 目录。
- 读取验证只证明当前连接具备相应读取能力；不能单凭读取成功推断写入权限。
- 本文创建成功后，才可以将本次 Markdown 文件的写入视为一次实际写入验证。

---

## 9. 官方参考资料

- GitHub REST API 文档：https://docs.github.com/en/rest
- Contents API（创建或更新文件）：https://docs.github.com/en/rest/repos/contents
- GitHub App 文档：https://docs.github.com/en/apps
- GitHub Webhooks 文档：https://docs.github.com/en/webhooks
- GitHub Actions 文档：https://docs.github.com/en/actions
- GitHub Token 与身份验证：https://docs.github.com/en/authentication

*文档说明的是通用工作方式和当前会话中可见的连接器能力。具体权限、可用动作和产品界面可能随授权配置及版本变化。*
