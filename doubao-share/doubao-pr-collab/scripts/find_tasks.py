#!/usr/bin/env python3
"""拉取 PR 评论，解析首行收件人，按回复痕迹去重，输出发给豆包的未回复任务编号。

用法:
  find_tasks.py owner/repo PR_NUM --token-file 路径

输出:
  每行 "<comment_id> <任务编号>"；无任务时打印 NONE。
检测到 [定稿] 时额外打印 FINAL 到 stderr。
"""
import argparse
import json
import re
import sys
import urllib.request

MY_ALIASES = ['doubao-oops618', '给豆包']          # 收件人别名（兼容新旧协议）
TASK_RE = r'T\d{8}-\d+[A-Za-z0-9]*'                # 任务编号，如 T20261015-02 / T20261013-06b


def api(owner, repo, path, token):
    url = 'https://api.github.com/repos/{}/{}{}'.format(owner, repo, path)
    req = urllib.request.Request(url, headers={
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/vnd.github+json',
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser(description='找出 PR 留言板中发给豆包的未回复任务')
    ap.add_argument('owner_repo', help='owner/repo')
    ap.add_argument('pr_num', type=int, help='PR 编号')
    ap.add_argument('--token-file', required=True, help='GitHub 令牌文件路径')
    args = ap.parse_args()

    owner, repo = args.owner_repo.split('/')
    token = open(args.token_file).read().strip()
    comments = api(owner, repo, '/issues/{}/comments?per_page=100'.format(args.pr_num), token)

    # 收集我方所有回评：(任务编号 or None, 发布时间)
    # 协议格式：首行 [claude-oops618]/[给Claude]，正文里带「回复 TYYYYMMDD-NN」
    replies = []
    for c in comments:
        first = c['body'].strip().split('\n')[0]
        if re.match(r'^\s*\[(claude-oops618|给Claude)\]', first):
            m = re.search(TASK_RE, c['body'])
            tid = m.group(0) if m else None
            replies.append((tid, c['created_at']))

    def is_replied(comment, task_id):
        # 必须同时满足：① 回评带**同一**任务编号（避免跨任务误判）；
        # ② 回评发布时间**晚于**本评论（避免把上一轮的旧回评当成这一轮追问的回复）
        for rid, rt in replies:
            if rid == task_id and rt > comment['created_at']:
                return True
        return False

    tasks = []
    last_task = None  # 无编号评论（如"第 N 轮追问"）继承本 PR 最近出现的任务编号
    for c in comments:
        first = c['body'].strip().split('\n')[0]
        bracket = re.match(r'^\s*\[([^\]]+)\]', first)
        if not bracket:
            continue
        addrs = [a.strip() for a in bracket.group(1).split(';')]
        if not any(a in addrs for a in MY_ALIASES):
            continue
        m = re.search(TASK_RE, c['body'])
        if m:
            last_task = m.group(0)
        task_id = m.group(0) if m else last_task
        if not task_id:
            continue
        if not is_replied(c, task_id):
            tasks.append((c['id'], task_id))

    if any('[定稿]' in c['body'] for c in comments):
        print('FINAL', file=sys.stderr)

    if tasks:
        for cid, task in tasks:
            print('{} {}'.format(cid, task))
    else:
        print('NONE')


if __name__ == '__main__':
    main()
