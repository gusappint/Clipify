from __future__ import annotations

import sys


def main() -> int:
    if "--worker" in sys.argv:
        from ytclip.worker import worker_main

        worker_args = [arg for arg in sys.argv[1:] if arg != "--worker"]
        return worker_main(worker_args)

    from ytclip.ui import run_app

    run_app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
