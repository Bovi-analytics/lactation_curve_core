"""Pulumi infrastructure for the MilkBot Function App.

Creates the following Azure resources:
  - Resource Group
  - Storage Account (required backing store for Function App)
  - Blob Container (deployment package storage for Flex Consumption)
  - Log Analytics Workspace (PerGB2018 - first 5 GB/month free via App Insights)
  - Application Insights (monitoring)
  - App Service Plan (Flex Consumption FC1 tier - serverless)
  - Function App (Python 3.12, ASGI wrapping FastAPI)
  - Role Assignment (Storage Blob Data Contributor for managed identity)

Deployment approach:
  Pulumi manages infrastructure only. App code is deployed separately using
  `func azure functionapp publish` (Azure Functions Core Tools). The Function
  App runs from a deployment package stored in blob storage.
"""

import pulumi
from pulumi_azure_native import (
    applicationinsights,
    authorization,
    operationalinsights,
    resources,
    storage,
    web,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config()
stack = pulumi.get_stack()

# Naming prefix based on stack (e.g., "milkbot-dev")
prefix = f"milkbot-{stack}"

# Tags applied to all resources
tags = {
    "Environment": stack,
    "Project": "MilkBot",
    "Owner": "Bovi",
    "ManagedBy": "Pulumi",
}

# ---------------------------------------------------------------------------
# Resource Group
# ---------------------------------------------------------------------------
resource_group = resources.ResourceGroup(
    "resource-group",
    resource_group_name=f"rg-{prefix}",
    tags=tags,
)

# ---------------------------------------------------------------------------
# Storage Account
# Cheapest option: Standard_LRS (locally redundant, no geo-replication)
# ---------------------------------------------------------------------------
storage_account = storage.StorageAccount(
    "storage-account",
    resource_group_name=resource_group.name,
    account_name=f"{prefix.replace('-', '')}sa",  # 3-24 chars, no hyphens
    sku=storage.SkuArgs(name=storage.SkuName.STANDARD_LRS),
    kind=storage.Kind.STORAGE_V2,
    access_tier=storage.AccessTier.HOT,
    enable_https_traffic_only=True,
    minimum_tls_version=storage.MinimumTlsVersion.TLS1_2,
    allow_blob_public_access=False,
    tags=tags,
)

# Get storage account keys for connection strings
storage_keys = pulumi.Output.all(resource_group.name, storage_account.name).apply(
    lambda args: storage.list_storage_account_keys(
        resource_group_name=args[0],
        account_name=args[1],
    )
)
primary_storage_key = storage_keys.keys[0].value

storage_connection_string = pulumi.Output.all(
    storage_account.name, primary_storage_key
).apply(
    lambda args: (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={args[0]};"
        f"AccountKey={args[1]};"
        f"EndpointSuffix=core.windows.net"
    )
)

# ---------------------------------------------------------------------------
# Blob Container (deployment package storage for Flex Consumption)
# ---------------------------------------------------------------------------
deployment_container = storage.BlobContainer(
    "deployment-container",
    resource_group_name=resource_group.name,
    account_name=storage_account.name,
    container_name="deployment-package",
    public_access=storage.PublicAccess.NONE,
)

# ---------------------------------------------------------------------------
# Log Analytics Workspace (PerGB2018 - pay-as-you-go, first 5 GB/month free via App Insights)
# 31 days is the minimum retention for this SKU.
# ---------------------------------------------------------------------------
log_analytics = operationalinsights.Workspace(
    "log-analytics",
    resource_group_name=resource_group.name,
    workspace_name=f"{prefix}-logs",
    sku=operationalinsights.WorkspaceSkuArgs(name="PerGB2018"),
    retention_in_days=31,
    tags=tags,
)

# ---------------------------------------------------------------------------
# Application Insights (Free tier - 1 GB/month data cap, no cost)
# ---------------------------------------------------------------------------
app_insights = applicationinsights.Component(
    "app-insights",
    resource_group_name=resource_group.name,
    resource_name_=f"{prefix}-insights",
    kind="web",
    application_type=applicationinsights.ApplicationType.WEB,
    workspace_resource_id=log_analytics.id,
    retention_in_days=30,
    tags=tags,
)

# ---------------------------------------------------------------------------
# App Service Plan (Flex Consumption - FC1 tier)
# Serverless with per-second billing. Scales to zero when idle.
# ---------------------------------------------------------------------------
app_service_plan = web.AppServicePlan(
    "consumption-plan",
    resource_group_name=resource_group.name,
    name=f"{prefix}-plan",
    sku=web.SkuDescriptionArgs(
        tier="FlexConsumption",
        name="FC1",
    ),
    reserved=True,  # Required for Linux
    tags=tags,
)

# ---------------------------------------------------------------------------
# Function App (Flex Consumption, Python 3.12, ASGI/FastAPI)
# ---------------------------------------------------------------------------
milkbot_key = config.get_secret("milkbotKey") or ""

function_app = web.WebApp(
    "function-app",
    resource_group_name=resource_group.name,
    name=f"{prefix}-func",
    kind="functionapp,linux",
    reserved=True,
    server_farm_id=app_service_plan.id,
    https_only=True,
    identity=web.ManagedServiceIdentityArgs(
        type=web.ManagedServiceIdentityType.SYSTEM_ASSIGNED,
    ),
    function_app_config=web.FunctionAppConfigArgs(
        deployment=web.FunctionsDeploymentArgs(
            storage=web.FunctionsDeploymentStorageArgs(
                type=web.FunctionsDeploymentStorageType.BLOB_CONTAINER,
                value=pulumi.Output.all(
                    storage_account.primary_endpoints,
                    deployment_container.name,
                ).apply(lambda args: f"{args[0]['blob']}{args[1]}"),
                authentication=web.FunctionsDeploymentAuthenticationArgs(
                    type=web.AuthenticationType.STORAGE_ACCOUNT_CONNECTION_STRING,
                    storage_account_connection_string_name="AzureWebJobsStorage",
                ),
            ),
        ),
        runtime=web.FunctionsRuntimeArgs(
            name=web.RuntimeName.PYTHON,
            version="3.12",
        ),
        scale_and_concurrency=web.FunctionsScaleAndConcurrencyArgs(
            instance_memory_mb=2048,
            maximum_instance_count=100,
        ),
    ),
    site_config=web.SiteConfigArgs(
        ftps_state=web.FtpsState.DISABLED,
        min_tls_version="1.2",
        app_settings=[
            # Azure Functions runtime config
            # Note: FUNCTIONS_WORKER_RUNTIME and FUNCTIONS_EXTENSION_VERSION are
            # managed automatically by Flex Consumption via function_app_config.
            web.NameValuePairArgs(name="AzureWebJobsStorage", value=storage_connection_string),
            web.NameValuePairArgs(name="AzureWebJobsFeatureFlags", value="EnableWorkerIndexing"),
            # Monitoring
            web.NameValuePairArgs(
                name="APPLICATIONINSIGHTS_CONNECTION_STRING",
                value=app_insights.connection_string,
            ),
            # Application secrets
            web.NameValuePairArgs(name="MILKBOT_KEY", value=milkbot_key),
        ],
        cors=web.CorsSettingsArgs(
            allowed_origins=["https://portal.azure.com"],
        ),
    ),
    tags=tags,
)

# ---------------------------------------------------------------------------
# Role Assignment — Storage Blob Data Contributor for function app identity
# Allows the function app to access the deployment blob container.
# ---------------------------------------------------------------------------
role_assignment = authorization.RoleAssignment(
    "blob-contributor-role",
    scope=storage_account.id,
    principal_id=function_app.identity.apply(lambda i: i.principal_id),
    principal_type=authorization.PrincipalType.SERVICE_PRINCIPAL,
    # Storage Blob Data Contributor built-in role
    role_definition_id="/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe",
)

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
pulumi.export("resource_group_name", resource_group.name)
pulumi.export("function_app_name", function_app.name)
pulumi.export(
    "function_app_url",
    function_app.default_host_name.apply(lambda host: f"https://{host}"),
)
pulumi.export("app_insights_name", app_insights.name)
pulumi.export("storage_account_name", storage_account.name)
