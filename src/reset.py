from __future__ import annotations

from session import Session


def main() -> None:
    session = Session()
    session.reset()
    print("Session reset complete.")


if __name__ == "__main__":
    main()
