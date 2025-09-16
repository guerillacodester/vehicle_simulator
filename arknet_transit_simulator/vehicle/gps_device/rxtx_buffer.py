import queue

class RxTxBuffer:
    """
    Simple FIFO queue that decouples the simulator (producer)
    from the GPS device worker (consumer).
    """
    def __init__(self, maxsize=1000):
        self.queue = queue.Queue(maxsize=maxsize)

    def write(self, data):
        """Write telemetry into the buffer (non-blocking)."""
        try:
            self.queue.put(data, block=False)
        except queue.Full:
            print("[WARN] RxTxBuffer full, dropping data")

    def read(self, block=True, timeout=None):
        """Read telemetry from the buffer (blocking or timed)."""
        try:
            return self.queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
