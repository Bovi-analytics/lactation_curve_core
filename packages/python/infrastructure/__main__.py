"""Pulumi infrastructure for the MilkBot Function App.

Creates the following Azure resources:
  - Resource Group
  - Storage Account (required backing store for Function App)
  - Log Analytics Workspace (PerGB2018 - first 5 GB/month free via App Insights)
  - Application Insights (monitoring)
  - App Service Plan (Linux Consumption Y1 tier - serverless, free for first 1M requests/mo)
  - Function App (Python 3.12, ASGI wrapping FastAPI)

Deployment approach:
  Pulumi manages infrastructure only. App code is deployed separately using
  `func azure functionapp publish` (Azure Functions Core Tools). The Function
  App uses Azure Files mounting for its content storage.
"""

import hashlib
from pathlib import Path

import pulumi
from dotenv import dotenv_values
from pulumi_azure_native import (
    applicationinsights,
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

# Load environment variables from .env.{stack}
env_file = Path(__file__).parent / f".env.{stack}"
if not env_file.exists():
    raise FileNotFoundError(f"Environment file not found: {env_file}")
env = dotenv_values(env_file)

location = env.get("LOCATION")
if not location:
    raise ValueError(f"LOCATION not set in {env_file}")

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
# Resource Group (existing - looked up from .env.{stack})
# ---------------------------------------------------------------------------
subscription_id = config.require("subscriptionId")
suffix = hashlib.md5(subscription_id.encode()).hexdigest()[:6]
resource_group_name = env.get("RESOURCE_GROUP")
if not resource_group_name:
    raise ValueError(f"RESOURCE_GROUP not set in {env_file}")

resource_group = resources.ResourceGroup.get(
    "resource-group",
    id=pulumi.Output.concat(
        "/subscriptions/",
        subscription_id,
        "/resourceGroups/",
        resource_group_name,
    ),
)

# ---------------------------------------------------------------------------
# Storage Account
# Cheapest option: Standard_LRS (locally redundant, no geo-replication)
# ---------------------------------------------------------------------------
storage_account = storage.StorageAccount(
    "storage-account",
    resource_group_name=resource_group.name,
    location=location,
    # Storage account names must be globally unique, 3-24 chars, lowercase alphanumeric
    account_name=f"{prefix.replace('-', '')}{suffix}",
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
# Log Analytics Workspace (PerGB2018 - pay-as-you-go, first 5 GB/month free via App Insights)
# 31 days is the minimum retention for this SKU.
# ---------------------------------------------------------------------------
log_analytics = operationalinsights.Workspace(
    "log-analytics",
    resource_group_name=resource_group.name,
    location=location,
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
    location=location,
    resource_name_=f"{prefix}-insights",
    kind="web",
    application_type=applicationinsights.ApplicationType.WEB,
    workspace_resource_id=log_analytics.id,
    retention_in_days=30,
    tags=tags,
)

# ---------------------------------------------------------------------------
# App Service Plan (Linux Consumption - Y1 Dynamic tier)
# Free: first 1 million requests and 400,000 GB-s per month included.
# Scales to zero when idle - you only pay for what you use.
# ---------------------------------------------------------------------------
app_service_plan = web.AppServicePlan(
    "consumption-plan",
    resource_group_name=resource_group.name,
    location=location,
    name=f"{prefix}-plan",
    sku=web.SkuDescriptionArgs(
        name="Y1",
        tier="Dynamic",
    ),
    kind="linux",
    reserved=True,  # Required for Linux
    tags=tags,
)

# ---------------------------------------------------------------------------
# Function App
# ---------------------------------------------------------------------------
milkbot_key = config.get_secret("milkbotKey") or ""

function_app = web.WebApp(
    "function-app",
    resource_group_name=resource_group.name,
    location=location,
    name=f"{prefix}-{suffix}-func",
    kind="functionapp,linux",
    reserved=True,
    server_farm_id=app_service_plan.id,
    https_only=True,
    site_config=web.SiteConfigArgs(
        linux_fx_version="PYTHON|3.12",
        ftps_state=web.FtpsState.DISABLED,
        min_tls_version="1.2",
        app_settings=[
            # Azure Functions runtime config
            web.NameValuePairArgs(name="AzureWebJobsStorage", value=storage_connection_string),
            web.NameValuePairArgs(name="FUNCTIONS_WORKER_RUNTIME", value="python"),
            web.NameValuePairArgs(name="FUNCTIONS_EXTENSION_VERSION", value="~4"),
            # Required for Python v2 programming model (decorator-based function discovery)
            web.NameValuePairArgs(name="AzureWebJobsFeatureFlags", value="EnableWorkerIndexing"),
            # Note: WEBSITE_CONTENTAZUREFILECONNECTIONSTRING and WEBSITE_CONTENTSHARE
            # are managed by `func azure functionapp publish` — do not set them here
            # or Pulumi and func will fight over them on every deploy.
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
