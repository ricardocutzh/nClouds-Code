# S3 Ingest Bucket

## Assume AB FILMS role

* Export the nClouds account SSO Credentials

* Run the *./assume* script to get credentials for ABFilms account:
```
./assume.sh arn:aws:iam::225707668146:role/nc_cross_acc_fullaccess_default
```

* Test you can check the s3 buckets from ABFilms

```
aws s3 ls
```

## Deploy S3 Bucket for Ingest

* Assume the ABFilms credentials

* Deploy using the *./deploy* script:

```
./deploy.sh prod abfilms
```

* You should see an output like this:
```
-------------------------------------------------------
🚀 Deploying Stack: abfilms-filmhub-ingest-bucket to us-east-1
Environment: prod
Identifier: abfilms
-------------------------------------------------------
✅ Deployment Successful!
------------------------------------------------------------
{
    "StackId": "arn:aws:cloudformation:us-east-1:225707668146:stack/abfilms-filmhub-ingest-bucket/c8180f10-2303-11f1-9010-0affeb9748af"
}
🛡️ Termination protection enabled for PROD
```
---