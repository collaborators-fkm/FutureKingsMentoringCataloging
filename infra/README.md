# Terraform Infrastructure

This folder contains the Terraform configuration for the Azure resources used by
the catalog service.

## What Terraform Manages

Terraform is configured to manage these existing Azure resources:

- Resource group: `fkm-ppt-catalog`
- App Service plan: `ASP-fkmpptcatalog-a032`
- Linux Web App: `catalog-service`

Because these resources already exist in Azure, import them into Terraform state
before running `terraform plan` or `terraform apply`.

## Prerequisites

Install these tools before starting:

1. Terraform.
2. Azure CLI.

The AzureRM provider uses the Azure CLI for authentication. Follow the provider
guide here for installing and authenticating with the Azure CLI:

https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/azure_cli

After installing the Azure CLI, sign in:

```sh
az login
```

If you have access to more than one Azure subscription, select the subscription
that owns the `fkm-ppt-catalog` resources:

```sh
az account list --output table
az account set --subscription "<SUBSCRIPTION_ID_OR_NAME>"
```

## Prepare Local Variables

From the repository root, copy the example variables file:

```sh
cp infra/.tfvars.example infra/terraform.tfvars
```

Edit `infra/terraform.tfvars` and replace every placeholder value with the real
value for the environment.

Do not commit `terraform.tfvars`. It contains secrets. The `.gitignore` file is
configured to ignore `*.tfvars`.

## Initialize Terraform

Run all Terraform commands from the `infra` folder:

```sh
cd infra
terraform init
```

`terraform init` downloads the AzureRM provider and prepares the local
Terraform working directory.

## Import Existing Azure Resources

First, get the Azure resource IDs.

Resource group:

```sh
az group show --name fkm-ppt-catalog --query id -o tsv
```

App Service plan:

```sh
az appservice plan show \
  --name ASP-fkmpptcatalog-a032 \
  --resource-group fkm-ppt-catalog \
  --query id -o tsv
```

Web App:

```sh
az webapp show \
  --name catalog-service \
  --resource-group fkm-ppt-catalog \
  --query id -o tsv
```

Then import each resource into Terraform state. Replace the placeholders with
the IDs returned by the commands above.

```sh
terraform import azurerm_resource_group.resource_group <RESOURCE_GROUP_ID>
terraform import azurerm_service_plan.service_plan <SERVICE_PLAN_ID>
terraform import azurerm_linux_web_app.app_service <WEB_APP_ID>
```

Importing tells Terraform that these Azure resources already exist and should be
managed by this configuration. It does not create, update, or delete the
resources.

## Check and Apply Changes

After importing the resources, run these commands from the `infra` folder:

```sh
terraform fmt -recursive
terraform validate
terraform plan
```

Review the `terraform plan` output carefully. It shows what Terraform will
change in Azure.

If the plan looks correct, apply it:

```sh
terraform apply
```

Terraform will ask for confirmation before making changes. Type `yes` only if
the planned changes are expected.

## Files That Should Not Be Committed

Do not commit local Terraform state or secret variable files, including:

- `terraform.tfvars`
- `*.tfstate`
- `*.tfstate.*`
- `.terraform/`
- `.terraform.tfstate.lock.info`

Commit the Terraform configuration files, `.tfvars.example`, this README, and
`.terraform.lock.hcl`.
