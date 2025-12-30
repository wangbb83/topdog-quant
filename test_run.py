import json

import os

from concurrent.futures import ProcessPoolExecutor, as_completed

from pathlib import Path

from typing import Any, Dict, List, Optional



try:

    from syncQuote import SAVE_DIR

except Exception:

    SAVE_DIR = "share_daily_qfq"

from pattern import PatternFinder



# 进程池中复用的 PatternFinder 实例，避免每个任务都重新构造。

_process_finder: Optional[PatternFinder] = None





def _init_finder() -> None:

    """进程池 initializer，只在子进程启动时运行一次。"""

    global _process_finder

    _process_finder = PatternFinder()





def _scan_file_worker(file_path: str, methods: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Run selected pattern matchers in a worker process."""
    global _process_finder
    if _process_finder is None:
        _process_finder = PatternFinder()
    method_map = {
        "custom": "find_custom_pattern",
        "combo": "find_limit_combo_pattern",
        "custom_v2": "find_custom_pattern_v2",
    }
    results: Dict[str, List[Dict[str, Any]]] = {}
    for method in methods:
        func = getattr(_process_finder, method_map[method])
        results[method] = func(file_path)
    return results

def scan_market(
    files: List[Path], methods: List[str], max_workers: Optional[int] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Scan market files with selected pattern methods and merge results."""
    results: Dict[str, List[Dict[str, Any]]] = {m: [] for m in methods}

    total = len(files)
    # pandas/NumPy compute + CSV parsing are CPU heavy; use processes to bypass GIL.
    worker_cnt = max_workers or min(max(1, (os.cpu_count() or 4) - 1), 12)
    with ProcessPoolExecutor(max_workers=worker_cnt, initializer=_init_finder) as executor:
        future_map = {executor.submit(_scan_file_worker, str(fp), methods): fp for fp in files}
        done = 0
        for future in as_completed(future_map):
            fp = future_map[future]
            done += 1
            try:
                file_results = future.result()
                for key, rows in file_results.items():
                    results[key].extend(rows)
                print(f"[{done}/{total}] done {fp.name}")
            except Exception as exc:
                print(f"[{done}/{total}] failed {fp.name}: {exc}")

    return results

def save_results(results: Dict[str, List[Dict[str, Any]]], output_path: Path) -> None:
    """Write scan results to a JSON file."""
    payload: Dict[str, Any] = {}
    for key, rows in results.items():
        payload[f"{key}_count"] = len(rows)
        payload[key] = rows
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("results saved:", output_path)

def _select_methods() -> List[str]:
    options = {
        "1": ("custom", "custom pattern v1"),
        "2": ("combo", "limit combo patterns"),
        "3": ("custom_v2", "custom pattern v2"),
        "4": ("__all__", "scan all patterns"),
    }
    print("Select scan modes (comma-separated, Enter = all):")
    for key, (_, desc) in options.items():
        print(f"  {key}) {desc}")
    while True:
        raw = input("Input: ").strip()
        if not raw or raw.lower() in {"all", "a"}:
            return [opt[0] for opt in options.values() if opt[0] != "__all__"]
        picks = [p.strip() for p in raw.split(",") if p.strip()]
        if all(p in options for p in picks):
            if "4" in picks:
                return [opt[0] for opt in options.values() if opt[0] != "__all__"]
            return [options[p][0] for p in picks]
        print("Invalid input, please try again.")

def main() -> None:
    data_dir = Path(SAVE_DIR)
    files = sorted(data_dir.glob("*.txt")) + sorted(data_dir.glob("*.csv"))
    if not files:
        print(f"{data_dir} has no txt/csv data files")
        return

    methods = _select_methods()
    print("Scan dir:", data_dir)
    print("Start scanning, total files:", len(files))
    results = scan_market(files, methods)
    for key, rows in results.items():
        print(f"{key} matches:", len(rows))
        if rows:
            print("results:", rows)

    save_results(results, Path("result.txt"))

if __name__ == "__main__":

    main()

