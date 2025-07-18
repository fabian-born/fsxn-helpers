#!/bin/bash

mkdir package
pip install -r requirements.txt --target ./package

cd package
zip -r ../deployment_DailyReport.zip .

cd ..

cp deployment_DailyReport.zip deployment_MonthlyReport.zip

cp GenerateDailyQuotaReport_v2.py lambda_function.py
zip deployment_DailyReport.zip lambda_function.py

cp GenerateMonthlyQuotaReport_v2.py lambda_function.py
zip deployment_MonthlyReport.zip lambda_function.py

mv deployment_MonthlyReport.zip ../dist/quota-reports-monthly.zip
mv deployment_DailyReport.zip ../dist/quota-reports-daily.zip

echo Clean Up...
rm lambda_function.py
rm -rf package

echo $VERSION
