import boto3
import json

REGION = "us-east-1"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

client = boto3.client("bedrock-runtime", region_name=REGION)
def invoke_bedrock(messages: list, system_prompt: str = "", max_tokens: int = 1000):

    # 1. FORCE correct structure
    formatted = []

    for m in messages:
        role = m["role"]

        # normalize role safety
        if role not in ["user", "assistant"]:
            continue

        formatted.append({
            "role": role,
            "content": [
                {
                    "type": "text",
                    "text": str(m["content"])
                }
            ]
        })

    # 2. REMOVE invalid start
    while formatted and formatted[0]["role"] != "user":
        formatted.pop(0)

    # 3. FIX consecutive roles (CRITICAL FIX)
    cleaned = []
    last_role = None

    for m in formatted:
        if m["role"] == last_role:
            continue
        cleaned.append(m)
        last_role = m["role"]

    formatted = cleaned

    # 4. fallback safety
    if not formatted:
        formatted = [{
            "role": "user",
            "content": [{"type": "text", "text": "Start interview"}]
        }]

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": formatted,
    }

    if system_prompt:
        payload["system"] = [{"type": "text", "text": system_prompt}]

    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]