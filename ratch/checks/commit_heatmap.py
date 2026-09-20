"""commit-heatmap eye: directory groups, file rows, time columns."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from ratch.check import Plant
from ratch.result import MeasuredValue, MState, Result, State
from ratch.testing import FakeWorkspace

_MAX_COMMITS = 500
_MAX_DIRS = 8
_MAX_FILES = 24
_DENSITY = (
    (0, " "),
    (1, "."),
    (3, ":"),
    (6, "*"),
    (11, "+"),
    (21, "#"),
)


def _top_dir(path):
    if "/" not in path:
        return "(root)"
    return path.split("/", 1)[0]


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
        commits.append((ts, lines[1:]))
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


def _bucket_keys(start_ts, end_ts, grain, max_cols=14):
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


def _row(label, key, cols, cell, width):
    cells = "".join(f"{_cell_char(cell.get((key, col), 0)):>3}" for col in cols)
    return f"{label:<{width}} {cells}"


def _header(cols, width):
    return " " * width + " " + "".join(f"{col[-3:]:>3}" for col in cols)


def _render(dir_cell, file_cell, dirs, files_by_dir, cols):
    width = 28
    lines = ["dirs", _header(cols, width)]
    for name in dirs:
        lines.append(_row(name, name, cols, dir_cell, width))
    lines.append("files")
    for name in dirs:
        grouped = files_by_dir.get(name, [])
        if not grouped:
            continue
        lines.append(f"{name}/")
        for path in grouped:
            short = path if len(path) <= width else "..." + path[-(width - 3):]
            lines.append(_row(short, path, cols, file_cell, width))
    return "\n".join(lines)


class CommitHeatmap:
    """Report a directory-grouped file x time commit heatmap.

    Rule:
        Recent commits are shown twice: top-level directories against
        time, then files grouped under those directories against the
        same time axis.

    Why:
        Coarse directory totals show where the repo is moving; file
        rows under each directory show which paths actually churned.
        That is a lens, not a gate.

    Proven in:
        git log timestamps plus name-only paths, folded into a density
        grid. Directories first, files second, time across.

    Not this:
        Not a gate. Not role inference. Not an interactive TUI.
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
                extra=("--name-only", "-n", str(_MAX_COMMITS)),
            )
        )
        n = len(commits)
        if n < self.min_surface:
            return Result(self.id, State.VACUOUS, examined_n=n, findings=[])
        timestamps = [ts for ts, _files in commits]
        span = max((max(timestamps) - min(timestamps)) / 3600, 0)
        grain = _grain(span)
        cols = _bucket_keys(min(timestamps), max(timestamps), grain)
        dir_cell = defaultdict(int)
        file_cell = defaultdict(int)
        dir_totals = Counter()
        file_totals = Counter()
        for ts, files in commits:
            col = _bucket_key(ts, grain)
            if col not in cols:
                continue
            for path in files:
                top = _top_dir(path)
                dir_cell[(top, col)] += 1
                dir_totals[top] += 1
                file_cell[(path, col)] += 1
                file_totals[path] += 1
        if not dir_totals:
            return Result(self.id, State.VACUOUS, examined_n=n, findings=[])
        dirs = [name for name, _ in dir_totals.most_common(self.max_dirs)]
        hot_files = [path for path, _ in file_totals.most_common(self.max_files)]
        files_by_dir = defaultdict(list)
        for path in hot_files:
            top = _top_dir(path)
            if top in dirs:
                files_by_dir[top].append(path)
        grid = _render(dir_cell, file_cell, dirs, files_by_dir, cols)
        measured = MeasuredValue(
            value=grid,
            state=MState.MEASURED,
            source="git_log:name-only",
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
        log = "\x1e1700000000\nratch/checks/a.py\ntests/t.py\n"
        return FakeWorkspace(files={"a.py": "x = 1\n"}, git_log_text=log)
