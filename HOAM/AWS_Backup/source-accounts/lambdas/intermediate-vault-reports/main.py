import boto3
import json
import os
from botocore.config import Config
from datetime import datetime, timedelta


BACKUP_VAULT=os.getenv("BACKUP_VAULT")
ACCOUNT_ID=os.getenv("ACCOUNT_ID")
DESTINATION_VAULT_ID=os.getenv("DESTINATION_VAULT_ID")
DELTA_TIME_HOURS=int(os.getenv("DELTA_TIME_HOURS"))
REGION=os.getenv("REGION")
SLACK_WEBHOOK=os.getenv("SLACK_WEBHOOK")

my_config = Config(
    region_name = REGION
)

client = boto3.client('backup', config=my_config)

def protected_resources_report():
    results = {
        'account_id': ACCOUNT_ID,
        'protected_resources_count': 0,
        'protected_resources': []
    }
    response = client.list_protected_resources_by_backup_vault(
        BackupVaultName=BACKUP_VAULT,
    )
    if response["Results"]:
        results["protected_resources_count"] = len(response["Results"])
        results["protected_resources"] = response["Results"]
    else:
        print("no elements")

    return results

def copy_jobs_report():
    now = datetime.now()
    hours_ago = now - timedelta(hours=DELTA_TIME_HOURS)

    results = {
        'account_id': ACCOUNT_ID,
        'failed_jobs': {
            'count': 0,
            'jobs': []
        },
        'success_jobs': {
            'count': 0,
            'jobs': []
        }
    }
    response_success = client.list_copy_jobs(
        ByDestinationVaultArn=DESTINATION_VAULT_ID,
        ByCompleteAfter=hours_ago,
        ByState='COMPLETED'
    )
    response_failed = client.list_copy_jobs(
        ByDestinationVaultArn=DESTINATION_VAULT_ID,
        ByCompleteAfter=hours_ago,
        ByState='FAILED'
    )

    if response_failed["CopyJobs"]:
        results["failed_jobs"]["jobs"]  = response_failed["CopyJobs"]
        results["failed_jobs"]["count"] = len(response_failed["CopyJobs"])
    if response_success["CopyJobs"]:
        results["success_jobs"]["jobs"]  = response_success["CopyJobs"]
        results["success_jobs"]["count"] = len(response_success["CopyJobs"])

    return results


def lambda_handler(event, context):
    print("=="*30)
    result_pr = protected_resources_report()
    json_string_pr = json.dumps(result_pr, indent=4, default=lambda o: o.isoformat() if hasattr(o, 'isoformat') else str(o))
    print(json_string_pr)


    print("=="*30)
    result_cr = copy_jobs_report()
    json_string_cr = json.dumps(result_cr, indent=4, default=lambda o: o.isoformat() if hasattr(o, 'isoformat') else str(o))
    print(json_string_cr)

    print("=="*30)

lambda_handler({},{})