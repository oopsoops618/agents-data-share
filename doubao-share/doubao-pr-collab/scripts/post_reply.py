#!/usr/bin/env python3
"""生成并 POST PR 回评。首行必须为 [claude-oops618]，正文含任务编号。

用法:
  post_reply.py owner/repo PR_NUM --token-file 路径 --body '…' [--dry-run]

--dry-run: 只校验并打印统计，不实际发送。
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request

TASK_RE = r'T\d{8}-\d+[A-Za-z0-9]*'
MAX_PLAIN = 1200  # 去链接后的字数上限


def main():
    ap = argparse.ArgumentParser(description='向 PR 留言板 POST 回评')
    ap.add_argument('owner_repo', help='owner/repo')
    ap.add_argument('pr_num', type=int, help='PR 编号')
    ap.add_argument('--token-file', required=True, help='GitHub 令牌文件路径')
    ap.add_argument('--body', required=True, help='评论正文（首行 [claude-oops618] 回复 T{编号}）')
    ap.add_argument('--dry-run', action='store_true', help='只校验不发送')
    args = ap.parse_args()

    owner, repo = args.owner_repo.split('/')
    body = args.body.strip()

    if not re.match(r'^\[claude-oops618\]', body):
        sys.exit('错误：首行必须以 [claude-oops618] 开头')
    if not re.search(TASK_RE, body):
        sys.exit('错误：正文缺少任务编号（T{编号}）')
    lines = body.split('\n')
    if len(lines) < 2 or not re.match(r'^署名：(doubao-oops618|gemini-oops fenix) · 北京时间 \d{4}-\d{2}-\d{2} \d{2}:\d{2} · 第\d+轮$', lines[1].strip()):
        sys.exit('错误：第2行署名格式不符（应为：署名：<代号> · 北京时间 YYYY-MM-DD HH:MM · 第N轮；代号=doubao-oops618 或 gemini-oops fenix）')

    plain = re.sub(r'https?://\S+', '', body)
    if len(plain) > MAX_PLAIN:
        print('警告：去链接后 {} 字 > {}，建议分 (1/2)(2/2) 两条发'.format(len(plain), MAX_PLAIN), file=sys.stderr)

    if args.dry_run:
        print('[dry-run] 将 POST 到 {}/{}#{}，去链接 {} 字'.format(owner, repo, args.pr_num, len(plain)))
        return

    token = open(args.token_file).read().strip()
    url = 'https://api.github.com/repos/{}/{}/issues/{}/comments'.format(owner, repo, args.pr_num)
    req = urllib.request.Request(url, method='POST', headers={
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/vnd.github+json',
        'Content-Type': 'application/json',
    }, data=json.dumps({'body': body}).encode())
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode())
            print('✅ HTTP {} 评论ID: {}'.format(r.status, d['id']))
    except urllib.error.HTTPError as e:
        print('❌ {}: {}'.format(e.code, e.read().decode()), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
