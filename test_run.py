from pathlib import Path
from typing import List, Dict, Any

from syncQuote import save_all_codes2file, SAVE_DIR
from pattern import PatternFinder


def scan_market(files: List[Path]) -> Dict[str, List[Dict[str, Any]]]:
    """对给定行情文件列表运行两种形态识别，返回结果汇总。"""
    finder = PatternFinder()
    custom_matches: List[Dict[str, Any]] = []
    combo_matches: List[Dict[str, Any]] = []

    for fp in files:
        try:
            custom_matches.extend(finder.find_custom_pattern(fp))
            combo_matches.extend(finder.find_limit_combo_pattern(fp))
        except Exception as exc:
            print(f"扫描 {fp.name} 失败: {exc}")
            continue

    return {"custom": custom_matches, "combo": combo_matches}


def main() -> None:
    # 1) 同步全市场前复权日行情到本地
    print("开始同步全市场行情至目录:", SAVE_DIR)
    save_all_codes2file()
    print("行情同步完成")

    # 2) 扫描本地行情文件，识别两种形态
    files = list(Path(SAVE_DIR).glob("*.csv"))
    print("开始扫描模式，共", len(files), "只股票")
    results = scan_market(files)

    print("自定义模式匹配数:", len(results["custom"]))
    if results["custom"]:
        print("示例（前3条）:", results["custom"][:3])
    print("连板组合模式匹配数:", len(results["combo"]))
    if results["combo"]:
        print("示例（前3条）:", results["combo"][:3])


if __name__ == "__main__":
    main()
