import json
import boto3
import botocore.config
from datetime import datetime
from botocore.exceptions import ClientError

def blog_generate_using_bedrock(blogtopic: str) -> str:

    prompt = f"""
Write a blog (300–500 words, professional tone).
Include exactly 5 subtopics and a conclusion.


Topic: {blogtopic}
"""

    formatted_prompt = f"""
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
{prompt}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""

    native_request = {
        "prompt": formatted_prompt,
        "max_gen_len": 600,
        "temperature": 0.5
    }


    request = json.dumps(native_request)

    try:
        client = boto3.client(
            "bedrock-runtime",
            region_name="us-west-2",
            config=botocore.config.Config(
                read_timeout=300,
                retries={"max_attempts": 3}
            )
        )

        model_id = "meta.llama3-70b-instruct-v1:0"
        response = client.invoke_model(
            modelId=model_id,
            body=request
        )
        model_response = json.loads(response["body"].read())
        return model_response.get("generation", "")

    except ClientError as e:
        print(f"Bedrock ClientError: {e}")
        return ""

    except Exception as e:
        print(f"General Error: {e}")
        return ""

def save_blog_details_s3(s3_key, s3_bucket, generate_blog):

    s3 = boto3.client("s3")

    try:
        s3.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=generate_blog
        )
        print("Blog saved successfully to S3")

    except Exception as e:
        print(f"S3 Error: {e}")

def lambda_handler(event, context):
    print("EVENT RECEIVED:", event)
    body = event.get("body", "{}")

    if isinstance(body, str):
        body = json.loads(body)

    blogtopic = body.get("blog_topic", "")
    generate_blog = blog_generate_using_bedrock(blogtopic)

    if generate_blog:
        curr_time = datetime.now().strftime("%H%M%S")
        s3_key = f"blog-output/{curr_time}.txt"
        s3_bucket = {YOUR_BUCKET_NAME_HERE}
        save_blog_details_s3(s3_key, s3_bucket, generate_blog)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Blog generated successfully",
                "blog": generate_blog
            })
        }

    return {
        "statusCode": 500,
        "body": json.dumps("Blog generation failed")
    }

