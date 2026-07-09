#!/usr/bin/env python3
from _run_pt_maker_script import main

if __name__ == "__main__":
    import sys

    sys.argv.insert(1, "qa_final_review_gate.py")
    main()
