from datetime import datetime

class DebugLogger:
    def __init__(self):
        self.logs = []

    def log(self, step, message, data=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "step": step,
            "message": message,
            "data": data
        }
        self.logs.append(entry)
        print(f"[{timestamp}] {step}: {message}")
        if data:
            print(f"  Data: {data}")

    def clear(self):
        self.logs = []

    def get_logs(self):
        return self.logs
