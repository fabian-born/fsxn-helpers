import pandas as pd
import io
import logging
import boto3
from datetime import date, timedelta
from botocore.exceptions import ClientError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Constants
SECRET_NAME = "fsxn-read-api"
REGION_NAME = "<my-region-name>"
S3_BUCKET = "<my-s3-bucket-name>"  # This is the bucket where the CSV files will be uploaded

def lambda_handler(event, context):
    logdate = date.today() - timedelta(days=1)
    cur_month = logdate.strftime("%m")
    cur_year = logdate.strftime("%Y")
    filename = f"{cur_year}-{cur_month}_monthlyreport.csv"
    s3_folder = f"quota-reports/{cur_year}"  # Optional: specify a folder in the S3 bucket

    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=f'quota-reports/{cur_year}/{cur_month}/')

        combined_df = pd.DataFrame()
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].endswith('.csv'):
                    file_name = obj['Key']
                    logger.info(f"Processing file: {file_name}")
                    csv_obj = s3_client.get_object(Bucket=S3_BUCKET, Key=file_name)
                    body = csv_obj['Body'].read().decode('utf-8')
                    temp_df = pd.read_csv(io.StringIO(body), delimiter=',')
                    combined_df = pd.concat([combined_df, temp_df], ignore_index=True)

            if not combined_df.empty:
                combined_df['qtreeUsedTotalGB'] = combined_df['qtreeUsedTotalGB'].astype(float)
                aggregated_df = combined_df.groupby(['svmName', 'volumeName', 'qtreeName'])['qtreeUsedTotalGB'].agg(['max', 'min', 'mean']).reset_index()
                aggregated_df.rename(columns={'max': 'max_value', 'min': 'min_value', 'mean': 'avg_value'}, inplace=True)
                # Convert aggregated DataFrame to CSV in memory
                csv_buffer = io.StringIO()
                aggregated_df.to_csv(csv_buffer, index=False, sep=',')
                csv_buffer.seek(0)
                # Upload the CSV file to S3
                s3_client.put_object(Bucket=S3_BUCKET, Key=f"{s3_folder}/{filename}", Body=csv_buffer.getvalue())
                logger.info(f"Aggregated report uploaded to {s3_folder}/{filename}")
            else:
                logger.warning("No CSV files found for aggregation.")
        else:
            logger.warning("No files found in the specified S3 bucket and prefix.")
    except ClientError as e:
        logger.error(f"ClientError: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

# If running locally for testing
if __name__ == "__main__":
    lambda_handler({}, {})
