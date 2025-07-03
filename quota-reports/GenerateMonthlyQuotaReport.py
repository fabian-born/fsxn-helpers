import pandas as pd
import io
import logging
import boto3
import requests
requests.packages.urllib3.disable_warnings()
from datetime import date, timedelta    
from botocore.exceptions import ClientError
import json

### Variables ###
secret_name = "fsxn-read-api"
region_name = "eu-west-1"
s3_bucket = "fabianb-bucket"  # This is the bucket where the CSV files will be uploaded
#################

def lambda_handler():
    logdate = date.today() - timedelta(days = 1)
    curMonth = str(logdate.strftime("%m"))
    curYear = str(logdate.strftime("%Y"))
    logfile_prefix =  str(curYear) + "-" + str(curMonth) + "_"
    logfile_suffix = "_monthlyreport.csv"   
    filename = logfile_prefix + logfile_suffix
    s3_folder = "quota-reports" + "/" + curYear    # Optional: specify a folder in the S3 bucket

    try:
        # Upload the CSV file to S3
        s3_client = boto3.client('s3')
        #get all cvs file in a specific bucket
        response = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix='quota-reports/{}/'.format(curYear + '/' + curMonth)  )
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].endswith('.csv'):
                    file_name = obj['Key']
                   # read the csv file an combine them with the other csv files
                    print(f"Processing file: {file_name}")
                    # read file from s3
                    csv_obj = s3_client.get_object(Bucket=s3_bucket, Key=file_name)
                    body = csv_obj['Body'].read().decode('utf-8')
                    # print body
                    # Combine all CSV files into a single DataFrame
                    if 'combined_df' in locals():
                        combined_df = pd.concat([combined_df, pd.read_csv(io.StringIO(body), delimiter=',')])
                    else:
                        combined_df = pd.read_csv(io.StringIO(body), delimiter=',')
                    
                    # return combined_df
            # Sort the combined DataFrame by 'svmName', 'volumeName', and 'qtreeName' and groop it and calculate max, min, and average for the 'value' column
            if 'combined_df' in locals():
                combined_df['qtreeUsedTotalGB'] = combined_df['qtreeUsedTotalGB'].astype(float)
                aggregated_df = combined_df.groupby(['svmName', 'volumeName', 'qtreeName'])['qtreeUsedTotalGB'].agg(['max', 'min', 'mean']).reset_index()
                aggregated_df.rename(columns={'max': 'max_value', 'min': 'min_value', 'mean': 'avg_value'}, inplace=True)
                # Export the aggregated DataFrame to a new CSV file
                aggregated_df.to_csv(filename, index=False, sep=',')
                s3_client.upload_file(filename, s3_bucket, s3_folder + '/' + filename)
                pd.set_option('display.max_rows', None)
                print(aggregated_df)
            
            
        
    except Exception as e:
        print(f"Error: {e}")


lambda_handler()