import os
import json


class Logger:
    def __init__(self, log_dir, name = "log.jsonl"):
        os.makedirs(log_dir, exist_ok=True)
        self.log_path = os.path.join(log_dir, name)
        print(f"[INFO] [Logger] Logging to: {self.log_path}")

    def log(self, test, results):
        record = {
            "test": test,
        }

        for method in results:
            record[method] = results[method]

        with open(self.log_path, 'a', encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
