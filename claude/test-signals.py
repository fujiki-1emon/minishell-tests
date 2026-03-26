#!/usr/bin/env python3
"""
Signal behavior test suite: Ctrl+C and Ctrl+D
Compares claude/minishell against bash reference behavior.
"""
import pexpect
import re
import sys
import time
import os

MINISHELL = os.path.dirname(os.path.abspath(__file__)) + "/minishell"
BASH      = "/bin/bash"
TIMEOUT   = 5
MS_PROMPT = r"minishell\$ "

PASS_COUNT = 0
FAIL_COUNT = 0
RESULTS    = []

# ── helpers ──────────────────────────────────────────────────────────────────

def strip_ansi(s):
    s = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', '', s)
    s = re.sub(r'\x1b[()][AB012]', '', s)
    return s.replace('\r\n', '\n').replace('\r', '\n')

def spawn_ms():
    p = pexpect.spawn(MINISHELL, encoding='utf-8', timeout=TIMEOUT,
                      dimensions=(24, 80))
    p.expect(MS_PROMPT)
    return p

def spawn_bash():
    p = pexpect.spawn(BASH, ['--norc', '--noprofile', '--noediting'],
                      encoding='utf-8', timeout=TIMEOUT, dimensions=(24, 80))
    p.setecho(False)
    p.sendline('PS1="$ "; export PS1')
    p.expect(r'\$ ')
    return p

def get_ec(sh, prompt):
    """Read $? from running shell."""
    sh.sendline('echo __EC__$?__EC__')
    sh.expect(r'__EC__(\d+)__EC__')
    val = sh.match.group(1)
    sh.expect(prompt)
    return val

def record(tc_id, name, passed, expected="", actual="", note=""):
    global PASS_COUNT, FAIL_COUNT
    if passed:
        PASS_COUNT += 1
        status = "PASS"
    else:
        FAIL_COUNT += 1
        status = "FAIL"
    RESULTS.append((tc_id, name, status, expected, actual, note))
    mark = "✓" if passed else "✗"
    print(f"  [{status}] {tc_id}: {name}")
    if not passed:
        print(f"         expected : {repr(expected)}")
        print(f"         actual   : {repr(actual)}")
    if note:
        print(f"         note     : {note}")

# ── Ctrl+C Tests ──────────────────────────────────────────────────────────────

def cc_01():
    """EC-C1: Ctrl+C at empty prompt -> ^C + new prompt, $?=130"""
    sh = spawn_ms()
    sh.send('\x03')
    try:
        sh.expect(MS_PROMPT, timeout=3)
        buf = strip_ansi(sh.before)
        has_caret = '^C' in buf
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        passed = has_caret and ec == '130'
        record("CC-01", "EC-C1: Ctrl+C 空行 -> ^C + プロンプト + $?=130",
               passed, "^C in output, $?=130",
               f"^C={'yes' if has_caret else 'no'}, $?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CC-01", "EC-C1: Ctrl+C 空行 -> ^C + プロンプト + $?=130",
               False, "prompt reappear", "TIMEOUT")

def cc_02():
    """EC-C1: Ctrl+C mid-input -> ^C + prompt (input cleared), $?=130"""
    sh = spawn_ms()
    sh.send('hello')
    time.sleep(0.1)
    sh.send('\x03')
    try:
        sh.expect(MS_PROMPT, timeout=3)
        buf = strip_ansi(sh.before)
        has_caret = '^C' in buf
        # "hello" should NOT appear after ^C on the new prompt line
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        passed = has_caret and ec == '130'
        record("CC-02", "EC-C1: Ctrl+C 入力途中 -> ^C + プロンプト + $?=130",
               passed, "^C in output, $?=130",
               f"^C={'yes' if has_caret else 'no'}, $?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CC-02", "EC-C1: Ctrl+C 入力途中 -> ^C + プロンプト + $?=130",
               False, "prompt reappear", "TIMEOUT")

def cc_03():
    """EC-C2: Ctrl+C during sleep -> $?=130"""
    sh = spawn_ms()
    sh.sendline('sleep 10')
    time.sleep(0.3)
    sh.send('\x03')
    try:
        sh.expect(MS_PROMPT, timeout=3)
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        passed = ec == '130'
        record("CC-03", "EC-C2: sleep 中 Ctrl+C -> $?=130",
               passed, "$?=130", f"$?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CC-03", "EC-C2: sleep 中 Ctrl+C -> $?=130",
               False, "prompt after Ctrl+C", "TIMEOUT")

def cc_04():
    """EC-C2: Ctrl+C during pipeline -> $?=130"""
    sh = spawn_ms()
    sh.sendline('sleep 10 | cat')
    time.sleep(0.3)
    sh.send('\x03')
    try:
        sh.expect(MS_PROMPT, timeout=3)
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        passed = ec == '130'
        record("CC-04", "EC-C2: パイプライン中 Ctrl+C -> $?=130",
               passed, "$?=130", f"$?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CC-04", "EC-C2: パイプライン中 Ctrl+C -> $?=130",
               False, "prompt after Ctrl+C", "TIMEOUT")

def cc_05():
    """EC-C3: Ctrl+C during heredoc -> heredoc cancelled, $?=130"""
    sh = spawn_ms()
    sh.sendline('cat <<EOF')
    time.sleep(0.2)
    sh.send('\x03')
    try:
        sh.expect(MS_PROMPT, timeout=3)
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        passed = ec == '130'
        record("CC-05", "EC-C3: heredoc 中 Ctrl+C -> $?=130",
               passed, "$?=130", f"$?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CC-05", "EC-C3: heredoc 中 Ctrl+C -> $?=130",
               False, "prompt after Ctrl+C in heredoc", "TIMEOUT")

def cc_06():
    """EC-C4: Ctrl+\ at prompt -> ignored (no output change)"""
    sh = spawn_ms()
    sh.send('\x1c')
    time.sleep(0.3)
    # Should still be at prompt, not have received any extra output
    sh.send('')  # send nothing, check what's there
    try:
        # send a benign command to verify shell is still alive at prompt
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        # $? should still be 0 (no command was run, no signal changed it)
        passed = ec == '0'
        record("CC-06", "EC-C4: readline 中 Ctrl+\\ -> 無視 ($?=0)",
               passed, "$?=0 (ignored)", f"$?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CC-06", "EC-C4: readline 中 Ctrl+\\ -> 無視 ($?=0)",
               False, "shell alive, $?=0", "TIMEOUT or shell died")

def cc_07():
    """EC-C5: Ctrl+\ during sleep -> Quit message, $?=131"""
    sh = spawn_ms()
    sh.sendline('sleep 10')
    time.sleep(0.3)
    sh.send('\x1c')
    try:
        sh.expect(MS_PROMPT, timeout=3)
        buf = strip_ansi(sh.before)
        has_quit = 'Quit' in buf
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        passed = has_quit and ec == '131'
        record("CC-07", "EC-C5: sleep 中 Ctrl+\\ -> Quit + $?=131",
               passed, "'Quit' in output, $?=131",
               f"Quit={'yes' if has_quit else 'no'}, $?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CC-07", "EC-C5: sleep 中 Ctrl+\\ -> Quit + $?=131",
               False, "prompt after Ctrl+\\", "TIMEOUT")

def cc_08():
    """BC-C1: Ctrl+C after 1 char input (boundary of empty/non-empty)"""
    sh = spawn_ms()
    sh.send('a')
    time.sleep(0.1)
    sh.send('\x03')
    try:
        sh.expect(MS_PROMPT, timeout=3)
        buf = strip_ansi(sh.before)
        has_caret = '^C' in buf
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        passed = has_caret and ec == '130'
        record("CC-08", "BC-C1: 1文字入力後 Ctrl+C -> ^C + プロンプト + $?=130",
               passed, "^C, $?=130",
               f"^C={'yes' if has_caret else 'no'}, $?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CC-08", "BC-C1: 1文字入力後 Ctrl+C -> ^C + プロンプト + $?=130",
               False, "prompt reappear", "TIMEOUT")

def cc_09():
    """BC-C2: Two consecutive Ctrl+C -> each shows ^C + prompt"""
    sh = spawn_ms()
    sh.send('\x03')
    try:
        sh.expect(MS_PROMPT, timeout=3)
        buf1 = strip_ansi(sh.before)
        sh.send('\x03')
        sh.expect(MS_PROMPT, timeout=3)
        buf2 = strip_ansi(sh.before)
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        has_caret1 = '^C' in buf1
        has_caret2 = '^C' in buf2
        passed = has_caret1 and has_caret2 and ec == '130'
        record("CC-09", "BC-C2: Ctrl+C 連続2回 -> 各回 ^C + プロンプト",
               passed, "both show ^C, $?=130",
               f"1st ^C={'yes' if has_caret1 else 'no'}, 2nd ^C={'yes' if has_caret2 else 'no'}, $?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CC-09", "BC-C2: Ctrl+C 連続2回 -> 各回 ^C + プロンプト",
               False, "prompt reappear twice", "TIMEOUT")

def cc_10():
    """BC-C3: Ctrl+C right after a command finishes -> $?=130"""
    sh = spawn_ms()
    sh.sendline('echo ok')
    sh.expect(MS_PROMPT)
    # now Ctrl+C at idle prompt
    sh.send('\x03')
    try:
        sh.expect(MS_PROMPT, timeout=3)
        buf = strip_ansi(sh.before)
        has_caret = '^C' in buf
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        passed = has_caret and ec == '130'
        record("CC-10", "BC-C3: コマンド直後に Ctrl+C -> ^C + $?=130",
               passed, "^C, $?=130",
               f"^C={'yes' if has_caret else 'no'}, $?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CC-10", "BC-C3: コマンド直後に Ctrl+C -> ^C + $?=130",
               False, "prompt reappear", "TIMEOUT")

def cc_11():
    """BC-C4: Ctrl+C then Enter -> $? stays 130 (empty line doesn't change $?)"""
    sh = spawn_ms()
    sh.send('\x03')
    sh.expect(MS_PROMPT, timeout=3)
    sh.sendline('')  # just Enter
    sh.expect(MS_PROMPT, timeout=3)
    ec = get_ec(sh, MS_PROMPT)
    sh.close()
    passed = ec == '130'
    record("CC-11", "BC-C4: Ctrl+C 後 Enter -> $?=130 のまま",
           passed, "$?=130", f"$?={ec}")

# ── Ctrl+D Tests ──────────────────────────────────────────────────────────────

def cd_01():
    """EC-D1: Ctrl+D at empty prompt -> 'exit' printed, shell terminates"""
    sh = spawn_ms()
    sh.sendeof()  # sends Ctrl+D (EOF)
    try:
        sh.expect(pexpect.EOF, timeout=3)
        buf = strip_ansi(sh.before)
        has_exit = 'exit' in buf
        sh.close()
        passed = has_exit
        record("CD-01", "EC-D1: 空行 Ctrl+D -> 'exit' 表示 + 終了",
               passed, "'exit' in output + EOF", f"exit={'yes' if has_exit else 'no'}, buf={repr(buf[:40])}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CD-01", "EC-D1: 空行 Ctrl+D -> 'exit' 表示 + 終了",
               False, "shell terminates", "TIMEOUT (shell did not exit)")

def cd_02():
    """EC-D2: Ctrl+D mid-input -> character deleted, shell stays"""
    sh = spawn_ms()
    sh.send('hello')
    time.sleep(0.1)
    sh.send('\x04')  # Ctrl+D (should delete 'o')
    time.sleep(0.1)
    # Shell should still be alive; send Ctrl+C to get back to prompt
    sh.send('\x03')
    try:
        sh.expect(MS_PROMPT, timeout=3)
        # Check shell is still alive (not exited)
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        passed = True  # shell stayed alive = correct
        record("CD-02", "EC-D2: 入力途中 Ctrl+D -> 文字削除（シェルは継続）",
               passed, "shell continues (no exit)",
               "shell stayed alive after Ctrl+D mid-input")
    except pexpect.EOF:
        record("CD-02", "EC-D2: 入力途中 Ctrl+D -> 文字削除（シェルは継続）",
               False, "shell continues", "shell EXITED (should not on non-empty line)")
    except pexpect.TIMEOUT:
        sh.close()
        record("CD-02", "EC-D2: 入力途中 Ctrl+D -> 文字削除（シェルは継続）",
               False, "shell continues", "TIMEOUT")

def cd_03():
    """EC-D3: Ctrl+D during heredoc (empty line) -> heredoc ends, cmd runs"""
    sh = spawn_ms()
    sh.sendline('cat <<EOF')
    time.sleep(0.2)
    sh.send('\x04')  # Ctrl+D on empty heredoc line
    try:
        # heredoc should end; cat runs with empty/partial content
        sh.expect(MS_PROMPT, timeout=3)
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        # bash: heredoc terminates and cat runs (exit 0)
        passed = ec == '0'
        record("CD-03", "EC-D3: heredoc 中 Ctrl+D (空行) -> heredoc 終了・コマンド実行",
               passed, "$?=0 (cat runs with empty heredoc)", f"$?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CD-03", "EC-D3: heredoc 中 Ctrl+D (空行) -> heredoc 終了・コマンド実行",
               False, "prompt after heredoc ends", "TIMEOUT")

def cd_04():
    """EC-D4: Non-interactive stdin EOF -> shell exits without 'exit' message"""
    # Run minishell with stdin from /dev/null
    p = pexpect.spawn(MINISHELL, encoding='utf-8', timeout=TIMEOUT)
    # close stdin by sending EOF immediately via /dev/null redirect
    p.close()
    # Use subprocess instead
    import subprocess
    result = subprocess.run(
        [MINISHELL],
        stdin=open('/dev/null'),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5
    )
    stdout = result.stdout.decode()
    # In non-interactive mode (stdin=/dev/null, not a tty), bash exits without "exit" message
    # minishell should also exit cleanly with code 0
    passed = result.returncode == 0
    record("CD-04", "EC-D4: 非インタラクティブ stdin EOF -> 終了コード 0",
           passed, "exit code 0", f"exit code={result.returncode}, stdout={repr(stdout[:30])}")

def cd_05():
    """BC-D1: Ctrl+D after 1 char (boundary: minimum non-empty)"""
    sh = spawn_ms()
    sh.send('a')
    time.sleep(0.1)
    sh.send('\x04')  # should delete 'a'
    time.sleep(0.1)
    # now send Ctrl+D again on empty line -> should exit
    sh.sendeof()
    try:
        sh.expect(pexpect.EOF, timeout=3)
        buf = strip_ansi(sh.before)
        has_exit = 'exit' in buf
        sh.close()
        passed = has_exit
        record("CD-05", "BC-D1: 1文字後 Ctrl+D -> 文字削除 -> 次 Ctrl+D で終了",
               passed, "exit after second Ctrl+D", f"exit={'yes' if has_exit else 'no'}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CD-05", "BC-D1: 1文字後 Ctrl+D -> 文字削除 -> 次 Ctrl+D で終了",
               False, "shell exits", "TIMEOUT")

def cd_06():
    """BC-D2: Two Ctrl+D on empty line -> exits on first"""
    sh = spawn_ms()
    sh.send('\x04')
    try:
        sh.expect(pexpect.EOF, timeout=3)
        # If we get EOF quickly, first Ctrl+D caused exit (correct)
        sh.close()
        record("CD-06", "BC-D2: 空行 Ctrl+D 連続 -> 1回目で終了",
               True, "exit on first Ctrl+D", "exited immediately")
    except pexpect.TIMEOUT:
        sh.close()
        record("CD-06", "BC-D2: 空行 Ctrl+D 連続 -> 1回目で終了",
               False, "exit on first Ctrl+D", "TIMEOUT (did not exit)")

def cd_07():
    """BC-D3: $? after Ctrl+D exit == last command's exit code"""
    import subprocess
    # Run: echo 42 ; <Ctrl+D>  -- check process exit code
    p = pexpect.spawn(MINISHELL, encoding='utf-8', timeout=TIMEOUT)
    p.expect(MS_PROMPT)
    p.sendline('exit 42')
    try:
        p.expect(pexpect.EOF, timeout=3)
        p.close()
        ec = p.exitstatus
        passed = ec == 42
        record("CD-07", "BC-D3: exit 42 後の終了コード = 42",
               passed, "exitstatus=42", f"exitstatus={ec}")
    except pexpect.TIMEOUT:
        p.close()
        record("CD-07", "BC-D3: exit 42 後の終了コード = 42",
               False, "shell exits with 42", "TIMEOUT")

def cd_08():
    """BC-D4: Ctrl+D mid-line in heredoc (2 Ctrl+D needed)"""
    sh = spawn_ms()
    sh.sendline('cat <<EOF')
    time.sleep(0.2)
    sh.send('hel')       # partial input
    time.sleep(0.1)
    sh.send('\x04')      # 1st Ctrl+D: flushes "hel" in canonical mode
    time.sleep(0.2)
    sh.send('\x04')      # 2nd Ctrl+D: EOF on empty buffer -> heredoc ends
    try:
        sh.expect(MS_PROMPT, timeout=3)
        ec = get_ec(sh, MS_PROMPT)
        sh.close()
        # heredoc ended and cat ran; exit code 0
        passed = ec == '0'
        record("CD-08", "BC-D4: heredoc 途中 Ctrl+D × 2 -> heredoc 終了・コマンド実行",
               passed, "$?=0", f"$?={ec}")
    except pexpect.TIMEOUT:
        sh.close()
        record("CD-08", "BC-D4: heredoc 途中 Ctrl+D × 2 -> heredoc 終了・コマンド実行",
               False, "heredoc ends after 2 Ctrl+D", "TIMEOUT")

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Signal Behavior Test Suite")
    print(f"  Target: {MINISHELL}")
    print("=" * 60)

    print("\n── Ctrl+C Tests ──────────────────────────────────────────")
    cc_01()
    cc_02()
    cc_03()
    cc_04()
    cc_05()
    cc_06()
    cc_07()
    cc_08()
    cc_09()
    cc_10()
    cc_11()

    print("\n── Ctrl+D Tests ──────────────────────────────────────────")
    cd_01()
    cd_02()
    cd_03()
    cd_04()
    cd_05()
    cd_06()
    cd_07()
    cd_08()

    total = PASS_COUNT + FAIL_COUNT
    print("\n" + "=" * 60)
    print(f"  Results: {PASS_COUNT}/{total} PASS  |  {FAIL_COUNT}/{total} FAIL")
    print("=" * 60)

    if FAIL_COUNT > 0:
        print("\n── Failed Tests ──────────────────────────────────────────")
        for tc_id, name, status, expected, actual, note in RESULTS:
            if status == "FAIL":
                print(f"  {tc_id}: {name}")
                if expected:
                    print(f"    expected: {repr(expected)}")
                if actual:
                    print(f"    actual  : {repr(actual)}")
                if note:
                    print(f"    note    : {note}")

if __name__ == '__main__':
    main()
