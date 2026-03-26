# minishell シグナルフェーズ分析レポート

## フェーズ一覧

| # | フェーズ | プロセス | 備考 |
|---|---|---|---|
| 1 | readline 入力待ち | 親 | インタラクティブハンドラ有効 |
| 2 | lex/parse/expand 処理中 | 親 | readline 非アクティブで interactive ハンドラが残る危険 |
| 3 | fork 前（子なし） | 親 | exec ハンドラ設定済みだが誰も殺せない |
| 4 | パイプライン fork 間 | 親 | 子1は起動済み、子2以降は未起動 |
| 5 | waitpid 待機中 | 親 | EINTR で中断される可能性あり |
| 6 | waitpid リターン後〜sig_set_interactive 前 | 親 | exec ハンドラのまま g_sig がセットされている可能性 |
| 7 | builtin 実行中（親） | 親 | readline 非アクティブ、fork なし |
| 8 | heredoc 入力待ち（親） | 親 | exec_single_parent 経由の場合 |
| 9 | heredoc 入力待ち（子） | 子 | ayusa モデル: fork した子が読む |
| 10 | fork 直後〜sig_set_child 前 | 子 | 親のハンドラ（sig_handler_exec）を継承 |
| 11 | sig_set_child 後〜execve 前 | 子 | SIG_DFL だがリダイレクト・PATH 探索が走っている |
| 12 | 外部コマンド実行中（execve 後） | 子 | SIG_DFL、シグナルで終了 |
| 13 | Ctrl+D / exit 処理中 | 親 | readline が NULL を返した後の終了フェーズ |
| 14 | 非インタラクティブモード | 親 | isatty=false、全フェーズに影響 |
| 15 | プロセスグループへの一斉配送 | 親+子 | Ctrl+C は全プロセスに同時送信される境界 |

---

## 特に見落とされやすい境界

### フェーズ2: lex/parse/expand 中
readline がリターンしてから `exec_pipeline` に入るまでの計算フェーズ。
`sig_handler_interactive` が生きたまま。Ctrl+C が届くと `rl_redisplay()` が
呼ばれるが readline はアクティブではなく、内部状態が壊れる可能性がある。

### フェーズ3: fork 前（子なし）
`sig_set_exec_parent()` 設定後、まだ `fork()` していない状態。
SIGINT が届いても誰も kill されない。

### フェーズ10: fork 直後の子プロセス
`fork()` 直後、子は親のシグナルハンドラ（`sig_handler_exec`）をそのまま継承する。
`sig_set_exec_child()` を呼ぶまでの僅かな間、SIGINT が来ても記録されるだけ。

### フェーズ4: パイプライン途中の fork 間
`ls | grep foo | wc -l` で子を1つずつ fork していく途中で Ctrl+C が来た場合、
すでに fork した子は死に、まだ fork していないコマンドは実行されない。
`wait_all` が不完全な子セットを待つことになる。

### フェーズ13: Ctrl+D / exit 処理中
readline が NULL を返した後、`env_free`・`clear_history` 等の終了処理中にも
シグナルは届き得る。独立したフェーズとして扱う必要がある。

### フェーズ14: 非インタラクティブモード
`isatty(STDIN_FILENO) == false` の場合（`./minishell < script.sh` 等）。
readline は使われても画面表示は行わず、「プロンプト再描画」は意味をなさない。
bash は非インタラクティブ時に SIGINT を SIG_DFL にする。

### フェーズ15: プロセスグループへの一斉配送
Ctrl+C はフォアグラウンド**プロセスグループ全体**に同時送信される。
「親だけ受け取る」「子だけ受け取る」ではなく、全プロセスが同時に受信する。

```
Ctrl+C 押下
    ↓
カーネルがプロセスグループに SIGINT を一斉送信
    ├── 親プロセス（shell）→ sig_handler_exec が受け取る
    ├── 子プロセス1（cmd1）→ SIG_DFL → 死ぬ
    └── 子プロセス2（cmd2）→ SIG_DFL → 死ぬ
```

---

## 各フェーズの信号状態まとめ

```
readline 待機        exec 前後         子プロセス        heredoc
    ↓                   ↓                  ↓               ↓
sig_set_interactive  sig_set_exec_parent  sig_set_exec_child  sig_set_heredoc
SIGINT→handler       SIGINT→recorder     SIGINT→DFL       SIGINT→recorder
SIGQUIT→IGN          SIGQUIT→IGN         SIGQUIT→DFL      SIGQUIT→IGN
```
