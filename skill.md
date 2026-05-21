# skill.md

title: Qwen_Text_Processor
description: 提供基于阿里云百炼大模型的文本处理能力，包括中英互译和文本总结。
version: 1.0.0
type: rest_api

openapi_spec: |
  openapi: 3.0.0
  info:
    title: Qwen Mini App API
    version: 1.0.0
  servers:
    - url: http://localhost:8000/api
  paths:
    /task:
      post:
        operationId: submitTask
        summary: 提交异步文本处理任务
        description: 提交中译英、英译中或文本总结任务。返回任务ID供后续轮询。
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  feature:
                    type: string
                    enum: [zh_to_en, en_to_zh, summarize]
                    description: 要执行的功能
                  text:
                    type: string
                    description: 需要处理的文本内容
                required:
                  - feature
                  - text
        responses:
          '200':
            description: 任务提交成功
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    task_id:
                      type: string
                    message:
                      type: string
    
    /task/{task_id}:
      get:
        operationId: getTaskStatus
        summary: 轮询任务状态与结果
        parameters:
          - name: task_id
            in: path
            required: true
            schema:
              type: string
        responses:
          '200':
            description: 返回任务当前状态及结果
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    status:
                      type: string
                      enum: [pending, processing, completed, failed]
                    result:
                      type: string
                      description: 最终处理结果（仅在completed状态下有效）