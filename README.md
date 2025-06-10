# TA-assistant

## zip ファイルの作成

PandA にアップロードする zip ファイルには、本アプリ固有の `allocation.json` や `detailed_grades.json` が含まれていてはいけない。
`-x` オプションで JSON ファイルを除外すること。

```shell
zip ~/Downloads/test.zip -r 課題名/ -x 課題名/*.json
```
