# cli.py
import argparse
import requests
import time
import sys

API_BASE = "http://localhost:8000/api"


def main():
    parser = argparse.ArgumentParser(description="Qwen Backend CLI Tool")
    parser.add_argument("--action", required=True, choices=["zh_to_en", "en_to_zh", "summarize"], help="要执行的功能")
    parser.add_argument("--text", required=True, help="要处理的文本")
    parser.add_argument("--mode", choices=["sync", "stream", "poll"], default="poll", help="调用模式")

    args = parser.parse_args()
    payload = {"feature": args.action, "text": args.text}

    if args.mode == "poll":
        print("[*] 提交异步任务...")
        resp = requests.post(f"{API_BASE}/task", json=payload).json()
        task_id = resp["task_id"]
        print(f"[*] 任务 ID: {task_id}。开始轮询...")

        while True:
            status_resp = requests.get(f"{API_BASE}/task/{task_id}").json()
            if status_resp["status"] == "completed":
                print("\n[✔] 最终结果：\n")
                print(status_resp["result"])
                break
            elif status_resp["status"] == "failed":
                print(f"\n[✘] 任务失败: {status_resp['result']}")
                break

            print(".", end="", flush=True)
            time.sleep(1)

    elif args.mode == "stream":
        print("[*] 开始流式接收：\n")
        with requests.post(f"{API_BASE}/stream", json=payload, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startsWith("data: "):
                        data = decoded_line[6:]
                        if data == "[DONE]":
                            break
                        print(data, end="", flush=True)
        print("\n\n[✔] 完成")


if __name__ == "__main__":
    main()