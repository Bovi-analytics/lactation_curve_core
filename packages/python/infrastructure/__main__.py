"""Pulumi infrastructure for the Lactation Curves Function App.

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

import pulumi
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

# Naming prefix based on stack (e.g., "lc-dev")
prefix = f"lc-{stack}"

# Tags applied to all resources
tags = {
    "Environment": stack,
    "Project": "LactationCurves",
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
# App Service Plan (Linux Consumption - Y1 Dynamic tier)
# Free: first 1 million requests and 400,000 GB-s per month included.
# Scales to zero when idle - you only pay for what you use.
# ---------------------------------------------------------------------------
app_service_plan = web.AppServicePlan(
    "consumption-plan",
    resource_group_name=resource_group.name,
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
    name=f"{prefix}-func",
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
            # Required for v2 programming model (function_app.py instead of function.json)
            web.NameValuePairArgs(name="AzureWebJobsFeatureFlags", value="EnableWorkerIndexing"),
            # Required for Linux Consumption plan — the worker process needs
            # a file share even when using WEBSITE_RUN_FROM_PACKAGE.
            web.NameValuePairArgs(
                name="WEBSITE_CONTENTAZUREFILECONNECTIONSTRING",
                value=storage_connection_string,
            ),
            web.NameValuePairArgs(
                name="WEBSITE_CONTENTSHARE",
                value=f"{prefix}-func-content",
            ),
            # Monitoring
            web.NameValuePairArgs(
                name="APPINSIGHTS_INSTRUMENTATIONKEY",
                value=app_insights.instrumentation_key,
            ),
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
