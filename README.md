# Lokask Infrastructure


This repository contains the infrastructure definitions and deployment configurations for the Lokask application. It manages the provisioning of AWS resources (such as S3 storage and IAM roles) and the underlying host environment configuration (EC2, SSH access). It also handles the Dockerized application environment, enforcing secure traffic routing through an NGINX reverse proxy with configured SSL volumes while isolating the Go backend.

# Structure

```Plaintext
LOKASK-INFRA/
├── env/
│   └── dev/                     # Environment-specific configurations
│       ├── packer/              # Used for building pre-made images
│       ├── main.tf
│       ├── outputs.tf
│       ├── providers.tf
│       ├── terraform.tfvars
│       └── variables.tf
├── modules/                     # Reusable code, independent of environments
│   ├── compute/
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── networking/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   └── storage/
│       ├── main.tf
│       ├── outputs.tf
│       └── variables.tf
└── script/                      # Scripts for assume role, cleanup, etc.
```

# Current status: 

Active developed
