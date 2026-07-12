import sys
import os

# Add upy_light_engine root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import engine.framebuffer as fb

def test_push_and_flush(func_call):
    try:
        func_call()
        if hasattr(fb.screen, '_flush'):
            fb.screen._flush()
        return "OK"
    except Exception as e:
        return f"FAILED (Exception caught): {type(e).__name__}: {e}"

def run_tests():
    print("Starting pset crash investigation tests...")
    
    # 1. Coordinate Boundary Tests
    print("\n--- 1. Coordinate Boundary Tests ---")
    boundaries = [
        (-1, -1),
        (240, 135),
        (30000, 30000),
        (-30000, -30000),
        (65535, 65535),
        (-65535, -65535)
    ]
    
    for x, y in boundaries:
        print(f"Testing pset({x}, {y}, 1)... ", end="")
        res = test_push_and_flush(lambda: fb.screen.pset(x, y, 1))
        print(res)

    # 2. Invalid Type Tests
    print("\n--- 2. Invalid Type Tests ---")
    types_to_test = [
        (10.5, 20.3, "float"),
        ("10", "20", "str"),
        (None, None, "None")
    ]
    
    for x, y, desc in types_to_test:
        print(f"Testing pset with {desc}... ", end="")
        res = test_push_and_flush(lambda: fb.screen.pset(x, y, 1))
        print(res)

    # 3. Invalid Color Tests
    print("\n--- 3. Invalid Color Tests ---")
    colors = [
        -1,
        256,
        0xFFFFFF,
        -99999
    ]
    
    for c in colors:
        print(f"Testing pset(10, 10, {c})... ", end="")
        res = test_push_and_flush(lambda: fb.screen.pset(10, 10, c))
        print(res)

    # 4. Line Boundary Tests (more complex calculations)
    print("\n--- 4. Line Boundary Tests ---")
    lines = [
        (-100, -100, 300, 300),
        (32767, 32767, -32768, -32768)
    ]
    for x1, y1, x2, y2 in lines:
        print(f"Testing line({x1}, {y1}) to ({x2}, {y2})... ", end="")
        res = test_push_and_flush(lambda: fb.screen.line(x1, y1, x2, y2, 1))
        print(res)

    print("\nAll tests completed without hard crash.")

if __name__ == "__main__":
    run_tests()
