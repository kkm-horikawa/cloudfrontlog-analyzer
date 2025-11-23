#!/usr/bin/env python
"""簡易スクリプト: CloudFrontディストリビューションID取得"""
import boto3

session = boto3.Session(profile_name='default')
cf = session.client('cloudfront')
dists = cf.list_distributions()

items = dists.get('DistributionList', {}).get('Items', [])
if items:
    for item in items[:3]:
        print(f"{item['Id']}: {item['DomainName']}")
else:
    print("No distributions found")
