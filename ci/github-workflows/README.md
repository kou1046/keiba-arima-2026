# ci/github-workflows (一時置き場)

この 6 ファイルは本来 `.github/workflows/` 配下に置く GitHub Actions ワークフロー。

PR を作成した token に `workflow` scope が無く `.github/workflows/` へ直接 push できなかったため、
ここに退避している。**マージ前に `.github/workflows/` へ移動すること** (どちらか):

```bash
git mv ci/github-workflows/*.yml .github/workflows/
git rm -r ci/github-workflows  # README ごと不要なら
```

- ローカルから push する場合は `workflow` scope 付きの PAT が必要。
- もしくは GitHub web UI で各ファイルを `.github/workflows/` に新規作成して貼り付け。

composite action (`.github/actions/run-scrape-job/`) は既にリポジトリに含まれている。
