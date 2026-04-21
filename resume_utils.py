import boto3

S3_BUCKET = "ali-interview-coach"   # ← change this
REGION    = "us-east-1"

s3       = boto3.client("s3",       region_name=REGION)
textract = boto3.client("textract", region_name=REGION)


def upload_resume_to_s3(file_bytes: bytes, filename: str) -> str:
    """Upload file to S3 and return the S3 key."""
    from datetime import datetime
    s3_key = f"resumes/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=file_bytes)
    return s3_key


def extract_text_from_resume(s3_key: str) -> str:
    """Use Textract to extract text from a resume stored in S3."""
    response = textract.detect_document_text(
        Document={"S3Object": {"Bucket": S3_BUCKET, "Name": s3_key}}
    )
    print("Checking for Debug:",response)
    blocks = response.get("Blocks", [])
    lines  = [b["Text"] for b in blocks if b["BlockType"] == "LINE"]
    return "\n".join(lines)