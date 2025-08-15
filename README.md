# sample-python-app (NON WSGI / NOT FOR PRODUCTION)

## Python specific Files
1. wsgi.py : A simple flask server with port exposed at 8080
2. `app/` folder
2. Dockerfile.app : Simple dockerfile
3. requirements.txt : python dependencies
How to run python app locally:
```
pip install -r requirements.txt
gunicorn -w 2 --timeout 120 -b 0.0.0.0:8080 wsgi:app
```
or
```
python3 wsgi.py
```


## GCP Local Setup
### Install Gcloud using Brew
```
brew install google-cloud-sdk
```

###  Create a GCP Project
![image](https://drive.google.com/uc?export=view&id=1dqDnbe3Yg0MsVRlsMAdWzTkNkMGbOtJq)
1. Go to Google Cloud Console [https://console.cloud.google.com/welcome](https://console.cloud.google.com/welcome)
2. Create a project with the name: hackathon0-project
3. See the Project ID (e.g., hackathon0-project)

### Set the Environment (You have to change it ***)
```
export GCP_PROJECT_ID="openserve-0" # Write it properly after seeing the dashboard
export SERVICE_AC_DISPLAYNAME="openserve0-sa"
export BUCKET_NAME="hackathon-bucket-0"
export GAR_REPOSITORY_ID="python-prod-server"
export GAR_LOCATION="us-central1"
```

### Login To GCloud and Other Setup 
```
gcloud components update
gcloud auth login
gcloud config set project $GCP_PROJECT_ID
```

### Create an Service A/c ( One Time Setup )
```
gcloud iam service-accounts create $SERVICE_AC_DISPLAYNAME --display-name $SERVICE_AC_DISPLAYNAME
```

### Enable the APis ( One Time Setup )
```
gcloud services enable cloudresourcemanager.googleapis.com \
    artifactregistry.googleapis.com \
    iam.googleapis.com \
    run.googleapis.com \
    storage.googleapis.com \
    --project=$GCP_PROJECT_ID
```

### Set the IAM roles ((Service includes CloudRun, GCS, Artifact Registry)) ( One Time Setup )
```
for role in resourcemanager.projectIamAdmin \
            iam.serviceAccountUser \
            run.admin \
            artifactregistry.writer \
            artifactregistry.reader \
            artifactregistry.admin \
            storage.admin \
            storage.objectAdmin \
            storage.objectViewer \
            storage.objectCreator; do
    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
        --member=serviceAccount:$SERVICE_AC_DISPLAYNAME@$GCP_PROJECT_ID.iam.gserviceaccount.com \
        --role=roles/$role
done
```


### Create Bucket ( One Time Setup )
```
gcloud storage buckets create gs://$BUCKET_NAME --location=US --uniform-bucket-level-access
```
If you are getting this error : ERROR: (gcloud.storage.buckets.create) HTTPError 409: The requested bucket name is not available. Then, just set the bucket name with a more unique name, e.g. `export BUCKET_NAME="hackathon-bucket-021432"`

### Create GAR Registry ( One Time Setup )
```
gcloud artifacts repositories create $GAR_REPOSITORY_ID \
    --project=$GCP_PROJECT_ID \
    --location=$GAR_LOCATION \
    --repository-format=docker \
    --description="Docker repository for Python server"
```

### Creating key.json for Service Account ( One Time Setup )
```
gcloud iam service-accounts keys create key.json \
    --iam-account=$SERVICE_AC_DISPLAYNAME@$GCP_PROJECT_ID.iam.gserviceaccount.com
```
Copy the content of key.json into GitHub Secrets in your repository. The GitHub secret key should be GCP_SA_KEY.



## CICD specific Files
 Go to `.github/workflows/pipeline-main.yml`. 
 1. Just change the parameters `GCP_PROJECT_ID`, `CLOUD_RUN_SERVICE` etc as per your need.
 2. Change the 'uses' ref to : <YOUR_GH_USER_ID>/<REPO_NAME>/.github/workflows/python-gcp-main.yml@main


## Commit The Codes
```
sh git-push.sh main 'sample commit message'
```

## Verify the Deployment
![image](https://drive.google.com/uc?export=view&id=1QOn7-2jjjVJUICJkiz36WzTOn91gkU2L)


## Use skip-ci tag to bypass CI deployment
```
sh git-push.sh main 'sample commit message [skip-ci]'
```
 