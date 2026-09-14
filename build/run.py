"""Entry point: python -m build.run  [--only TAB ...]

Runs the full assemble. --only restricts which models rebuild (others keep their
committed baked payload), handy for testing one ported model.
"""
import sys, argparse
sys.path.insert(0, ".")
from build import assemble

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="tab stems to rebuild")
    args = ap.parse_args()
    if args.only:
        import os
        os.environ["MONITOR_ONLY"] = ",".join(args.only)
        print("recomputing only:", args.only, "(others keep baked payload)")
    assemble.run()
