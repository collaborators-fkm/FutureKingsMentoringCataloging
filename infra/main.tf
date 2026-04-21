provider "azurerm" {
  features {}
}
resource "azurerm_resource_group" "resource_group" {
  location = "eastus"
  name     = "fkm-ppt-catalog"
}
resource "azurerm_service_plan" "service_plan" {
  location            = "centralus"
  name                = "ASP-fkmpptcatalog-a032"
  os_type             = "Linux"
  resource_group_name = azurerm_resource_group.resource_group.name
  sku_name            = "F1"
}
resource "azurerm_linux_web_app" "app_service" {
  app_settings = {
    CLIENT_ID                        = var.client_id
    TENANT_ID                        = var.tenant_id
    WEBSITE_AUTH_AAD_ALLOWED_TENANTS = var.tenant_id
    SITE_HOSTNAME                    = var.site_hostname
    SITE_PATH                        = var.site_path

    CLIENT_SECRET_VALUE                      = var.client_secret_value
    MICROSOFT_PROVIDER_AUTHENTICATION_SECRET = var.microsoft_provider_authentication_secret
    OPENAI_API_KEY                           = var.openai_api_key

    DATABASE_PATH                  = "/home/data/catalog.sqlite3"
    SCM_DO_BUILD_DURING_DEPLOYMENT = "true"
  }
  auth_settings_v2 {
    auth_enabled             = true
    default_provider         = "azureactivedirectory"
    forward_proxy_convention = "NoProxy"
    http_route_api_prefix    = "/.auth"
    require_authentication   = true
    require_https            = true
    runtime_version          = "~1"
    unauthenticated_action   = "RedirectToLoginPage"
    active_directory_v2 {
      allowed_applications        = [var.easy_auth_client_id]
      allowed_audiences           = ["api://${var.easy_auth_client_id}"]
      client_id                   = var.easy_auth_client_id
      client_secret_setting_name  = "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET"
      tenant_auth_endpoint        = "https://sts.windows.net/${var.tenant_id}/v2.0"
      www_authentication_disabled = false
    }
    login {
      cookie_expiration_convention      = "FixedTime"
      cookie_expiration_time            = "08:00:00"
      nonce_expiration_time             = "00:05:00"
      preserve_url_fragments_for_logins = false
      token_refresh_extension_time      = 72
      token_store_enabled               = true
      validate_nonce                    = true
    }
  }
  ftp_publish_basic_authentication_enabled       = false
  https_only                                     = true
  location                                       = azurerm_service_plan.service_plan.location
  name                                           = "catalog-service"
  resource_group_name                            = azurerm_resource_group.resource_group.name
  service_plan_id                                = azurerm_service_plan.service_plan.id
  webdeploy_publish_basic_authentication_enabled = false
  site_config {
    always_on               = false
    app_command_line        = "python app.py"
    ftps_state              = "Disabled"
    minimum_tls_version     = "1.2"
    scm_minimum_tls_version = "1.2"
    application_stack {
      python_version = "3.14"
    }
  }
}
