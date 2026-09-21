"""commit-heatmap eye: directory groups, file rows, time columns."""
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from ratch.check import Plant
from ratch.result import MeasuredValue, MState, Result, State
from ratch.testing import FakeWorkspace

_MAX_COMMITS = 500
_MAX_DIRS = 8
_MAX_FILES = 24
_MAX_COLS = 14
_DENSITY = (
    (0, " "),
    (1, "."),
    (3, ":"),
    (6, "*"),
    (11, "+"),
    (21, "#"),
)
# log-ish |net| cutoffs: 10^0, 10^1, ~10^1.5, 10^2, ~10^2.5
_GROWTH_STEPS = (
    (1, ".", "o"),
    (10, ":", "~"),
    (32, "*", "-"),
    (100, "+", "="),
    (316, "#", "@"),
)
_GROWTH_CAPTION = (
    "growth (per-column ins-del, log ladder, not file size; tracked only)"
)


def _want_compact():
    if os.environ.get("RATCH_COMPACT"):
        return True
    return os.environ.get("CI", "").lower() in {"1", "true"}


def _top_dir(path):
    if "/" not in path:
        return "(root)"
    return path.split("/", 1)[0]


def _normalize_path(path):
    if " => " not in path:
        return path
    left, right = path.split(" => ", 1)
    if "{" in left and right.endswith("}"):
        prefix, _old = left.split("{", 1)
        return prefix + right[:-1]
    return right


def _parse_stat_line(line):
    parts = line.split("\t", 2)
    if len(parts) != 3:
        return None
    ins_s, del_s, raw_path = parts
    path = _normalize_path(raw_path)
    if ins_s == "-" and del_s == "-":
        return path, None, None
    try:
        return path, int(ins_s), int(del_s)
    except ValueError:
        return None


def _parse_log(text):
    commits = []
    for rec in text.split("\x1e"):
        lines = [line.strip() for line in rec.splitlines() if line.strip()]
        if not lines:
            continue
        try:
            ts = int(lines[0])
        except ValueError:
            continue
        files = []
        for line in lines[1:]:
            parsed = _parse_stat_line(line)
            if parsed is not None:
                files.append(parsed)
        commits.append((ts, files))
        if len(commits) >= _MAX_COMMITS:
            break
    return commits


def _grain(span_hours):
    if span_hours <= 48:
        return "hour"
    if span_hours <= 14 * 24:
        return "day"
    return "week"


def _bucket_key(ts, grain):
    dt = datetime.fromtimestamp(ts)
    if grain == "hour":
        return dt.strftime("%m-%d %H")
    if grain == "day":
        return dt.strftime("%m-%d")
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def _bucket_keys(start_ts, end_ts, grain, max_cols=_MAX_COLS):
    start = datetime.fromtimestamp(start_ts)
    end = datetime.fromtimestamp(end_ts)
    if grain == "hour":
        cursor = start.replace(minute=0, second=0, microsecond=0)
        step = timedelta(hours=1)
    elif grain == "day":
        cursor = start.replace(hour=0, minute=0, second=0, microsecond=0)
        step = timedelta(days=1)
    else:
        cursor = (start - timedelta(days=start.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        step = timedelta(days=7)
    keys = []
    while cursor <= end:
        keys.append(_bucket_key(cursor.timestamp(), grain))
        cursor += step
    return keys[-max_cols:]


def _cell_char(n):
    ch = " "
    for threshold, glyph in _DENSITY:
        if n >= threshold:
            ch = glyph
    return ch


def _growth_char(n):
    if n == 0:
        return " "
    glyph = " "
    for threshold, pos, neg in _GROWTH_STEPS:
        if abs(n) >= threshold:
            if n > 0:
                glyph = pos
            else:
                glyph = neg
    return glyph


def _row(label, key, cols, cell, width, char_fn):
    cells = "".join(f"{char_fn(cell.get((key, col), 0)):>3}" for col in cols)
    return f"{label:<{width}} {cells}"


def _header(cols, width):
    return " " * width + " " + "".join(f"{col[-3:]:>3}" for col in cols)


def _short(path, width):
    if len(path) <= width:
        return path
    return "..." + path[-(width - 3):]


def _render_panel(title, dir_cell, file_cell, dirs, files_by_dir, cols, char_fn):
    width = 28
    lines = [title, "dirs", _header(cols, width)]
    for name in dirs:
        lines.append(_row(name, name, cols, dir_cell, width, char_fn))
    lines.append("files")
    for name in dirs:
        grouped = files_by_dir.get(name, [])
        if not grouped:
            continue
        lines.append(f"{name}/")
        for path in grouped:
            lines.append(
                _row(_short(path, width), path, cols, file_cell, width, char_fn)
            )
    return lines


def _group(dirs, ranked_files):
    files_by_dir = defaultdict(list)
    allowed = set(dirs)
    for path in ranked_files:
        top = _top_dir(path)
        if top in allowed:
            files_by_dir[top].append(path)
    return files_by_dir


class CommitHeatmap:
    """Report a directory-grouped file x time commit heatmap.

    Rule:
        Recent commits are shown as two panels on the same axes:
        touch counts, then per-column insert-minus-delete net.

    Why:
        How often a path moved and how much mass it gained are different
        facts. Both are git-recomputable; neither is a quality score.

    Proven in:
        git log --numstat timestamps and paths, folded into a density
        grid. Directories first, files second, time across. Growth is
        per-column net, not file size.

    Not this:
        Not a gate. Not a cumulative stock. Not role inference.
    """

    id = "commit-heatmap"
    tier = "A"
    kind = "eye"
    scope = "global"
    proven_in = ()
    confidence = "depth-once"
    tolerates_unparseable = False

    def __init__(self, min_surface=1, max_dirs=_MAX_DIRS, max_files=_MAX_FILES):
        if min_surface < 1:
            raise ValueError("min_surface must be >= 1")
        self.min_surface = min_surface
        self.max_dirs = max_dirs
        self.max_files = max_files

    def check(self, ws):
        commits = _parse_log(
            ws.git_log(
                fmt="%x1e%at",
                extra=("--numstat", "-n", str(_MAX_COMMITS)),
            )
        )
        n = len(commits)
        if n < self.min_surface:
            return Result(self.id, State.VACUOUS, examined_n=n, findings=[])
        timestamps = [ts for ts, _files in commits]
        span = max((max(timestamps) - min(timestamps)) / 3600, 0)
        grain = _grain(span)
        cols = _bucket_keys(min(timestamps), max(timestamps), grain)
        retained = set(cols)
        touch_dir = defaultdict(int)
        touch_file = defaultdict(int)
        grow_dir = defaultdict(int)
        grow_file = defaultdict(int)
        touch_dir_n = Counter()
        touch_file_n = Counter()
        grow_file_n = Counter()
        tracked = set(ws.tracked_files())
        for ts, files in commits:
            col = _bucket_key(ts, grain)
            if col not in retained:
                continue
            for path, ins, dele in files:
                if path not in tracked:
                    continue
                top = _top_dir(path)
                touch_dir[(top, col)] += 1
                touch_dir_n[top] += 1
                touch_file[(path, col)] += 1
                touch_file_n[path] += 1
                if ins is None:
                    continue
                net = ins - dele
                grow_dir[(top, col)] += net
                grow_file[(path, col)] += net
                grow_file_n[path] += net
        if not touch_dir_n:
            return Result(self.id, State.VACUOUS, examined_n=n, findings=[])
        dirs = [name for name, _ in touch_dir_n.most_common(self.max_dirs)]
        touch_files = [p for p, _ in touch_file_n.most_common(self.max_files)]
        grow_files = sorted(
            grow_file_n, key=lambda path: grow_file_n[path], reverse=True,
        )[: self.max_files]
        lines = _render_panel(
            "touches", touch_dir, touch_file, dirs,
            _group(dirs, touch_files), cols, _cell_char,
        )
        lines.extend(_render_panel(
            _GROWTH_CAPTION, grow_dir, grow_file, dirs,
            _group(dirs, grow_files), cols, _growth_char,
        ))
        if _want_compact():
            value = (
                f"tracked-only commits={n} dirs={len(dirs)} "
                f"files={len(touch_files)}"
            )
        else:
            value = "\n".join(lines)
        measured = MeasuredValue(
            value=value,
            state=MState.MEASURED,
            source="git_log:numstat",
            measured_at=ws.now(),
        )
        return Result(
            self.id, State.PASS, examined_n=n, findings=[], measured=measured,
        )

    def plants(self, ws):
        yield Plant(
            label="empty-log",
            planted_ws=FakeWorkspace(files={"a.py": "x = 1\n"}, git_log_text=""),
            expected=(self.id, "git_log", "0"),
        )

    def fixture(self, kit):
        return FakeWorkspace(
            files={
                "a.py": "x = 1\n",
                "ratch/checks/a.py": "x = 1\n",
                "tests/t.py": "x = 1\n",
            },
            git_log_text=(
                "\x1e1700000000\n"
                "12\t0\tratch/checks/a.py\n"
                "3\t1\ttests/t.py\n"
            ),
        )
