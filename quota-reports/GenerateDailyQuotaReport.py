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
s3_bucket = "<my-s3-bucket-name>" # This is the bucket where the CSV files will be uploaded
#################

logger = logging.getLogger(__name__)

def lambda_handler():
    # 

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
    )
    # Get the current date and time, set it to yesterday
    # This is used to create the log file name. The log file name is in the format YYYY-MM-DD_dailyreport 

    logdate = date.today() - timedelta(days = 1)
    logfile_prefix =  str(logdate) + "_"
    logfile_suffix = "_dailyreport.csv"
    curMonth = str(logdate.strftime("%m"))
    curYear = str(logdate.strftime("%Y"))

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    # receive credentials from AWS Secrets Manager
    # This is required to access the FSxN API
    secret = json.loads(get_secret_value_response['SecretString'])

    # Create a boto3 client for FSx
    # This is required to access the FSxN API
    # The client is used to retrieve the list of FSx filesystems
    # and to get the management IP address for each filesystem
    # The client is also used to get the quota reports for each filesystem
    fsx_client = boto3.client('fsx')




    try:
        # Retrieve the list of FSx filesystems
        # required for looping through all filesystems
        response = fsx_client.describe_file_systems()

        # Iterate through the filesystems and print details
        for filesystem in response['FileSystems']:
            # Print files sysstem details
            # print(f"File System ID: {filesystem['FileSystemId']}")
            # print(f"File System Name: {filesystem['Tags'][0]['Value']}")
            # print(f"File System Type: {filesystem['FileSystemType']}")
            # print(f"Storage Capacity: {filesystem['StorageCapacity']} GB")
            # print(f"Creation Time: {filesystem['CreationTime']}")
            # print(f"Lifecycle: {filesystem['Lifecycle']}")
            # print(f"Endpoints: {filesystem['OntapConfiguration']['Endpoints']['Management']['IpAddresses']}")
            # print("-" * 40)

            # Management IP address for API calls
            mgmt_ip = filesystem['OntapConfiguration']['Endpoints']['Management']['IpAddresses'][0] # Assuming there's at least one IP address
            # Get all SVMs

            # Generate csv file for quota reports and write file header
            with open(logfile_prefix + filesystem['Tags'][0]['Value'] + logfile_suffix, "w") as f:
                   f.write("svmName,volumeName,qtreeName,qtreeUsedTotalGB\n")


        
            # Get Quota Reports
            apiurl = "https://" + mgmt_ip + "/api/storage/quota/reports"

            # A get request to the API
            quotaresponse = requests.get(apiurl, auth=(secret['username'], secret['password']), verify=False, headers={'Content-Type': 'application/json'})
            # save json response as to variable
            quotadata = quotaresponse.json()

            # Check if the response contains records
            # If there are no records, skip to the next filesystem

            for quotareport in quotadata['records']:
                # get Quota report URL
                # This is the URL to get detailed quota report for each volume
                # The URL is in the _links section of the quota report
                volumeQuotaReportURL = quotareport['_links']['self']['href']

                # Get Detailed Volume Quota Report                
                apiurl = "https://" + mgmt_ip + volumeQuotaReportURL 
                vqresponse  = requests.get(apiurl, auth=(secret['username'], secret['password']), verify=False, headers={'Content-Type': 'application/json'})
                detailreport = vqresponse.json()
                
                
                svmName = quotareport['svm']['name']    
                volumeName = quotareport['volume']['name']

                qtreeName = detailreport['qtree']['name']
                if qtreeName == "":
                    qtreeName = "-"

                SpaceUsedTotalGB = round((detailreport['space']['used']['total']/1024/1024/1024),3)
                # SpaceHardlimitGB = round((detailreport['space']['hard_limit']/1024/1024/1024),3)
                # SpaceSoftlimitGB= round((detailreport['space']['soft_limit']/1024/1024/1024),3)
                # SpaceUsedSoftlimitPercent = detailreport['space']['used']['soft_limit_percent']
                # SpaceUsedHardlimitPercent = detailreport['space']['used']['hard_limit_percent']


                FilesUsedTotal = detailreport['files']['used']['total']
                # FilesHardlimit = detailreport['files']['hard_limit']
                # FilesSoftlimit = detailreport['files']['soft_limit']
                # FilesUsedSoftlimitPercent = detailreport['space']['used']['soft_limit_percent']
                # FilesUsedHardlimitPercent = detailreport['space']['used']['hard_limit_percent']                

                # Write the quota report to a CSV file
                # The file is named with the filesystem name and the date
                # The file is created in the same directory as the script

                with open(logfile_prefix + filesystem['Tags'][0]['Value'] + logfile_suffix, "a") as f:
                    f.write("{svmName},{volumeName},{qtreeName},{SpaceUsedTotalGB}\n".format(qtreeName=qtreeName, svmName=svmName, volumeName=volumeName, SpaceUsedTotalGB =SpaceUsedTotalGB ))
    
    except Exception as e: 
        print(f"Error: {e}")


    try:
        # Upload the CSV file to S3
        s3_client = boto3.client('s3')
        # The CSV file is named with the filesystem name and the date
        # The file is created in the same directory as the script
        # The file is uploaded to the S3 bucket specified in the s3_bucket variable
        # The file is uploaded with the same name as the local file
        filename = logfile_prefix + filesystem['Tags'][0]['Value'] + logfile_suffix
        s3_folder = "quota-reports" + "/" + curYear + "/" + curMonth   # Optional: specify a folder in the S3 bucket
        
        s3_client.put_object(Bucket=s3_bucket, Key=(s3_folder + '/'))
        # print(f"Folder '{s3_folder}' created successfully in bucket '{s3_bucket}'.")

        s3_client.upload_file(filename, s3_bucket, s3_folder + '/' + filename)
        # Print success message
        # print(f"Quota report for {filesystem['Tags'][0]['Value']} uploaded to S3 bucket {s3_bucket}/{s3_folder}.")
    except Exception as e:
        print(f"Error: {e}")

lambda_handler()
