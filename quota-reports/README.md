# FSxN Quota Report Generator (AWS Lambda)

This project provides an AWS Lambda function that generates **daily quota reports** from **Amazon FSx for NetApp ONTAP (FSxN)**. The reports are created in both CSV and JSON format and uploaded to a defined S3 bucket. The JSON output can optionally be used as a **custom resource for CloudWatch dashboards, alarms, or custom metrics**.

---

## 📦 Features

- Fetches quota reports via the FSxN REST API
- Authenticates using AWS Secrets Manager
- Generates a daily quota report:
  - 📄 CSV format for archival or analysis
  - 🧾 JSON format for integration with CloudWatch or other services
- Stores both files in a structured S3 bucket path by year/month/date
- Fully optimized to run as an AWS Lambda function

---

## File Versions

| file                                                                 | description                                                       | state       |
| -------------------------------------------------------------------- | ----------------------------------------------------------------- | ----------- |
| [GenerateDailyQuotaReport.py](GenerateDailyQuotaReport.py)           | Generate daily report from an EC2 - not working with AWS Lambda   | available   |
| [GenerateDailyQuotaReport_v2.py](GenerateDailyQuotaReport_v2.py)     | Generate daily report, running as Lambda function                 | available   |
| [GenerateMonthlyQuotaReport.py](GenerateMonthlyQuotaReport.py)       | Generate monthly report from an EC2 - not working with AWS Lambda | testing |
| [GenerateMonthlyQuotaReport_v2.py](GenerateMonthlyQuotaReport_v2.py) | Generate monthly report, running as Lambda function               | testing |

---

## 🔧 Setup

### Prerequisites

- One or more FSxN file systems with management endpoint enabled
- A secret in AWS Secrets Manager with this structure:

```json
{
  "username": "admin",
  "password": "your_password"
}
```

- Required IAM permissions for the Lambda execution role:
  - `fsx:DescribeFileSystems`
  - `secretsmanager:GetSecretValue`
  - `s3:PutObject`
  - `s3:PutObjectAcl` (optional)
  - `logs:*` (for debugging/logging)

---

## 🚀 Deployment

### Manual Deployment via AWS Console

1. Create a new Lambda function using Python 3.11 (or 3.9+)
2. Upload the `lambda_function.py` script (as a ZIP or directly)
3. Package and attach the `requests` module either via Lambda Layer or within the ZIP
4. Set environment variables (optional) or hardcode the following:
   - `SECRET_NAME`
   - `REGION_NAME`
   - `S3_BUCKET`
5. Schedule the Lambda function using **EventBridge (CloudWatch Events)**, e.g., daily at 01:00 AM

---

## 📁 S3 Output Structure

Reports are saved in the following structure:

```
s3://fabianb-bucket/quota-reports/YYYY/MM/2025-07-01_fsxName_dailyreport.csv
s3://fabianb-bucket/quota-reports/YYYY/MM/2025-07-01_fsxName_dailyreport.json
```

---

## 📊 Using JSON Output for CloudWatch

The generated JSON file follows this structure:

```json
[
  {
    "FileSystem": "fsxName",
    "SVM": "svm1",
    "Volume": "vol1",
    "Qtree": "qtree1",
    "UsedGB": 123.45
  }
]
```

This data can be used to:

- Push custom metrics into CloudWatch
- Build CloudWatch dashboards for storage usage
- Feed into analytics tools like Athena, QuickSight, or third-party solutions

---

## 🛡️ Security

- API credentials are securely retrieved from AWS Secrets Manager
- All API calls are made over HTTPS (SSL verification currently disabled — can be enabled for production)

---

## 🤝 Contributing

Pull requests are welcome! Feel free to contribute enhancements such as:

- Additional output formats
- Direct CloudWatch integration
- Infrastructure-as-Code (IaC) deployment support via CDK or Terraform

---

## 📄 License

MIT License – see [LICENSE](LICENSE)
