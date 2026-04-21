import boto3
import json

client = boto3.client("bedrock-runtime", region_name="us-east-1")

MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

prompt = "Generate 3 interview questions for a Python developer."

payload = {
    "anthropic_version": "bedrock-2023-05-31",
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ],
    "max_tokens": 300,
    "temperature": 0.7
}

try:
    print("🔄 Calling Bedrock...")

    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())

    print("\n✅ RESPONSE:\n")
    print(result["content"][0]["text"])

except Exception as e:
    print("❌ ERROR:", e)
