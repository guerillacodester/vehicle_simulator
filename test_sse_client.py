import requests
import sys

def sse_client(url):
    with requests.get(url, stream=True) as response:
        if response.status_code != 200:
            print(f"Failed to connect: {response.status_code} {response.reason}")
            return
        print("Connected to SSE endpoint. Waiting for events...")
        for line in response.iter_lines():
            if line:
                decoded = line.decode()
                if decoded.startswith("data: "):
                    print(f"Event: {decoded[6:]}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_sse_client.py <SSE_URL>")
        sys.exit(1)
    sse_url = sys.argv[1]
    sse_client(sse_url)
