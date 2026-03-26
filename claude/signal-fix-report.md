# Signal (Ctrl+C) 修正レポート

## 問題の概要

`claude/` の Ctrl+C 挙動が ayusa-minishell と異なっていた。原因は3つ。

---

## 問題1: Ctrl+C で `^C` が表示されない

### 変更前
```c
static void sig_handler_interactive(int sig)
{
    g_sig = sig;
    rl_on_new_line();
    write(STDOUT_FILENO, "\n", 1);   // "\n" だけ
    rl_replace_line("", 0);
    rl_done = 1;                      // readline を強制リターン
}
```

### 変更後
```c
static void sig_handler_interactive(int sig)
{
    g_sig = sig;
    write(STDOUT_FILENO, "^C\n", 3); // "^C\n" を明示 write
    rl_on_new_line();
    rl_replace_line("", 0);
    rl_redisplay();                   // プロンプトを再描画して待機継続
}
```

### 説明

`rl_catch_signals = 0` を設定すると readline はシグナルを自前で処理しない。
そのため `^C` の表示もシェル側で明示的に行う必要がある。
bash・ayusa はどちらも `"^C\n"` を write している。

---

## 問題2: `rl_done = 1` で readline が強制リターンする

`rl_done = 1` を設定すると readline が即座に `""` を返す。

- Ctrl+C のたびに readline がリターン → ループが1周する
- `flush_sigint` という専用関数で後始末が必要な複雑な制御フローになっていた

ayusa は `rl_redisplay()` を使い、readline を終了させずプロンプトを再描画するだけ。
readline は次のユーザー入力（Enter 等）まで待機を継続するシンプルな設計。

### loop.c の変更

`flush_sigint` を削除し、ayusa と同じパターンに統一した。

```c
// 変更後 ms_loop
while (1)
{
    sig_set_interactive();        // ループ先頭で必ず設定
    line = read_prompt(sh);
    if (g_sig == SIGINT)          // readline リターン後に確認
    {
        sh->exit_code = 130;
        g_sig = 0;
    }
    if (!line)
        break ;
    ...
}
```

---

## 問題3: parent builtin 実行中に `rl_redisplay()` が呼ばれる危険

`exec_pipeline` は `cd`・`export` などの parent builtin 実行時に
シグナルハンドラを切り替えていなかった。

```
readline から返る
 → exec_pipeline (cd を実行中)
    ↑ この間、SIGINT は sig_handler_interactive のまま
```

この状態で Ctrl+C が来ると、readline が動いていないのに `rl_redisplay()` が
呼ばれる。readline の内部状態が壊れたり、表示が崩れる可能性があった。

ayusa は `exec_ast` 呼び出し前に必ず `set_signal_executing()` を呼んで、
実行中は readline 関数を触らないハンドラに切り替えている。

### 修正: signal_exec.c

```c
// 変更前
void sig_set_exec_parent(void)
{
    signal(SIGQUIT, SIG_IGN);
    signal(SIGINT, SIG_IGN);    // 完全無視
}
```

```c
// 変更後
static void sig_handler_exec(int sig)
{
    g_sig = sig;                // g_sig に記録するだけ（readline 関数は呼ばない）
}

void sig_set_exec_parent(void)
{
    signal(SIGQUIT, SIG_IGN);
    signal(SIGINT, sig_handler_exec);
}
```

### 修正: exec.c

`exec_pipeline` の先頭と末尾にシグナル切り替えを追加。
parent builtin・空コマンド・forked pipeline のすべての経路をカバー。

```c
int exec_pipeline(t_shell *sh, t_pipeline *pl)
{
    int ret;

    sig_set_exec_parent();       // 実行前に切り替え
    if (...)
        ret = exec_single_parent(...);
    else if (...)
        ret = apply_redirects(...);
    else
        ret = exec_forked_pipeline(...);
    if (g_sig == SIGINT)         // parent builtin が中断された場合
    {
        write(STDERR_FILENO, "\n", 1);
        ret = 130;
    }
    sig_set_interactive();       // 実行後に復元（g_sig もリセット）
    return (ret);
}
```

---

## 根本原因の一言まとめ

`rl_done = 1` で「readline をリターンさせて後で処理する」という設計にしたため、
「実行中は別のハンドラに切り替える」という基本が抜けていた。

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `src/signal/signal.c` | `"^C\n"` を write、`rl_done = 1` → `rl_redisplay()` |
| `src/signal/signal_exec.c` | SIG_IGN → `sig_handler_exec`（g_sig を記録するだけ） |
| `src/exec/exec.c` | `exec_pipeline` に実行前後のシグナル切り替えを追加 |
| `src/core/loop.c` | `flush_sigint` 削除、`sig_set_interactive()` をループ先頭に移動 |
| `src/core/main.c` | `rl_catch_signals = 0` を追加 |
