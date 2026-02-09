# HOAM Backup Strategy Infrastructure

## Overview

> The following infrastructure has been created to have a backup strategy for the production running databases and clusters.

### Infrastructure Overview

#### Backup Policy
![alt text](imgs/Infrastructure%20-%20Backup%20Organizations.jpeg "Backup Policy")

The backup policy has been created at the organizations level. Using the associa-billing account (158423647223) we have deployed the following backup policy over the production Organizational Unit:

* Backups will be placed in the **source-backup-vault-Prod** backup vault with 7 days of retention
* There will be an automatic copy job that will move the backup snapshots to the us-east-1 region to the **intermediate-backup-vault-Prod** vault
* The **intermediate-backup-vault-Prod** will store snapshots for 35 days.
* The role specified is a custom role deployed on each prod account named **CustomBackupServiceRole**

#### Backup Resources

The strategy for backing up requires a centralized place to have the backups in case of a disaster. The account to store the backups will be the Audit Account (137708847303). Each production account will have a local backup but also we will place anothe copy in the audit account.

The following diagrams shows the infrastructure and resources used to achieve this:

