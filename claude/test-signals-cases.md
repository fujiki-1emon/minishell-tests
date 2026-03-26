# シグナルテストケース定義書

評価基準: bash と同じ挙動であれば PASS

---

## 同値クラスと境界値の設計方針

### Ctrl+C 同値クラス

| クラス | 条件 | 同値の根拠 |
|---|---|---|
| EC-C1 | readline 待機中（空行 / 非空行） | どちらも ^C + 改行 + プロンプト再表示 |
| EC-C2 | 外部コマンド実行中（単体 / パイプライン） | どちらも $?=130 + プロンプト |
| EC-C3 | heredoc 入力中 | heredoc 中断 + $?=130 |
| EC-C4 | readline 中の Ctrl+\ | 完全無視 |
| EC-C5 | コマンド実行中の Ctrl+\ | Quit メッセージ + $?=131 |

### Ctrl+C 境界値

| ケース | 境界の意味 |
|---|---|
| BC-C1 | 空行と非空行の境（1 文字入力状態） |
| BC-C2 | 連続 Ctrl+C（1 回と 2 回の境） |
| BC-C3 | コマンド終了直後の Ctrl+C（実行済み/待機の境） |
| BC-C4 | Ctrl+C 直後に Enter（exit_code が 130 のまま引き継がれるか） |

### Ctrl+D 同値クラス

| クラス | 条件 | 同値の根拠 |
|---|---|---|
| EC-D1 | readline 待機中・空行 | "exit" + シェル終了 |
| EC-D2 | readline 待機中・入力途中 | カーソル位置の文字削除（EOF ではない） |
| EC-D3 | heredoc 入力中・空行 | heredoc 終了（デリミタなし） |
| EC-D4 | 非インタラクティブ stdin EOF | シェル終了（メッセージなし） |

### Ctrl+D 境界値

| ケース | 境界の意味 |
|---|---|
| BC-D1 | 1 文字入力後 Ctrl+D（最小非空行） |
| BC-D2 | 連続 Ctrl+D・空行（1 回目で exit） |
| BC-D3 | 終了後の $? 値（直前コマンドを引き継ぐか） |
| BC-D4 | heredoc 入力途中 Ctrl+D（部分行の扱い） |

---

## テストケース一覧

### Ctrl+C テスト

| TC-ID | 分類 | フェーズ | 操作 | 期待（bash） |
|---|---|---|---|---|
| CC-01 | EC-C1 | readline 待機・空行 | Ctrl+C | `^C` 表示 + 改行 + プロンプト、$?=130 |
| CC-02 | EC-C1 | readline 待機・非空行 | `hello` 入力後 Ctrl+C | `^C` 表示 + 改行 + プロンプト（入力クリア）、$?=130 |
| CC-03 | EC-C2 | 外部コマンド単体 | `sleep 10` 後 Ctrl+C | 改行 + プロンプト、$?=130 |
| CC-04 | EC-C2 | パイプライン | `sleep 10 \| cat` 後 Ctrl+C | 改行 + プロンプト、$?=130 |
| CC-05 | EC-C3 | heredoc 入力中 | `cat <<EOF` 後 Ctrl+C | 改行 + プロンプト、$?=130 |
| CC-06 | EC-C4 | readline 待機・Ctrl+\ | Ctrl+\ | 何も変化しない（無視） |
| CC-07 | EC-C5 | コマンド実行中・Ctrl+\ | `sleep 10` 後 Ctrl+\ | `Quit` 表示、$?=131 |
| CC-08 | BC-C1 | readline 待機・1 文字 | `a` 入力後 Ctrl+C | `^C` + 改行 + プロンプト（`a` 消える）、$?=130 |
| CC-09 | BC-C2 | readline 連続 Ctrl+C | Ctrl+C × 2 | 2 回とも `^C` + 改行 + プロンプト |
| CC-10 | BC-C3 | コマンド終了直後 | `echo ok` 実行後 Ctrl+C | `^C` + 改行 + プロンプト、$?=130 |
| CC-11 | BC-C4 | Ctrl+C 後に Enter | Ctrl+C → Enter | $?=130 のまま（空行実行は $? を変えない） |

### Ctrl+D テスト

| TC-ID | 分類 | フェーズ | 操作 | 期待（bash） |
|---|---|---|---|---|
| CD-01 | EC-D1 | readline 待機・空行 | Ctrl+D | `exit` 表示 + シェル終了 |
| CD-02 | EC-D2 | readline 待機・入力途中 | `hello` 入力後 Ctrl+D | `o` が削除される（bash: カーソル位置の 1 文字削除） |
| CD-03 | EC-D3 | heredoc 入力中・空行 | `cat <<EOF` → Ctrl+D | heredoc 終了（警告なし or あり）、コマンド実行 |
| CD-04 | EC-D4 | 非インタラクティブ | stdin を /dev/null にリダイレクト | 即時終了（"exit" なし） |
| CD-05 | BC-D1 | readline 待機・1 文字 | `a` 入力後 Ctrl+D | `a` が削除される |
| CD-06 | BC-D2 | 連続 Ctrl+D・空行 | 空行で Ctrl+D × 2 | 1 回目で終了（2 回目は届かない） |
| CD-07 | BC-D3 | 終了時の $? | `echo 42` 後 Ctrl+D | 終了コード = 0（最後のコマンドの $?） |
| CD-08 | BC-D4 | heredoc 入力途中 Ctrl+D | `cat <<EOF` → `hel` → Ctrl+D | bash: 行フラッシュ（1 回目）→ 次 Ctrl+D で終了 |

---

## テストケースの十分性

### カバレッジ分析

**フェーズカバレッジ（Ctrl+C）**

| フェーズ | 対応 TC |
|---|---|
| readline 待機・空行 | CC-01 |
| readline 待機・非空行 | CC-02, CC-08 |
| 外部コマンド実行中・単体 | CC-03 |
| 外部コマンド実行中・パイプ | CC-04 |
| heredoc 入力中 | CC-05 |
| readline 中の SIGQUIT | CC-06 |
| コマンド実行中の SIGQUIT | CC-07 |
| 境界：最小入力 | CC-08 |
| 境界：連続送信 | CC-09 |
| 境界：直後の状態 | CC-10, CC-11 |

**フェーズカバレッジ（Ctrl+D）**

| フェーズ | 対応 TC |
|---|---|
| readline 待機・空行（EOT） | CD-01 |
| readline 待機・非空行（文字削除） | CD-02, CD-05 |
| heredoc readline 中 | CD-03, CD-08 |
| 非インタラクティブ | CD-04 |
| 境界：最小入力 | CD-05 |
| 境界：連続送信 | CD-06 |
| 境界：終了コード引き継ぎ | CD-07 |
| 境界：行中途 Ctrl+D | CD-08 |

### 十分性の根拠

1. **同値クラス網羅**: 各クラスから代表ケースを 1 つ以上選択している
2. **境界値網羅**: 各クラスの境界（最小・最大・遷移点）を個別にテストしている
3. **フェーズ網羅**: signal-phases-report.md の全フェーズ（lex/parse/expand 中は
   外部コマンドテストで間接的にカバー）を対象としている
4. **未カバーフェーズ**: lex/parse/expand 処理中の Ctrl+C（実質テスト不能）、
   プロセスグループ一斉配送（パイプテストで代替）、exit 処理中（CD-06 で近似）
