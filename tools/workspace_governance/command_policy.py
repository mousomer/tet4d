"""Shared command policy: classify one tool invocation for autonomous polling.

Pure and bounded: no remote calls, no filesystem or repository mutation, no
background work. It classifies a supported shell subset (words, quotes,
operators, loops, functions, command/process substitution, heredocs, shell
``-c`` recursion, common wrappers and GitHub CLI aliases). Anything outside the
subset that may observe remote state is ``UNDETERMINED``; callers deny it.
"""

from __future__ import annotations

import glob
import os
import posixpath
import re
from collections import Counter
from dataclasses import dataclass, field, replace
from itertools import chain, pairwise
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

VERSION = "command-policy-v1"
MAX_ALIAS_CONFIG = 1 << 20
POLICY_CODE = "NO_AUTONOMOUS_POLLING"
ALLOW, DENY, UNDETERMINED = "ALLOW", "DENY", "UNDETERMINED"
MAX_COMMAND_CHARS = 65536
MAX_DEPTH = 6

ALTERNATIVE = (
    "Make one synchronous status request (for example "
    "`gh pr checks N --json name,state,bucket` or `./gov ci-status N`), report "
    "PENDING_EXTERNAL if unresolved, and stop; resume only on a host "
    "notification, a relevant event or a new user instruction. Do not wait for "
    "remote CI unless the declared gate requires it."
)

SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "mksh", "fish"}
INLINE = {
    "python": "-c",
    "python3": "-c",
    "node": "-e",
    "ruby": "-e",
    "perl": "-e",
    "deno": "eval",
}
WAITS = {"sleep", "gsleep"}
REMOTE_FETCHERS = {"curl", "wget", "http", "https", "xh", "httpie"}
OTHER_CI = {
    "glab", "hub", "az", "gcloud", "aws", "circleci", "buildkite-agent", "kubectl",
}  # fmt: skip
GIT_REMOTE = {"ls-remote", "fetch", "pull", "remote"}
LOCAL_HOSTS = re.compile(
    r"^(?:[a-z]+://)?(?:localhost|127\.0\.0\.1|\[::1\]|[^/:]+\.localhost)(?:[:/]|$)",
    re.IGNORECASE,
)
REMOTE_TEXT = re.compile(
    r"\b(?:gh|curl|wget|watch|glab|hub)\b|api\.github\.com|requests\.get|urlopen"
)
DYNAMIC_TEXT = re.compile(
    r"\b(?:gh|watch|curl|wget|glab|hub|kubectl)\b|--watch|--interval|"
    r"pr\s+checks|run\s+(?:view|watch)|api\.github",
    re.IGNORECASE,
)
LOOP_TEXT = re.compile(r"\b(?:sleep|while|until|setInterval|setTimeout)\b")
REMOTE_CALL = re.compile(
    r"subprocess|os\.system|\bsystem\(|execSync|spawnSync|\bspawn\(|urlopen|"
    r"requests\.|http\.client|\bfetch\(|Net::HTTP|LWP::"
)
URL_TEXT = re.compile(r"https?://[^\s'\"]+")
STATUS_FIELDS = re.compile(r"statusCheckRollup|mergeStateStatus")
STATUS_API = re.compile(
    r"check-runs|check-suites|/status(?:es)?$|/statuses/|actions/runs|actions/jobs"
)
GH_TOP = {
    "agent-task", "alias", "api", "attestation", "auth", "browse", "cache",
    "codespace", "completion", "config", "copilot", "extension", "gist",
    "gpg-key", "help", "issue", "label", "org", "pr", "preview", "project",
    "release", "repo", "ruleset", "run", "search", "secret", "ssh-key", "status",
    "variable", "workflow", "accessibility", "licenses", "version",
}  # fmt: skip
GH_VALUE_FLAGS = {
    "-R", "--repo", "-i", "--interval", "-q", "--jq", "-t", "--template",
    "--json", "-a", "--attempt", "-j", "--job", "-X", "--method", "-H",
    "--header", "-f", "--field", "-F", "--raw-field", "-L", "--limit", "-b",
    "--branch", "-s", "--status", "--state", "-u", "--user", "-e", "--event",
    "-c", "--commit", "--hostname", "--input", "--cache", "-p", "--preview",
    "-S", "--search", "-l", "--label", "-A", "--author", "--assignee", "-B",
    "--base", "--head", "-T", "--title", "--body", "--body-file", "-r",
    "--reviewer", "-m", "--milestone", "--workflow", "--created", "-O", "--owner",
}  # fmt: skip
GH_MUTATING = {
    "create", "merge", "close", "reopen", "edit", "comment", "review", "ready",
    "checkout", "rerun", "cancel", "delete", "upload", "set", "add", "remove",
    "lock", "unlock", "transfer", "fork", "clone", "sync", "login", "logout",
    "refresh", "setup-git", "install", "upgrade", "enable", "disable",
    "archive", "unarchive", "rename", "develop", "pin", "unpin", "revert",
    "update-branch", "run", "approve", "dismiss", "link", "unlink", "copy",
}  # fmt: skip
RESERVED = {
    "if", "then", "elif", "else", "fi", "do", "done", "while", "until", "for",
    "select", "case", "esac", "{", "}", "!", "function", "in", "coproc", "repeat",
}  # fmt: skip
SEPARATORS = {";", "&", "&&", "||", "\n", ";;", "(", ")"}
PIPES = {"|", "|&"}


@dataclass(frozen=True)
class RemoteTarget:
    kind: str
    value: str = ""
    repository: str = ""
    ordinary_listing_key: str = ""
    observe: bool = True

    def observation(self) -> str:
        return f"{self.kind}:{self.value}"


def repository_identity(repository: str) -> str:
    return repository.lower().removeprefix("github.com/")


@dataclass(frozen=True)
class Decision:
    decision: str
    violation: str | None = None
    reason: str = ""
    observations: tuple[str, ...] = ()
    limits: tuple[str, ...] = ()
    state_change: bool = False
    remote_targets: tuple[RemoteTarget, ...] = ()
    supervised_remote: bool = False

    def as_dict(self) -> dict:
        return {
            "classifier": VERSION,
            "decision": self.decision,
            "code": POLICY_CODE if self.decision != ALLOW else None,
            "violation": self.violation,
            "reason": self.reason,
            "observations": list(self.observations),
            "limits": list(self.limits),
            "state_change": self.state_change,
        }


@dataclass
class Command:
    argv: list[str]
    loops: tuple[int, ...] = ()
    function: str | None = None
    body: str | None = None
    feeds_from: list[str] | None = None


@dataclass
class Script:
    commands: list[Command] = field(default_factory=list)
    loop_kinds: dict[int, str] = field(default_factory=dict)
    loop_vars: dict[int, str] = field(default_factory=dict)
    subscripts: list[str] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)


class ParseError(ValueError):
    pass


# ---------------------------------------------------------------- lexer


def _match_close(text: str, start: int, opener: str, closer: str) -> int:
    """Index after the matching closer, honouring quotes and nesting."""
    depth, i = 1, start
    while i < len(text):
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char in "'\"":
            i = _skip_quote(text, i)
            continue
        depth += (char == opener) - (char == closer)
        i += 1
        if depth == 0:
            return i
    raise ParseError(f"unterminated {opener}")


def _skip_quote(text: str, start: int) -> int:
    quote, i = text[start], start + 1
    while i < len(text):
        if text[i] == "\\" and quote == '"':
            i += 2
            continue
        if text[i] == quote:
            return i + 1
        i += 1
    raise ParseError("unterminated quote")


class _Lexer:
    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.tokens: list[tuple[str, str]] = []
        self.subs: list[str] = []
        self.globs: list[str] = []
        self.pending_heredocs: list[tuple[str, bool]] = []

    def run(self) -> list[tuple[str, str]]:
        while self.i < len(self.text):
            self._step()
        if self.pending_heredocs:
            self._read_heredocs()
        return self.tokens

    def _step(self) -> None:
        char = self.text[self.i]
        if char == "\n":
            self.tokens.append(("op", "\n"))
            self.i += 1
            if self.pending_heredocs:
                self._read_heredocs()
        elif char in " \t\r":
            self.i += 1
        elif char == "#":
            end = self.text.find("\n", self.i)
            self.i = len(self.text) if end < 0 else end
        elif self._operator():
            return
        else:
            self.tokens.append(("word", self._word()))

    def _operator(self) -> bool:
        text, i = self.text, self.i
        for op in ("&&", "||", ";;", "|&", ";", "|", "&", "(", ")"):
            if text.startswith(op, i) and not text.startswith("&>", i):
                self.tokens.append(("op", op))
                self.i += len(op)
                return True
        match = re.match(r"\d*(<<<|<<-|<<|&>>|&>|>>|>&|<&|<>|>\||>|<)", text[i:])
        if not match or text.startswith(("<(", ">("), i):
            return False
        self.i += match.end()
        self._redirection(match.group(1))
        return True

    def _redirection(self, op: str) -> None:
        if op in {"<<", "<<-"}:
            self._skip_blanks()
            raw_start = self.i
            delimiter = self._word()
            quoted = any(c in self.text[raw_start : self.i] for c in "'\"\\")
            self.pending_heredocs.append((delimiter, op == "<<-"))
            self.tokens.append(("heredoc_marker", "quoted" if quoted else "plain"))
            return
        self._skip_blanks()
        target = self._word() if self.i < len(self.text) else ""
        kind = "herestring" if op == "<<<" else "redirect"
        self.tokens.append((kind, target))

    def _skip_blanks(self) -> None:
        while self.i < len(self.text) and self.text[self.i] in " \t":
            self.i += 1

    def _read_heredocs(self) -> None:
        for delimiter, strip in self.pending_heredocs:
            lines = []
            while self.i < len(self.text):
                end = self.text.find("\n", self.i)
                end = len(self.text) if end < 0 else end
                line = self.text[self.i : end]
                self.i = end + 1
                if (line.lstrip("\t") if strip else line) == delimiter:
                    break
                lines.append(line)
            self.tokens.append(("heredoc", "\n".join(lines)))
        self.pending_heredocs = []

    def _word(self) -> str:
        out: list[str] = []
        pattern = []
        expands = False
        while self.i < len(self.text):
            char = self.text[self.i]
            if char in " \t\r\n;&|()<>" and not self._process_sub(char):
                break
            mark = len(out)
            self._word_part(char, out)
            piece = "".join(out[mark:])
            if char in "'\"\\":
                piece = glob.escape(piece)
            elif char in "*?[":
                expands = True
            pattern.append(piece)
        if expands:
            self.globs.append("".join(pattern))
        return "".join(out)

    def _process_sub(self, char: str) -> bool:
        return char in "<>" and self.text.startswith("(", self.i + 1)

    def _word_part(self, char: str, out: list[str]) -> None:
        text, i = self.text, self.i
        if char == "\\":
            if text[i + 1 : i + 2] != "\n":
                out.append(text[i + 1 : i + 2])
            self.i += 2
        elif char == "'":
            end = _skip_quote(text, i)
            out.append(text[i + 1 : end - 1])
            self.i = end
        elif char == '"':
            self._double_quoted(out)
        elif char == "$" or char == "`" or self._process_sub(char):
            self._expansion(out)
        else:
            out.append(char)
            self.i += 1

    def _double_quoted(self, out: list[str]) -> None:
        self.i += 1
        while self.i < len(self.text) and self.text[self.i] != '"':
            char = self.text[self.i]
            following = self.text[self.i + 1 : self.i + 2]
            if char == "\\" and following and following in '"\\$`\n':
                out.append(self.text[self.i + 1])
                self.i += 2
            elif char in "$`":
                self._expansion(out)
            else:
                out.append(char)
                self.i += 1
        if self.i >= len(self.text):
            raise ParseError("unterminated quote")
        self.i += 1

    def _expansion(self, out: list[str]) -> None:
        text, i = self.text, self.i
        if text.startswith("$((", i):
            self.i = _match_close(text, i + 3, "(", ")") + 1
            out.append("$((arith))")
        elif text.startswith(("$(", "<(", ">("), i):
            end = _match_close(text, i + 2, "(", ")")
            self.subs.append(text[i + 2 : end - 1])
            out.append(f"$(sub:{len(self.subs) - 1})")
            self.i = end
        elif text[i] == "`":
            end = text.find("`", i + 1)
            if end < 0:
                raise ParseError("unterminated backtick")
            self.subs.append(text[i + 1 : end])
            out.append(f"$(sub:{len(self.subs) - 1})")
            self.i = end + 1
        elif text.startswith("${", i):
            end = _match_close(text, i + 2, "{", "}")
            out.append(text[i:end])
            self.i = end
        else:
            out.append("$")
            self.i += 1


# ---------------------------------------------------------------- parser


class _Parser:
    def __init__(self, tokens: list[tuple[str, str]], subs: list[str]):
        self.tokens = tokens
        self.script = Script(subscripts=list(subs))
        self.loop_stack: list[int] = []
        self.pending_loop: list[int] = []
        self.function_stack: list[tuple[str, int]] = []
        self.brace_depth = 0
        self.current: Command | None = None
        self.previous: Command | None = None
        self.piped = False

    def run(self) -> Script:
        index = 0
        while index < len(self.tokens):
            index = self._token(index)
        self._finish()
        return self.script

    def _token(self, index: int) -> int:
        kind, value = self.tokens[index]
        if kind == "op":
            return self._op(index, value)
        if kind == "word":
            return self._word(index, value)
        self._attachment(kind, value)
        return index + 1

    def _attachment(self, kind: str, value: str) -> None:
        if kind in {"heredoc", "herestring"} and self.current is not None:
            self.current.body = value
        elif kind == "heredoc" and self.previous is not None:
            self.previous.body = value

    def _op(self, index: int, value: str) -> int:
        if value == "(" and self._function_definition(index):
            return index + 2
        self._finish()
        self.piped = value in PIPES
        if value in {"(", ")"}:
            return index + 1
        if value == ";;":
            self.script.unsupported.append("case")
        return index + 1

    def _function_definition(self, index: int) -> bool:
        following = self.tokens[index + 1 : index + 2]
        if self.current is None or len(self.current.argv) != 1:
            return False
        if following != [("op", ")")]:
            return False
        name = self.current.argv[0]
        self.current = None
        self.function_stack.append((name, self.brace_depth))
        return True

    def _word(self, index: int, value: str) -> int:
        if self.current is None and value in RESERVED:
            return self._reserved(index, value)
        if self.current is None:
            self.current = Command(
                [],
                loops=tuple(self.loop_stack + self.pending_loop),
                function=self.function_stack[-1][0] if self.function_stack else None,
                feeds_from=self._feed(),
            )
        self.current.argv.append(value)
        return index + 1

    def _feed(self) -> list[str] | None:
        if self.piped and self.previous is not None:
            return self.previous.argv
        return None

    def _reserved(self, index: int, value: str) -> int:
        if value in {"while", "until"}:
            return self._while(index, value)
        elif value == "repeat":
            self._open_loop("repeat")
            return index + 2
        elif value in {"for", "select"}:
            return self._for(index)
        elif value == "do":
            self.loop_stack.extend(self.pending_loop)
            self.pending_loop = []
        elif value == "done" and self.loop_stack:
            self.loop_stack.pop()
        elif value == "{":
            self.brace_depth += 1
        elif value == "}":
            self._close_brace()
        elif value in {"case", "coproc"}:
            self.script.unsupported.append(value)
        elif value == "function":
            return self._function_keyword(index)
        return index + 1

    def _open_loop(self, kind: str) -> int:
        loop_id = len(self.script.loop_kinds)
        self.script.loop_kinds[loop_id] = kind
        self.pending_loop.append(loop_id)
        return loop_id

    def _while(self, index: int, kind: str) -> int:
        if kind == "while" and self.tokens[index + 1 : index + 2] == [("word", "read")]:
            loop_id = self._open_loop("read")
            words = []
            for token_kind, value in self.tokens[index + 2 :]:
                if token_kind != "word" or value == "do":
                    break
                words.append(value)
            names = [w for w in words if not w.startswith("-")]
            self.script.loop_vars[loop_id] = names[-1] if names else "REPLY"
        else:
            self._open_loop(kind)
        return index + 1

    def _for(self, index: int) -> int:
        loop_id = self._open_loop("for")
        name = self.tokens[index + 1][1] if index + 1 < len(self.tokens) else ""
        self.script.loop_vars[loop_id] = name
        index += 2
        while index < len(self.tokens) and self.tokens[index] not in {
            ("word", "do"),
            ("op", ";"),
            ("op", "\n"),
        }:
            index += 1
        return index

    def _function_keyword(self, index: int) -> int:
        name = self.tokens[index + 1][1] if index + 1 < len(self.tokens) else ""
        self.function_stack.append((name, self.brace_depth))
        skip = 2
        if self.tokens[index + 2 : index + 4] == [("op", "("), ("op", ")")]:
            skip = 4
        return index + skip

    def _close_brace(self) -> None:
        self.brace_depth -= 1
        if self.function_stack and self.function_stack[-1][1] == self.brace_depth:
            self.function_stack.pop()

    def _finish(self) -> None:
        if self.current is not None and self.current.argv:
            self.script.commands.append(self.current)
            self.previous = self.current
        self.current = None


def parse(text: str) -> Script:
    lexer = _Lexer(text)
    tokens = lexer.run()
    return _Parser(tokens, lexer.subs).run()


# ---------------------------------------------------------------- commands


@dataclass
class Facts:
    deny: tuple[str, str] | None = None
    observations: list[str] = field(default_factory=list)
    remote: bool = False
    wait: bool = False
    undetermined: list[str] = field(default_factory=list)
    state_change: bool = False

    remote_targets: list[RemoteTarget] = field(default_factory=list)
    supervised_remote: bool = False

    def merge(self, other: Facts) -> None:
        self.deny = self.deny or other.deny
        self.observations += other.observations
        self.remote_targets += other.remote_targets
        self.supervised_remote |= other.supervised_remote
        self.remote = self.remote or other.remote or bool(other.observations)
        self.wait = self.wait or other.wait
        self.undetermined += other.undetermined
        self.state_change = self.state_change or other.state_change


WRAPPER_SKIP = {
    "env": {"-u", "--unset", "-C", "--chdir", "-S"},
    "timeout": {"-s", "--signal", "-k", "--kill-after"},
    "gtimeout": {"-s", "--signal", "-k", "--kill-after"},
    "nice": {"-n", "--adjustment"},
    "stdbuf": set(),
    "exec": {"-a"},
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U"},
    "doas": {"-u", "-C"},
}
REPEATERS = {
    "xargs": {"-I", "-n", "-P", "-L", "-d", "-E", "-s", "-J"},
    "parallel": {"-j", "-n", "-N", "--jobs", "--delay"},
}
SIMPLE_WRAPPERS = {
    "command", "builtin", "nohup", "time", "caffeinate", "unbuffer", "setsid",
    "noglob", "nocorrect", "chronic",
}  # fmt: skip
MAX_SCRIPT_CHARS = 65536
MAX_SCRIPT_FILES = 16


def _unwrap(argv: list[str]) -> list[str]:
    while argv:
        while argv and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", argv[0]):
            argv = argv[1:]
        if not argv:
            return argv
        name = posixpath.basename(argv[0])
        if name in SIMPLE_WRAPPERS:
            argv = _drop_flags(argv[1:], set())
        elif name in WRAPPER_SKIP:
            argv = _drop_flags(argv[1:], WRAPPER_SKIP[name])
            if name in {"timeout", "gtimeout"} and argv:
                argv = argv[1:]
        else:
            return argv
    return argv


def _drop_flags(argv: list[str], valued: set[str]) -> list[str]:
    index = 0
    while index < len(argv) and argv[index].startswith("-") and argv[index] != "-":
        if argv[index] == "--":
            return argv[index + 1 :]
        index += 2 if argv[index] in valued else 1
    while index < len(argv) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", argv[index]):
        index += 1
    return argv[index:]


class Evaluator:
    """Classify parsed commands. ``reader(path)`` optionally returns the text of a
    shell script the command would run (bounded); without it scripts on disk are
    a recorded coverage limit."""

    def __init__(self, aliases: dict[str, str] | None = None, reader=None):
        self.aliases = dict(aliases or {})
        self.reader = reader
        self.limits: list[str] = []
        self.visited: set[str] = set()

    # -- entry points
    def script(self, text: str, depth: int = 0) -> Facts:
        if depth > MAX_DEPTH:
            return Facts(undetermined=["nesting depth exceeded"])
        try:
            parsed = parse(text)
        except (ParseError, IndexError) as exc:
            return self._unparsed(text, str(exc))
        facts = Facts()
        subs = [self.script(sub, depth + 1) for sub in parsed.subscripts]
        functions = self._functions(parsed, depth, subs)
        used: set[int] = set()
        per_command = []
        for command in parsed.commands:
            item = self.command(command, depth, functions)
            for index in _substitutions(command.argv):
                used.add(index)
                item.merge(subs[index])
            per_command.append(item)
            if command.function:
                facts.deny = facts.deny or item.deny
                facts.undetermined += item.undetermined
            else:
                facts.merge(item)
        for index, sub in enumerate(subs):
            if index not in used:
                facts.merge(sub)
        self._loops(parsed, per_command, facts)
        self._recursion(parsed, functions, facts)
        top_level = [
            item
            for command, item in zip(parsed.commands, per_command, strict=True)
            if not command.function
        ]
        _wait_then_remote(top_level, facts)
        _repeated(facts)
        if parsed.unsupported and REMOTE_TEXT.search(text):
            facts.undetermined.append("unsupported construct: " + parsed.unsupported[0])
        return facts

    def _unparsed(self, text: str, why: str) -> Facts:
        if REMOTE_TEXT.search(text):
            return Facts(undetermined=[f"unparseable shell ({why})"])
        return Facts()

    def _functions(self, parsed: Script, depth: int, subs) -> dict[str, Facts]:
        result: dict[str, Facts] = {}
        for command in parsed.commands:
            if command.function:
                facts = result.setdefault(command.function, Facts())
                facts.merge(self.command(command, depth, {}))
                for index in _substitutions(command.argv):
                    facts.merge(subs[index])
        return result

    # -- simple commands
    def command(self, command: Command, depth: int, functions: dict) -> Facts:
        argv = _unwrap(list(command.argv))
        if not argv:
            return Facts()
        name = posixpath.basename(argv[0])
        if name in functions:
            return functions[name]
        handler = self._handler(name)
        if handler is not None:
            return handler(argv, command, depth)
        if argv[0].startswith("$") and DYNAMIC_TEXT.search(" ".join(argv)):
            return Facts(undetermined=["dynamic program name"])
        if "/" in argv[0]:
            return self._path_program(argv[0], depth)
        return Facts()

    def _handler(self, name: str):
        if re.fullmatch(r"python3(\.\d+)?", name):
            name = "python3"
        for names, method in (
            (SHELLS, self._shell),
            (WAITS, _wait),
            (REMOTE_FETCHERS, self._fetch),
            (OTHER_CI, self._other_ci),
            (set(INLINE), self._inline),
            (set(REPEATERS), self._repeater),
        ):
            if name in names:
                return method
        return {
            "eval": lambda argv, c, d: self.script(" ".join(argv[1:]), d + 1),
            "watch": _watch_wrapper,
            "gh": lambda argv, c, d: self.gh(argv[1:], d),
            "gov": self._gov,
            "git": self._git,
            "source": self._source,
            ".": self._source,
            "find": self._find,
        }.get(name)

    def _shell(self, argv: list[str], command: Command, depth: int) -> Facts:
        script = shell_script(argv)
        if script is not None:
            return self.script(script, depth + 1)
        operand = _shell_operand(argv)
        if operand is not None:
            return self._script_file(operand, depth, required=True)
        if command.body is not None:
            return self.script(command.body, depth + 1)
        if command.feeds_from and posixpath.basename(command.feeds_from[0]) in {
            "echo",
            "printf",
        }:
            return self.script(" ".join(command.feeds_from[1:]), depth + 1)
        return Facts()

    def _source(self, argv: list[str], command: Command, depth: int) -> Facts:
        if len(argv) < 2:
            return Facts()
        return self._script_file(argv[1], depth, required=True)

    def _path_program(self, path: str, depth: int) -> Facts:
        return self._script_file(path, depth, required=False)

    def _script_file(self, path: str, depth: int, *, required: bool) -> Facts:
        if self.reader is None:
            self.limits.append(f"script not inspected: {path}")
            return Facts()
        text = self.reader(path)
        if text is None:
            # A dynamic or missing path carries no remote signal of its own.
            if required:
                self.limits.append(f"script not readable: {path}")
            return Facts()
        first = text.split("\n", 1)[0]
        if not required and not re.match(r"#!.*\b(?:ba|z|da|k)?sh\b", first):
            return Facts()
        if path in self.visited:
            return Facts()
        if len(self.visited) >= MAX_SCRIPT_FILES:
            self.limits.append(f"script budget exhausted before: {path}")
            return Facts()
        self.visited.add(path)
        # Script files get their own nesting budget: chained scripts are normal.
        return self.script(text[:MAX_SCRIPT_CHARS], 0)

    def _repeater(self, argv: list[str], command: Command, depth: int) -> Facts:
        name = posixpath.basename(argv[0])
        inner = _unwrap(_drop_flags(argv[1:], REPEATERS[name]))
        return self._repeated_command(inner, command, depth)

    def _find(self, argv: list[str], command: Command, depth: int) -> Facts:
        facts = Facts()
        actions = {"-exec", "-execdir", "-ok", "-okdir"}
        index = 1
        while index < len(argv):
            if argv[index] not in actions:
                index += 1
                continue
            start = index + 1
            end = next(
                (i for i in range(start, len(argv)) if argv[i] in {";", "+"}),
                len(argv),
            )
            facts.merge(self._repeated_command(argv[start:end], command, depth))
            index = end + 1
        return facts

    def _repeated_command(self, inner: list[str], command: Command, depth) -> Facts:
        if not inner:
            return Facts()
        facts = self.command(Command(inner, body=command.body), depth + 1, {})
        if facts.remote or facts.observations or facts.remote_targets:
            code = "POLLING_LOOP" if facts.wait else "REMOTE_FANOUT"
            facts.deny = facts.deny or (
                code,
                "a repeater can repeat a remote state request",
            )
        return facts

    def _gov(self, argv: list[str], command: Command, depth: int) -> Facts:
        args = argv[3:] if argv[1:2] == ["--root"] else argv[1:]
        if args[:1] == ["op"] and (child := submitted_child(args[1:])):
            if depth >= MAX_DEPTH:
                return Facts(
                    undetermined=["nested supervised submission exceeds depth"]
                )
            facts = self.command(Command(child), depth + 1, {})
            if facts.remote or facts.observations or facts.remote_targets:
                facts.supervised_remote = True
            return facts
        positional = [a for a in argv[1:] if not a.startswith("-")]
        if positional[:1] != ["ci-status"]:
            return Facts()
        target = positional[1] if len(positional) > 1 else "current"
        return Facts(observations=[f"pr:{_pr_number(target)}"])

    def _fetch(self, argv: list[str], command: Command, depth: int) -> Facts:
        urls = [a for a in argv[1:] if not a.startswith("-")]
        if urls and all(LOCAL_HOSTS.match(url) for url in urls):
            return Facts()
        facts = Facts(remote=True)
        name = posixpath.basename(argv[0])
        if name in {"curl", "wget"}:
            fields = _curl_query_fields(argv[1:]) if name == "curl" else ()
            for url in urls:
                target = _github_api_target(url, fields=fields, absolute_only=True)
                if target:
                    if name == "curl" and _curl_mutates(argv[1:]):
                        target = replace(target, observe=False)
                    facts.merge(_remote_facts(target))
        return facts

    def _other_ci(self, argv: list[str], command: Command, depth: int) -> Facts:
        name = posixpath.basename(argv[0])
        flags = {a.split("=", 1)[0] for a in argv[1:] if a.startswith("-")}
        positional = [a for a in argv[1:] if not a.startswith("-")]
        watch = flags & {"--watch", "--live", "--stream", "--watch-only", "--follow"}
        if name == "kubectl" and (
            "-w" in flags or positional[:2] == ["rollout", "status"]
        ):
            watch = {"-w"}
        if watch or (
            name in {"aws", "az", "gcloud", "kubectl"} and "wait" in positional
        ):
            return _deny("TOOL_WATCH_MODE", f"{name} watch/wait mode polls")
        return Facts(remote=True)

    def _git(self, argv: list[str], command: Command, depth: int) -> Facts:
        positional = [a for a in argv[1:] if not a.startswith("-")]
        if positional[:1] == ["push"]:
            # Publishing commits changes remote CI state; it authorizes a new read.
            return Facts(state_change=True)
        return Facts(remote=bool(positional) and positional[0] in GIT_REMOTE)

    def _inline(self, argv: list[str], command: Command, depth: int) -> Facts:
        flag = INLINE.get(posixpath.basename(argv[0]), "-c")
        code = argv[argv.index(flag) + 1] if flag in argv[:-1] else command.body
        if not code or not LOOP_TEXT.search(code):
            return Facts()
        calls = REMOTE_CALL.search(code)
        urls = URL_TEXT.findall(code)
        if calls and urls and all(LOCAL_HOSTS.match(url) for url in urls):
            return Facts()
        if calls:
            return Facts(undetermined=["inline program runs remote calls and waits"])
        return Facts()

    # -- GitHub CLI
    def gh(self, args: list[str], depth: int) -> Facts:
        positional, flags = _gh_scan(args)
        path = positional[: 1 if positional[:1] in (["api"], ["status"]) else 2]
        if not path:
            return Facts(remote=True)
        if path[0] not in GH_TOP:
            return self._gh_alias(path, args, depth)
        facts = _gh_builtin(path, positional[len(path) :], flags)
        if any(f == "--watch" for f, _ in flags):
            facts.deny = ("TOOL_WATCH_MODE", "gh --watch polls remote state")
        return facts

    def _gh_alias(self, path, args, depth: int) -> Facts:
        expansion = self.aliases.get(path[0])
        if expansion is None or depth > MAX_DEPTH:
            return Facts(undetermined=[f"unknown gh command or alias: {path[0]}"])
        index = args.index(path[0])
        tail = args[index + 1 :]
        if expansion.startswith("!"):
            quoted = " ".join(_shell_quote(a) for a in tail)
            return self.script(expansion[1:] + " " + quoted, depth + 1)
        try:
            words = _Lexer(expansion).run()
        except ParseError:
            return Facts(undetermined=[f"unparseable gh alias: {path[0]}"])
        expanded = [v for k, v in words if k == "word"]
        return self.gh(args[:index] + expanded + tail, depth + 1)

    # -- whole-script rules
    def _loops(self, parsed: Script, per_command, facts: Facts) -> None:
        for loop_id, kind in parsed.loop_kinds.items():
            members = [
                item
                for command, item in zip(parsed.commands, per_command, strict=True)
                if loop_id in command.loops
            ]
            if not any(m.remote or m.observations for m in members):
                continue
            distinct = kind in {"for", "read"}
            waits = any(m.wait for m in members)
            if (
                distinct
                and not waits
                and not any(m.remote_targets for m in members)
                and not self._constant_status(parsed, loop_id)
            ):
                continue
            facts.deny = facts.deny or (
                "POLLING_LOOP",
                f"{kind} loop repeats a remote state request",
            )

    def _constant_status(self, parsed: Script, loop_id: int) -> bool:
        variable = parsed.loop_vars.get(loop_id, "")
        references = ("$" + variable, "${" + variable) if variable else ()
        for command in parsed.commands:
            argv = _unwrap(list(command.argv))
            if loop_id not in command.loops or not argv:
                continue
            if posixpath.basename(argv[0]) not in {"gh", "gov"}:
                continue
            text = " ".join(argv)
            if not any(ref in text for ref in references):
                return True
        return False

    def _recursion(self, parsed: Script, functions: dict, facts: Facts) -> None:
        for command in parsed.commands:
            name = command.function
            argv = _unwrap(list(command.argv))
            if not name or not argv or posixpath.basename(argv[0]) != name:
                continue
            body = functions.get(name, Facts())
            if body.remote or body.observations:
                facts.deny = facts.deny or (
                    "POLLING_LOOP",
                    "a recursive function repeats a remote state request",
                )


def _wait_then_remote(items: list[Facts], facts: Facts) -> None:
    waited = False
    for item in items:
        if waited and (item.remote or item.observations):
            facts.deny = facts.deny or (
                "SYNTHETIC_WAIT",
                "sleep followed by a remote state request",
            )
            return
        waited = waited or item.wait


def _repeated(facts: Facts) -> None:
    unscoped = Counter(facts.observations)
    scoped = Counter()
    for target in facts.remote_targets:
        if target.observe and target.kind in {"run", "sha"}:
            key = target.observation()
            unscoped[key] -= 1
            scoped[repository_identity(target.repository), key] += 1
    if max(chain(unscoped.values(), scoped.values()), default=0) > 1:
        facts.deny = facts.deny or (
            "REPEATED_STATUS_QUERY",
            "the same remote status is requested more than once",
        )


def _wait(*_) -> Facts:
    return Facts(wait=True)


def _watch_wrapper(*_) -> Facts:
    return _deny("WATCH_WRAPPER", "watch(1) repeats a command")


def _deny(violation: str, reason: str) -> Facts:
    return Facts(deny=(violation, reason))


def _shell_quote(arg: str) -> str:
    return "'" + arg.replace("'", "'\\''") + "'"


SUPERVISOR_VALUE_OPTIONS = {"--profile", "--output", "--run-id", "--repo", "--head-sha"}


def submitted_child(args: list[str]) -> list[str]:
    """The command a supervised run or submit would pass to its adapter."""
    if args[:1] not in (["run"], ["submit"]):
        return []
    index = 1
    while index < len(args):
        word = args[index]
        if word == "--":
            return args[index + 1 :]
        if word in SUPERVISOR_VALUE_OPTIONS:
            index += 2
        elif word.startswith("-"):
            index += 1
        else:
            return args[index:]
    return []


def shell_glob_patterns(command: str, depth: int = 0) -> list[str]:
    """Unquoted pathname expansions in a shell payload and its inline commands."""
    if depth > MAX_DEPTH:
        return []
    lexer = _Lexer(command)
    try:
        parsed = _Parser(lexer.run(), lexer.subs).run()
    except (ParseError, IndexError):
        return lexer.globs
    nested = list(parsed.subscripts)
    nested += [
        script
        for item in parsed.commands
        if (script := shell_script(_unwrap(item.argv)))
    ]
    return lexer.globs + [
        pattern for text in nested for pattern in shell_glob_patterns(text, depth + 1)
    ]


def shell_script(argv: list[str]) -> str | None:
    argv = _unwrap(argv)
    if not argv or posixpath.basename(argv[0]) not in SHELLS:
        return None
    index = 1
    while index < len(argv):
        arg = argv[index]
        if arg == "--" or not arg.startswith(("-", "+")):
            return None
        if not arg.startswith("--") and "c" in arg[1:]:
            return argv[index + 1] if index + 1 < len(argv) else ""
        index += 2 if arg in {"-o", "+o", "-O", "+O"} else 1
    return None


def _shell_operand(argv: list[str]) -> str | None:
    index = 1
    while index < len(argv):
        arg = argv[index]
        if arg == "--":
            return argv[index + 1] if index + 1 < len(argv) else None
        if arg in {"-s", "-i"} or (arg.startswith("-") and "s" in arg[1:]):
            return None
        if not arg.startswith(("-", "+")):
            return arg
        index += 2 if arg in {"-o", "+o", "-O", "+O"} else 1
    return None


def _gh_scan(args: list[str]) -> tuple[list[str], list[tuple[str, str | None]]]:
    """Positional arguments and (flag, value) pairs; values never act as flags."""
    positional: list[str] = []
    flags: list[tuple[str, str | None]] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            positional += args[index + 1 :]
            break
        if not arg.startswith("-") or arg == "-":
            positional.append(arg)
        elif "=" in arg and arg.startswith("--"):
            name, value = arg.split("=", 1)
            flags.append((name, value))
        elif arg in GH_VALUE_FLAGS or (
            arg == "-w" and positional[:2] == ["run", "list"]
        ):
            flags.append((arg, args[index + 1] if index + 1 < len(args) else None))
            index += 1
        elif re.fullmatch(r"-[icLRqtjaXHfF]\S+", arg):
            flags.append((arg[:2], arg[2:].removeprefix("=")))
        else:
            flags.append((arg, None))
        index += 1
    return positional, flags


def _gh_builtin(path: list[str], rest: list[str], flags) -> Facts:
    key = tuple(path)
    names = {name for name, _ in flags}
    remote = _gh_remote_target(key, rest, flags)
    target = _gh_status_target(key, rest, flags, names)
    if remote and remote.kind == "broad" and target:
        remote = replace(remote, ordinary_listing_key=target)
    if remote:
        facts = _remote_facts(
            remote, ordinary=bool(target) or remote.kind in {"sha", "run"}
        )
    else:
        facts = (
            Facts(observations=[target], remote=True) if target else Facts(remote=True)
        )
    if key == ("run", "watch"):
        facts.deny = ("TOOL_WATCH_MODE", "gh run watch polls remote state")
    if key == ("pr", "checks") and names & {"-i", "--interval", "--fail-fast"}:
        facts.deny = ("TOOL_WATCH_MODE", "gh pr checks interval mode polls")
    if len(key) > 1 and key[1] in GH_MUTATING and not facts.deny:
        return Facts(
            state_change=key[0] in {"pr", "run", "workflow", "release"},
            remote_targets=facts.remote_targets,
        )
    if key == ("api",) and _api_mutation(flags):
        return Facts(state_change=True, remote_targets=facts.remote_targets)
    return facts


def _remote_facts(target: RemoteTarget, *, ordinary=True) -> Facts:
    observation = (
        target.ordinary_listing_key if target.kind == "broad" else target.observation()
    )
    return Facts(
        remote=True,
        observations=[observation]
        if ordinary and target.observe and observation
        else [],
        remote_targets=[target],
    )


RUN_ACTIONS = {"view", "watch", "download", "rerun", "cancel", "delete"}
API_QUERY_FIELDS = {"-f", "-F", "--field", "--raw-field"}


def _gh_remote_target(key, rest, flags) -> RemoteTarget | None:
    values = {name: value for name, value in flags}
    repo = _last_flag_value(flags, {"--repo", "-R"}) or ""
    if key == ("run", "list"):
        commit = _last_flag_value(flags, {"--commit", "-c"})
        return _listing_target(repo, commit)
    if key[:1] == ("run",) and key[-1] in RUN_ACTIONS and rest:
        metadata = key[-1] == "view" and values.keys().isdisjoint(
            {"--log", "--log-failed", "-w", "--web"}
        )
        return RemoteTarget("run", rest[0], repo, observe=metadata)
    if key == ("api",) and rest:
        fields = [value for name, value in flags if name in API_QUERY_FIELDS and value]
        if values.get("--hostname") not in {None, "github.com", "api.github.com"}:
            return None
        # Run-scoped API mutations also act on the managed run.
        target = _github_api_target(rest[0], fields=fields)
        if target:
            mutates = _api_mutation(flags)
            if target.kind == "run" or not mutates:
                return replace(target, observe=target.observe and not mutates)
    return None


def _last_flag_value(flags, names) -> str | None:
    return next((value for name, value in reversed(flags) if name in names), None)


def _listing_target(repo: str, commit: str | None) -> RemoteTarget:
    if commit:
        return RemoteTarget("sha", commit.lower(), repo)
    return RemoteTarget("broad", repository=repo)


def _curl_query_fields(args: list[str]) -> tuple[str, ...]:
    names = {"-d", "--data", "--data-raw", "--data-urlencode", "--data-ascii"}
    if not {"-G", "--get"}.intersection(args):
        return ()
    fields = []
    for arg, following in pairwise([*args, ""]):
        if arg in names:
            fields.append(following)
        elif "=" in arg and arg.partition("=")[0] in names:
            fields.append(arg.partition("=")[2])
    return tuple(fields)


def _curl_mutates(args: list[str]) -> bool:
    for index, arg in enumerate(args):
        name, _, inline = arg.partition("=")
        if name in {"-X", "--request"}:
            method = inline or (args[index + 1] if index + 1 < len(args) else "")
            return method.upper() not in {"GET", "HEAD"}
        if arg.startswith("-X") and len(arg) > 2:
            return arg[2:].upper() not in {"GET", "HEAD"}
    return not any(arg in {"-G", "--get"} for arg in args) and bool(
        _curl_query_fields(args)
    )


def _github_api_target(url, *, fields=(), absolute_only=False) -> RemoteTarget | None:
    uri = urlsplit(url)
    if (absolute_only or uri.netloc) and uri.hostname != "api.github.com":
        return None
    path = unquote(uri.path).strip("/")
    match = re.fullmatch(r"repos/([^/]+/[^/]+)/(.+)", path)
    if not match:
        return None
    repository, endpoint = match.groups()
    if run := re.fullmatch(r"actions/runs/(\d+)(?:/(.*))?", endpoint):
        return RemoteTarget("run", run[1], repository, observe=run[2] in {None, "jobs"})
    if commit := re.fullmatch(
        r"commits/(.+)/(?:check-runs|check-suites|status|statuses)", endpoint
    ):
        return RemoteTarget("sha", commit[1].lower(), repository)
    if re.fullmatch(r"actions/(?:workflows/[^/]+/)?runs", endpoint):
        query = parse_qs("&".join((uri.query, *fields)))
        return _listing_target(repository, query.get("head_sha", [None])[-1])
    return None


MCP_RUN_LIST = {
    "list_workflow_runs",
    "fetch_workflow_runs",
    "fetch_commit_workflow_runs",
}
MCP_RUN_GET = {
    "get_workflow_run",
    "get_workflow_run_logs",
    "get_workflow_run_logs_url",
    "get_workflow_run_usage",
    "list_workflow_jobs",
    "list_workflow_run_artifacts",
    "fetch_workflow_run_jobs",
    "fetch_workflow_run_artifacts",
    "rerun_workflow_run",
    "rerun_failed_workflow_run_jobs",
    "cancel_workflow_run",
}
MCP_COMMIT_STATUS = {
    "get_commit_combined_status",
    "get_commit_status",
    "list_commit_statuses",
    "list_check_runs_for_ref",
    "list_check_suites_for_ref",
}


def mcp_remote_target(tool: str, parameters: dict) -> RemoteTarget | None:
    if not tool.startswith("mcp__"):
        return None
    name = tool.split("__")[-1].removeprefix("github_")
    if name in {"actions_get", "actions_list", "actions_run_trigger"}:
        name = parameters.get("method")
        if not isinstance(name, str):
            return None
    repository = str(
        parameters.get("repo_full_name") or parameters.get("repository") or ""
    )
    if not repository and (repo := parameters.get("repo")):
        owner = parameters.get("owner")
        repository = (
            str(repo) if "/" in str(repo) else f"{owner}/{repo}" if owner else ""
        )
    commit = (
        parameters.get("commit_sha")
        or parameters.get("head_sha")
        or parameters.get("sha")
    )
    if name in MCP_RUN_LIST:
        return _listing_target(repository, str(commit) if commit else None)
    if name in MCP_COMMIT_STATUS and (ref := commit or parameters.get("ref")):
        return RemoteTarget("sha", str(ref).lower(), repository)
    if name in MCP_RUN_GET:
        run = (
            parameters.get("run_id")
            or parameters.get("resource_id")
            or parameters.get("id")
        )
        if run is not None:
            metadata = name in {
                "get_workflow_run",
                "list_workflow_jobs",
                "fetch_workflow_run_jobs",
            }
            return RemoteTarget("run", str(run), repository, observe=metadata)
    return None


def _gh_status_target(key, rest, flags, names) -> str | None:
    first = rest[0] if rest else "current"
    json_fields = ",".join(v or "" for n, v in flags if n == "--json")
    if key == ("pr", "checks"):
        return f"pr:{_pr_number(first)}"
    if key == ("pr", "view") and STATUS_FIELDS.search(json_fields):
        return f"pr:{_pr_number(first)}"
    if key == ("run", "view") and not names & {"--log", "--log-failed", "-w", "--web"}:
        return f"run:{first}"
    if key == ("api",) and rest and not _api_mutation(flags):
        return _api_status_target(rest[0])
    return None


def _api_status_target(path: str) -> str | None:
    path = path.split("?", 1)[0].strip("/")
    if not STATUS_API.search(path):
        return None
    for pattern, kind in (
        (r"actions/(?:runs|jobs)/(\d+)", "run"),
        (
            r"commits/([0-9a-fA-F]{7,40}|[^/]+)/(?:check-runs|check-suites|status)",
            "sha",
        ),
        (r"pulls/(\d+)", "pr"),
    ):
        match = re.search(pattern, path)
        if match:
            return f"{kind}:{match.group(1)}"
    return f"api:{path}"


def _pr_number(value: str) -> str:
    match = re.search(r"/pull/(\d+)", value) or re.fullmatch(r"#?(\d+)", value)
    return match.group(1) if match else value


def _api_mutation(flags) -> bool:
    for name, value in flags:
        if name in {"-X", "--method"}:
            return (value or "").upper() != "GET"
    return any(n in {"-f", "-F", "--field", "--raw-field", "--input"} for n, _ in flags)


def _substitutions(argv: list[str]) -> list[int]:
    return [int(n) for word in argv for n in re.findall(r"\$\(sub:(\d+)\)", word)]


# ---------------------------------------------------------------- public API


def evaluate(
    invocation: dict, aliases: dict[str, str] | None = None, reader=None
) -> Decision:
    """Classify a normalized invocation ``{"tool": str, "command": str}``.

    ``reader(path)`` may return bounded text of a script the command would run;
    it lets the caller supply file contents without the evaluator doing I/O."""
    tool = str(invocation.get("tool") or "")
    command = invocation.get("command")
    if not isinstance(command, str):
        return Decision(ALLOW, limits=("no shell command in invocation",))
    if len(command) > MAX_COMMAND_CHARS:
        if REMOTE_TEXT.search(command):
            return Decision(UNDETERMINED, "UNDETERMINED_REMOTE", "command too large")
        return Decision(ALLOW, limits=("command too large to classify",))
    evaluator = Evaluator(aliases, reader)
    facts = evaluator.script(command)
    decision = replace(
        _decide(tool, facts),
        remote_targets=tuple(facts.remote_targets),
        supervised_remote=facts.supervised_remote,
    )
    if evaluator.limits:
        decision = replace(
            decision, limits=decision.limits + tuple(evaluator.limits[:5])
        )
    return decision


def _decide(tool: str, facts: Facts) -> Decision:
    observations = tuple(facts.observations)
    if facts.deny:
        violation, reason = facts.deny
        return Decision(DENY, violation, f"{reason}. {ALTERNATIVE}", observations)
    if tool == "Monitor" and (facts.remote or observations):
        return Decision(
            DENY,
            "MONITOR_REMOTE_STATE",
            f"Monitor would stream repeated remote observations. {ALTERNATIVE}",
            observations,
        )
    if facts.undetermined:
        return Decision(
            UNDETERMINED,
            "UNDETERMINED_REMOTE",
            f"{facts.undetermined[0]}; cannot prove this is not polling. {ALTERNATIVE}",
            observations,
        )
    return Decision(ALLOW, observations=observations, state_change=facts.state_change)


def gh_aliases() -> dict[str, str]:
    """Read `aliases:` from the GitHub CLI config without a YAML dependency."""
    base = os.environ.get("GH_CONFIG_DIR") or os.path.join(
        os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "gh"
    )
    try:
        text = Path(base, "config.yml").read_text(encoding="utf-8")[:MAX_ALIAS_CONFIG]
    except FileNotFoundError:
        return {}
    aliases: dict[str, str] = {}
    inside = False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            inside = line.split(":", 1)[0].strip() == "aliases"
            continue
        match = re.match(r"\s+([^:\s]+):\s*(.*)$", line) if inside else None
        if match:
            value = match.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            aliases[match.group(1)] = value
    return aliases


def script_reader(cwd: str):
    """Bounded reader for scripts a command would run, relative to its cwd."""

    def read(path: str) -> str | None:
        if "$" in path or "\0" in path:
            return None
        candidate = Path(os.path.expanduser(path))
        if not candidate.is_absolute():
            candidate = Path(cwd or ".") / candidate
        try:
            if not candidate.is_file():
                return None
            with candidate.open("rb") as stream:
                data = stream.read(MAX_SCRIPT_CHARS + 1)
        except OSError:
            return None
        if b"\0" in data[:4096]:
            return None
        return data[:MAX_SCRIPT_CHARS].decode("utf-8", "replace")

    return read


def evaluate_shell(invocation: dict, cwd: str) -> Decision:
    """Evaluate with bounded local context and no service access."""
    return evaluate(invocation, aliases=gh_aliases(), reader=script_reader(cwd))
