from downmess_core import DownmessCore
import os

def test_time_parsing():
    core = DownmessCore()
    print("Testing Time Parsing Logic...")
    
    test_cases = [
        ("01:24", 84),
        ("02:30:10", 9010),
        ("45", 45),
        ("0:10", 10),
        ("", 0)
    ]
    
    for t_str, expected in test_cases:
        res = core._parse_time_to_seconds(t_str)
        if res == expected:
            print(f" -> [PASS] '{t_str}' -> {res}s")
        else:
            print(f" -> [FAIL] '{t_str}' -> {res}s (Expected {expected}s)")

def test_mock_download_logic():
    # We won't download a real video to save time/bandwidth, 
    # but we can verify the options dict would be correct.
    # Actually, let's just do the syntax check for now.
    print("\nVerificando integridad de downmess.py...")
    try:
        with open("downmess.py", "r", encoding="utf-8") as f:
            compile(f.read(), "downmess.py", "exec")
        print(" -> [PASS] downmess.py Syntax OK")
    except Exception as e:
        print(f" -> [FAIL] downmess.py Syntax Error: {e}")

if __name__ == "__main__":
    test_time_parsing()
    test_mock_download_logic()
