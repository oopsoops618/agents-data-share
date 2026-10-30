#!/usr/bin/env python3
"""把交付物推到 doubao/ 分支（contents API），输出可贴评论的 blob 链接。

用法:
  push_card.py owner/repo --token-file 路径 --branch doubao/xxx --path cards/x.md --content-file 本地文件 [--dry-run]

分支不存在时自动基于默认分支创建；文件已存在时自动带 sha 更新。
"""
import argparse
import base64
import json
import sys
import urllib.error
import urllib.request


def api(owner, repo, path, token, method='GET', data=None, accept='application/vnd.github+json'):
    url = 'https://api.github.com/repos/{}/{}{}'.format(owner, repo, path)
    headers = {'Authorization': 'Bearer ' + token, 'Accept': accept}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, method=method, headers=headers, data=body)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser(description='推交付物到 doubao/ 分支并输出 blob 链接')
    ap.add_argument('owner_repo', help='owner/repo')
    ap.add_argument('--token-file', required=True, help='GitHub 令牌文件路径')
    ap.add_argument('--branch', required=True, help='分支名，如 doubao/story-review-cards')
    ap.add_argument('--path', required=True, help='分支内路径，如 cards/I_place_features.md')
    ap.add_argument('--content-file', required=True, help='本地内容文件路径')
    ap.add_argument('--dry-run', action='store_true', help='只打印目标不执行')
    args = ap.parse_args()

    owner, repo = args.owner_repo.split('/')

    if args.dry_run:
        print('[dry-run] 将写入 {}/{}:{}/{}'.format(owner, repo, args.branch, args.path))
        return

    token = open(args.token_file).read().strip()
    content = base64.b64encode(open(args.content_file, 'rb').read()).decode()

    # 1) 分支是否存在；不存在则基于默认分支创建
    try:
        api(owner, repo, '/git/ref/heads/' + args.branch, token)
        exists = True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            exists = False
        else:
            raise
    if not exists:
        default = api(owner, repo, '', token)['default_branch']
        sha = api(owner, repo, '/git/ref/heads/' + default, token)['object']['sha']
        api(owner, repo, '/git/refs', token, method='POST',
            data={'ref': 'refs/heads/' + args.branch, 'sha': sha})
        print('分支 {} 已创建（基于 {}）'.format(args.branch, default), file=sys.stderr)

    # 2) PUT 文件；已存在则带 sha 更新
    put = {'message': 'doubao: {}'.format(args.path), 'content': content, 'branch': args.branch}
    try:
        api(owner, repo, '/contents/' + args.path, token, method='PUT', data=put)
    except urllib.error.HTTPError as e:
        if e.code in (409, 422):
            sha = api(owner, repo, '/contents/{}?ref={}'.format(args.path, args.branch), token)['sha']
            put['sha'] = sha
            api(owner, repo, '/contents/' + args.path, token, method='PUT', data=put)
        else:
            raise

    print('https://github.com/{}/{}/blob/{}/{}'.format(owner, repo, args.branch, args.path))


if __name__ == '__main__':
    main()
