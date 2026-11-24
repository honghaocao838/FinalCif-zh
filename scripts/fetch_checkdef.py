"""Download the official PLATON check.def used for CheckCIF alert help.

The file is not versioned in this repository; the installer build fetches it
when it is missing. Usage: python scripts/fetch_checkdef.py [target]
"""
import sys
import urllib.request
from pathlib import Path

URL = 'http://www.platonsoft.nl/xraysoft/unix/platon/check.def'


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('finalcif/datafiles/check.def')
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(URL, timeout=30) as response:
        data = response.read()
    target.write_bytes(data)
    print(f'downloaded {len(data)} bytes -> {target}')


if __name__ == '__main__':
    main()
