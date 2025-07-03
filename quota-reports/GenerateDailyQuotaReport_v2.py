import boto3
import requests
import json
import io
from datetime import date, timedelta
from botocore.exceptions import ClientError

requests.packages.urllib3.disable_warnings()

# Configuration
SECRET_NAME = "fsxn-read-api"
REGION_NAME = "<my-region-name>"
S3_BUCKET = "<my-s3-bucket-name>"  # Replace with your actual S3 bucket name
S3_FOLDER = "quota-reports"

def lambda_handler(event, context):
    logdate = date.today() - timedelta(days=1)
    logfile_prefix = f"{logdate}_"
    logfile_suffix_csv = "_dailyreport.csv"
    logfile_suffix_json = "_dailyreport.json"
    cur_month = logdate.strftime("%m")
    cur_year = logdate.strftime("%Y")

    session = boto3.session.Session()
    secrets_client = session.client('secretsmanager', region_name=REGION_NAME)

    try:
        secret_response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(secret_response['SecretString'])
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise

    fsx_client = boto3.client('fsx')

    try:
        response = fsx_client.describe_file_systems()
        filesystems = response.get('FileSystems', [])
    except Exception as e:
        print(f"Error describing FSx file systems: {e}")
        return

    for filesystem in filesystems:
        try:
            fs_name = next((tag['Value'] for tag in filesystem['Tags'] if tag['Key'] == 'Name'), filesystem['FileSystemId'])
            mgmt_ip = filesystem['OntapConfiguration']['Endpoints']['Management']['IpAddresses'][0]
            
            # CSV buffer
            csv_buffer = io.StringIO()
            csv_buffer.write("svmName,volumeName,qtreeName,qtreeUsedTotalGB\n")
            # JSON structure
            json_records = []

            quota_api_url = f"https://{mgmt_ip}/api/storage/quota/reports"
            quota_response = requests.get(
                quota_api_url,
                auth=(secret['username'], secret['password']),
                verify=False,
                headers={'Content-Type': 'application/json'}
            )
            quota_data = quota_response.json()

            for report in quota_data.get('records', []):
                detail_url = f"https://{mgmt_ip}{report['_links']['self']['href']}"
                detail_response = requests.get(
                    detail_url,
                    auth=(secret['username'], secret['password']),
                    verify=False,
                    headers={'Content-Type': 'application/json'}
                )
                detail = detail_response.json()

                svm = report['svm']['name']
                volume = report['volume']['name']
                qtree = detail['qtree']['name'] or "-"
                used_gb = round(detail['space']['used']['total'] / 1024 / 1024 / 1024, 3)

                # CSV row
                csv_buffer.write(f"{svm},{volume},{qtree},{used_gb}\n")

                # JSON record
                json_records.append({
                    "FileSystem": fs_name,
                    "SVM": svm,
                    "Volume": volume,
                    "Qtree": qtree,
                    "UsedGB": used_gb
                })

            # Upload CSV to S3
            s3_key_csv = f"{S3_FOLDER}/{cur_year}/{cur_month}/{logfile_prefix}{fs_name}{logfile_suffix_csv}"
            s3_client = boto3.client('s3')
            s3_client.put_object(Body=csv_buffer.getvalue(), Bucket=S3_BUCKET, Key=s3_key_csv)
            print(f"Uploaded CSV: {s3_key_csv}")

            # Upload JSON to S3
            s3_key_json = f"{S3_FOLDER}/{cur_year}/{cur_month}/{logfile_prefix}{fs_name}{logfile_suffix_json}"
            s3_client.put_object(Body=json.dumps(json_records, indent=2), Bucket=S3_BUCKET, Key=s3_key_json)
            print(f"Uploaded JSON: {s3_key_json}")

        except Exception as e:
            print(f"Error processing filesystem {filesystem['FileSystemId']}: {e}")


# lambda_handler("test_event", "test_context")  # Replace with actual event and context in production