"""Run a quick redis_probe and print results (local smoke run)."""
from launcher.health import redis_probe
import json


def main():
    res = redis_probe(host='127.0.0.1', port=6379, timeout=0.3)
    print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()
