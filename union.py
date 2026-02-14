#!/usr/bin/env python3
import os
import re
import fnmatch
import json
import hashlib
import argparse
import subprocess
import codecs
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set

# ====== БАЗОВАЯ КОНФИГ ======
PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_BASENAME = PROJECT_ROOT.name
OUTPUT_EXT = ".txt"

TEXT_FILE_EXTENSIONS = (
    '.txt', '.md', '.log', '.csv', '.nfo', '.rtf', '.rst', '.twig',
    '.json', '.xml', '.yaml', '.yml', '.ini', '.cfg', '.conf', '.properties', '.toml', '.env',
    '.html', '.htm', '.css', '.scss', '.sass', '.less',
    '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte', '.astro',
    '.php', '.py', '.rb', '.go', '.java', '.cs', '.sh', '.bat', '.ps1', '.sql',
    '.c', '.cpp', '.h', '.hpp', '.swift', '.kt', '.rs', '.pl', '.dart', '.ipynb',
    '.psd1', '.psm1', '.xaml', '.csproj', '.sln', '.fsproj', '.dockerfile',
    '.gitconfig', '.editorconfig'
)

IGNORE_EXTENSIONS = (
    '.pyc', '.pyo', '.o', '.so', '.dll', '.exe', '.bin', '.tmp', '.temp',
    '.DS_Store', '.lock', '.orig', '.bak', '.swp', '.swo',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.jar', '.war', '.ear', '.class', '.pyi', '.sqlite3', '.db', '.sqlite',
    '.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico', '.svg',
    '.mp3', '.wav', '.ogg', '.flac', '.aac', 'md',
    '.mp4', '.avi', '.mkv', '.mov', '.wmv',
    '.woff', '.woff2', '.ttf', '.otf', '.eot',
)

IGNORE_FILENAMES_STATIC = (
    # системные/служебные
    '.gitignore', '.gitattributes', '.npmignore',
    'Thumbs.db', 'desktop.ini',
    # lock-файлы менеджеров
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'composer.lock', 'Gemfile.lock', 'Podfile.lock',
    'poetry.lock',
    # сборочные/конфиги
    'pyproject.toml', 'requirements.txt',
    'build.gradle', 'pom.xml',
    'webpack.config.js', 'rollup.config.js', 'vite.config.js', 'quasar.config.js',
    # старые «склейки», чтобы не самопоедаться
    'consolidated_content.txt', 'union.txt', 'union.md', 'merged.txt', 'merged.md', 'gemini-conversation-1760415913422.json'
)

IGNORE_DIRS = (
    '.git', '.svn', '.hg',
    '__pycache__',
    'node_modules',
    'venv', '.venv',
    'vendor', 'data',
    'target', 'build', 'dist',
    '.idea', '.vscode',
    'tmp', 'temp', 'old',
    'log', 'logs',
    '.nuxt', '.next', '.cache', '.parcel-cache',
    '.quasar',
    '.ipynb_checkpoints',
    'docs',
    'public', 'out',
    'bower_components',
    'coverage',
    '.devcontainer',
    'migrations', 'import_system_v2', 'unified_import_system', '!old', 'htmlcov'
)

LOCKFILE_NAME = ".consolidate.lock"

# Наследованные «склейки» любыми именами
LEGACY_OUTPUT_PAT = re.compile(r"""
    (?i)
    (consolidated|union|merged|dump|index|bundle|all|content|monolith)
    .* \.(txt|md)$
""", re.VERBOSE)

# ==== OPTIONAL: pathspec ====
try:
    from pathspec import PathSpec
    from pathspec.patterns import GitWildMatchPattern
    HAVE_PATHSPEC = True
except Exception:
    HAVE_PATHSPEC = False


# ====== УТИЛИТЫ ======
def output_name_pattern() -> re.Pattern:
    base = re.escape(OUTPUT_BASENAME)
    ext = re.escape(OUTPUT_EXT)
    return re.compile(rf"^{base}(?:_(\d+))?{ext}$")


def list_existing_outputs() -> List[Tuple[Path, int]]:
    pat = output_name_pattern()
    results: List[Tuple[Path, int]] = []
    for p in PROJECT_ROOT.iterdir():
        if not p.is_file():
            continue
        m = pat.match(p.name)
        if m:
            idx = int(m.group(1)) if m.group(1) else 1
            results.append((p, idx))
    return results


def choose_next_output_path() -> Path:
    outputs = list_existing_outputs()
    names = {p.name for p, _ in outputs}
    base_name = f"{OUTPUT_BASENAME}{OUTPUT_EXT}"
    if base_name not in names:
        return PROJECT_ROOT / base_name
    max_idx = max(idx for _, idx in outputs)
    next_idx = max_idx + 1
    return PROJECT_ROOT / f"{OUTPUT_BASENAME}_{next_idx}{OUTPUT_EXT}"


def prune_old_outputs(keep: int, keep_by: str = "mtime") -> None:
    outs = [p for p, _ in list_existing_outputs()]
    if len(outs) <= keep:
        return
    if keep_by == "index":
        # parse index again
        outs_idx = list_existing_outputs()
        outs_sorted = sorted((p for p, _ in outs_idx), key=lambda p: int(output_name_pattern().match(p.name).group(1) or 1), reverse=True)
    else:
        outs_sorted = sorted(outs, key=lambda p: p.stat().st_mtime, reverse=True)
    for old in outs_sorted[keep:]:
        try:
            old.unlink(missing_ok=True)
        except Exception:
            pass


def acquire_lock(lock_path: Path) -> bool:
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w") as f:
            f.write(str(os.getpid()))
        return True
    except FileExistsError:
        return False


def release_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink(missing_ok=True)
    except Exception:
        pass


def is_text_file(filename: str) -> bool:
    return filename.lower().endswith(TEXT_FILE_EXTENSIONS)


def should_ignore_dir(dirname: str, exclude_dir_globs: List[str]) -> bool:
    if dirname in IGNORE_DIRS:
        return True
    for pat in exclude_dir_globs:
        if fnmatch.fnmatch(dirname, pat):
            return True
    return False


def load_gitignore(project_root: Path):
    if HAVE_PATHSPEC:
        gi = project_root / ".gitignore"
        if gi.is_file():
            try:
                spec = PathSpec.from_lines(GitWildMatchPattern, gi.read_text(encoding="utf-8", errors="ignore").splitlines())
                return ("pathspec", spec)
            except Exception:
                pass
    # fallback: git check-ignore (если есть git и репозиторий)
    try:
        subprocess.run(["git", "-C", str(project_root), "rev-parse", "--is-inside-work-tree"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return ("git", True)
    except Exception:
        return None


def git_is_ignored(rel_path: str) -> bool:
    try:
        proc = subprocess.run(["git", "check-ignore", "-q", "--", rel_path], capture_output=False)
        return proc.returncode == 0
    except Exception:
        return False


def normalized_text(s: str) -> str:
    # нормализация перевода строк + одна пустая строка в конце
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.lstrip(codecs.BOM_UTF8.decode("utf-8"))  # BOM если вдруг в начале
    s = s.strip() + "\n"
    return s


def read_text_normalized(p: Path) -> str:
    raw = p.read_text(encoding="utf-8", errors="ignore")
    return normalized_text(raw)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def strip_ipynb_outputs(text: str) -> str:
    """Грубо и быстро: убираем outputs и execution_count, оставляем source.
    Если JSON кривой — вернем как есть."""
    try:
        import json as _json
        nb = _json.loads(text)
        if isinstance(nb, dict) and "cells" in nb and isinstance(nb["cells"], list):
            for cell in nb["cells"]:
                if isinstance(cell, dict):
                    cell.pop("outputs", None)
                    if "execution_count" in cell:
                        cell["execution_count"] = None
            # компактная запись
            return _json.dumps(nb, ensure_ascii=False, separators=(",", ":"))
        return text
    except Exception:
        return text


SECRET_KEY_PAT = re.compile(r'(?i)\b(PASSWORD|SECRET|TOKEN|API[-_ ]?KEY|ACCESS[-_ ]?KEY|PRIVATE[-_ ]?KEY|PWD)\b')
ENV_KV_PAT = re.compile(r'^\s*([A-Z0-9_\.:-]+)\s*=\s*(.*)\s*$')


def mask_secrets(filename: str, content: str, aggressive: bool) -> str:
    # PEM / приватные ключи
    if filename.lower().endswith(('.pem', '.key')) or "BEGIN PRIVATE KEY" in content:
        return "-----BEGIN PRIVATE KEY-----\n***MASKED***\n-----END PRIVATE KEY-----\n"

    # .env ключи
    if filename.lower().endswith('.env') or aggressive:
        out_lines = []
        for line in content.splitlines():
            m = ENV_KV_PAT.match(line)
            if m:
                k, v = m.group(1), m.group(2)
                if SECRET_KEY_PAT.search(k) or SECRET_KEY_PAT.search(v):
                    out_lines.append(f"{k}=***MASKED***")
                else:
                    out_lines.append(line)
            else:
                out_lines.append(line)
        content = "\n".join(out_lines) + "\n"
    return content


def dir_size_bytes(path: Path, quick_cutoff: int) -> int:
    """Подсчёт размера директории. Если quick_cutoff >0 и размер превысил порог — возвращаем сразу."""
    total = 0
    try:
        for root, dirs, files in os.walk(path, topdown=True, followlinks=False):
            for f in files:
                try:
                    fp = Path(root) / f
                    total += fp.stat().st_size
                    if quick_cutoff and total > quick_cutoff:
                        return total
                except FileNotFoundError:
                    pass
    except Exception:
        pass
    return total


def get_git_commit() -> Optional[str]:
    try:
        out = subprocess.check_output(["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return None


def parse_args():
    ap = argparse.ArgumentParser(description="Project consolidator (minimal output for AI code review)")
    ap.add_argument("--keep", type=int, default=3, help="Сколько итоговых файлов хранить")
    ap.add_argument("--keep-by", choices=["mtime", "index"], default="mtime", help="Критерий ротации")
    ap.add_argument("--max-file-size", type=int, default=2 * 1024 * 1024, help="Макс размер одного файла (байт)")
    ap.add_argument("--max-total-size", type=int, default=50 * 1024 * 1024, help="Макс суммарный размер записи (байт)")
    ap.add_argument("--respect-gitignore", action="store_true", default=True,
                    help="Исключать пути из .gitignore (pathspec/git). По умолчанию включено.")
    ap.add_argument("--no-respect-gitignore", action="store_false", dest="respect_gitignore")
    ap.add_argument("--include-glob", action="append", default=[], help="Доп. включение по glob (можно повторять)")
    ap.add_argument("--exclude-glob", action="append", default=[], help="Исключение по glob (можно повторять)")
    ap.add_argument("--exclude-dir-glob", action="append", default=[], help="Исключение директорий по glob")
    ap.add_argument("--dedupe", action="store_true", default=True, help="Дедуп по содержимому. По умолчанию включено.")
    ap.add_argument("--no-dedupe", action="store_false", dest="dedupe")
    ap.add_argument("--mask-secrets", action="store_true", default=True,
                    help="Маскировать секреты (.env, ключи). По умолчанию включено.")
    ap.add_argument("--no-mask-secrets", action="store_false", dest="mask_secrets")
    ap.add_argument("--mask-aggressive", action="store_true", default=False, help="Агрессивная маскировка (больше эвристик)")
    ap.add_argument("--strip-ipynb", action="store_true", default=True,
                    help="Удалять outputs из .ipynb. По умолчанию включено.")
    ap.add_argument("--no-strip-ipynb", action="store_false", dest="strip_ipynb")
    ap.add_argument("--exclude-dir-if-over", type=int, default=0,
                    help="Если каталог больше N байт — пропускать целиком (0 = выключено)")
    ap.add_argument("--json-summary", type=str, default="", help="Путь для JSON-отчёта")
    ap.add_argument("--dry-run", action="store_true", help="Показать, что попадёт в сборку, без записи файла")
    return ap.parse_args()


# ====== ОСНОВНАЯ ЛОГИКА ======
def should_ignore_file(filename: str, rel_path: str, full_path: Path, args, output_name: str,
                       gitignore_ctx, include_globs: List[str], exclude_globs: List[str]) -> Tuple[bool, Optional[str]]:
    """Возвращает (игнорировать?, причина)"""
    # текущий итоговый файл
    if filename == output_name:
        return True, "current_output"

    # pathspec/gitignore
    if args.respect_gitignore and gitignore_ctx:
        mode, spec = gitignore_ctx
        if mode == "pathspec":
            if spec.match_file(rel_path):
                return True, "gitignore"
        elif mode == "git":
            if git_is_ignored(rel_path):
                return True, "gitignore"

    if filename in IGNORE_FILENAMES_STATIC:
        return True, "static_ignore_filename"

    if any(filename.lower().endswith(ext) for ext in IGNORE_EXTENSIONS):
        return True, "ignore_extension"

    if output_name_pattern().match(filename):
        return True, "output_pattern"

    if LEGACY_OUTPUT_PAT.match(filename):
        return True, "legacy_bundle"

    # include/exclude globs
    if include_globs:
        if not any(fnmatch.fnmatch(rel_path, pat) for pat in include_globs):
            return True, "not_in_include_globs"
    if exclude_globs:
        if any(fnmatch.fnmatch(rel_path, pat) for pat in exclude_globs):
            return True, "exclude_glob"

    # symlink
    try:
        if full_path.is_symlink():
            return True, "symlink"
    except Exception:
        pass

    # не текстовый по расширению
    if not is_text_file(filename):
        return True, "non_text_ext"

    # размер файла
    try:
        size = full_path.stat().st_size
        if size > args.max_file_size:
            return True, "too_large_file"
    except FileNotFoundError:
        return True, "missing"

    return False, None


def consolidate():
    args = parse_args()

    # lock
    lock_path = PROJECT_ROOT / LOCKFILE_NAME
    if not args.dry_run:
        if not acquire_lock(lock_path):
            print("Другой процесс уже выполняет консолидацию. Выходим.")
            return

    summary = {
        "project_root": str(PROJECT_ROOT),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "git_commit": get_git_commit(),
        "params": vars(args),
        "processed_files": 0,
        "written_bytes": 0,
        "skipped": {},   # причина -> список/счетчик
        "included": [],  # список относительных путей
    }
    skipped_reasons_count: Dict[str, int] = {}

    try:
        # выбор имени
        output_path = choose_next_output_path()
        output_name = output_path.name

        gitignore_ctx = load_gitignore(PROJECT_ROOT) if args.respect_gitignore else None

        # детерминированный список всех кандидатов
        candidates: List[Path] = []
        # Быстрый отсев жирных каталогов по порогу
        big_dirs_skipped: Set[Path] = set()

        for root, dirs, files in os.walk(PROJECT_ROOT, topdown=True, followlinks=False):
            # сортировка для воспроизводимости
            dirs.sort()
            files.sort()

            # отсекаем каталоги по фикс-списку и glob’ам
            kept_dirs = []
            for d in dirs:
                if should_ignore_dir(d, args.exclude_dir_glob):
                    skipped_reasons_count["ignore_dir_name_or_glob"] = skipped_reasons_count.get("ignore_dir_name_or_glob", 0) + 1
                    continue
                dir_path = Path(root) / d
                if args.exclude_dir_if_over > 0 and dir_path not in big_dirs_skipped:
                    size = dir_size_bytes(dir_path, args.exclude_dir_if_over)
                    if size > args.exclude_dir_if_over:
                        big_dirs_skipped.add(dir_path)
                        skipped_reasons_count["ignore_dir_size"] = skipped_reasons_count.get("ignore_dir_size", 0) + 1
                        continue
                kept_dirs.append(d)
            dirs[:] = kept_dirs

            root_path = Path(root)
            for f in files:
                full = root_path / f
                candidates.append(full)

        # сортируем кандидатов по относительному пути
        candidates.sort(key=lambda p: p.relative_to(PROJECT_ROOT).as_posix())

        # запись
        total_written_bytes = 0
        content_hashes: Set[str] = set()

        # откроем файл, если не dry-run
        outfile = None
        if not args.dry_run:
            outfile = open(output_path, 'w', encoding='utf-8')
            # заголовок с контекстом сборки
            header = {
                "bundle": output_name,
                "project_root": str(PROJECT_ROOT),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "git_commit": get_git_commit(),
                "params": vars(args)
            }
            outfile.write(f"--- START OF FILE {output_name} ---\n\n")
            outfile.write("BUILD_META=" + json.dumps(header, ensure_ascii=False, sort_keys=True) + "\n\n")

        try:
            for full_path in candidates:
                rel = full_path.relative_to(PROJECT_ROOT).as_posix()
                filename = full_path.name

                ignore, reason = should_ignore_file(
                    filename, rel, full_path, args, output_name, gitignore_ctx,
                    args.include_glob, args.exclude_glob
                )
                if ignore:
                    if reason:
                        skipped_reasons_count[reason] = skipped_reasons_count.get(reason, 0) + 1
                    continue

                # читаем и нормализуем
                try:
                    content = read_text_normalized(full_path)
                    # спец-обработка ipynb
                    if args.strip_ipynb and filename.lower().endswith('.ipynb'):
                        content = strip_ipynb_outputs(content)

                    # маскируем секреты
                    if args.mask_secrets:
                        content = mask_secrets(filename, content, aggressive=args.mask_aggressive)

                    # дедуп по контенту
                    if args.dedupe:
                        h = sha256_text(content)
                        if h in content_hashes:
                            skipped_reasons_count["dedup_content"] = skipped_reasons_count.get("dedup_content", 0) + 1
                            continue
                        content_hashes.add(h)

                    block = f"=== НАЧАЛО ФАЙЛА: {rel} ===\n{content}=== КОНЕЦ ФАЙЛА: {rel} ===\n\n"
                    block_bytes = len(block.encode('utf-8'))

                    if total_written_bytes + block_bytes > args.max_total_size:
                        # мягкая остановка
                        if not args.dry_run:
                            outfile.write(f"--- Достигнут лимит '--max-total-size' ({args.max_total_size} байт). Остановлено. ---\n")
                        skipped_reasons_count["stop_by_total_limit"] = skipped_reasons_count.get("stop_by_total_limit", 0) + 1
                        break

                    if not args.dry_run:
                        outfile.write(block)
                    total_written_bytes += block_bytes
                    summary["processed_files"] += 1
                    summary["included"].append(rel)

                except Exception as e:
                    skipped_reasons_count["read_error"] = skipped_reasons_count.get("read_error", 0) + 1
                    if not args.dry_run and outfile:
                        outfile.write(f"=== НАЧАЛО ФАЙЛА (ОШИБКА ЧТЕНИЯ): {rel} ===\n")
                        outfile.write(f"(Произошла ошибка при чтении файла: {e})\n")
                        outfile.write(f"=== КОНЕЦ ФАЙЛА (ОШИБКА ЧТЕНИЯ): {rel} ===\n\n")
                    continue

        finally:
            if not args.dry_run and outfile:
                outfile.write(f"--- END OF FILE {output_name} ---\n")
                outfile.close()

        summary["written_bytes"] = total_written_bytes

        # ротация
        if not args.dry_run:
            prune_old_outputs(keep=args.keep, keep_by=args.keep_by)

        # печать итога
        print("-" * 50)
        if not args.dry_run:
            print(f"Сканирование завершено. Результаты в файле: {output_path}")
        else:
            print("DRY-RUN завершён. Ничего не записано.")
        print(f"Обработано файлов: {summary['processed_files']}")
        print(f"Итогово записано байт: {summary['written_bytes']}")
        for reason, cnt in sorted(skipped_reasons_count.items()):
            print(f"Пропущено ({reason}): {cnt}")

        summary["skipped"] = skipped_reasons_count

        # JSON summary
        if args.json_summary:
            try:
                Path(args.json_summary).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"JSON-отчёт: {args.json_summary}")
            except Exception as e:
                print(f"Не удалось записать JSON-отчёт: {e}")

    finally:
        if not args.dry_run:
            release_lock(lock_path)


if __name__ == "__main__":
    consolidate()
