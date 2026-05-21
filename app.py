
import os
import uuid
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI

app = FastAPI(title="Qwen Mini App")

# 初始化百炼 Qwen 客户端 (使用兼容 OpenAI 的模式)
client = AsyncOpenAI(
    api_key="sk-ce52db39bb3848839e0e9ccc1863d8d0",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 内存模拟数据库，用于存储异步任务状态
tasks_db = {}


# --- 数据模型 ---
class TaskRequest(BaseModel):
    feature: str
    text: str


# --- 功能配置 ---
FEATURES = {
    "zh_to_en": {"name": "中译英", "prompt": "请将以下中文翻译成流畅的英文：\n{text}"},
    "en_to_zh": {"name": "英译中", "prompt": "请将以下英文翻译成流畅的中文：\n{text}"},
    "summarize": {"name": "文本汇总", "prompt": "请对以下内容进行简明扼要的总结提炼：\n{text}"}
}


# --- 内部核心调用函数 ---
async def call_qwen(feature_key: str, text: str, stream: bool = False):
    if feature_key not in FEATURES:
        raise ValueError("不支持的功能")

    prompt = FEATURES[feature_key]["prompt"].format(text=text)
    response = await client.chat.completions.create(
        model="qwen-plus",  # 可替换为 qwen-turbo 或 qwen-max
        messages=[
            {"role": "system", "content": "你是一个专业的语言助手。"},
            {"role": "user", "content": prompt}
        ],
        stream=stream
    )
    return response


# --- 获取所有功能列表 ---
@app.get("/api/features")
async def get_features():
    return [{"id": k, "name": v["name"]} for k, v in FEATURES.items()]


# --- 异步任务提交 ---
@app.post("/api/task")
async def submit_task(req: TaskRequest):
    if req.feature not in FEATURES:
        raise HTTPException(status_code=400, detail="Invalid feature")

    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "pending", "result": ""}

    # 后台执行任务
    async def process_task(tid: str, feature: str, text: str):
        try:
            tasks_db[tid]["status"] = "processing"
            resp = await call_qwen(feature, text, stream=False)
            tasks_db[tid]["result"] = resp.choices[0].message.content
            tasks_db[tid]["status"] = "completed"
        except Exception as e:
            tasks_db[tid]["status"] = "failed"
            tasks_db[tid]["result"] = str(e)

    asyncio.create_task(process_task(task_id, req.feature, req.text))
    return {"task_id": task_id, "message": "Task submitted successfully."}


# --- 轮询获取结果 ---
@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id]


# --- 流式返回接口 ---
@app.post("/api/stream")
async def stream_task(req: TaskRequest):
    if req.feature not in FEATURES:
        raise HTTPException(status_code=400, detail="Invalid feature")

    async def generate():
        try:
            response_stream = await call_qwen(req.feature, req.text, stream=True)
            async for chunk in response_stream:
                if chunk.choices[0].delta.content:
                    # 使用 Server-Sent Events (SSE) 格式
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# --- 前端页面 ---
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)