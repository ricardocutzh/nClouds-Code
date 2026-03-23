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
./deploy.sh prod abfilms
```