import asyncio

from network_monitor_tds.bootstrap import serve
from network_monitor_tds.settings import AppSettings


def main() -> None:
    asyncio.run(serve(AppSettings()))


if __name__ == "__main__":
    main()
