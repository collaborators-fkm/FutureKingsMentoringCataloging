variable "client_id" {
  type = string
}

variable "client_secret_value" {
  type      = string
  sensitive = true
}

variable "easy_auth_client_id" {
  type = string
}

variable "microsoft_provider_authentication_secret" {
  type      = string
  sensitive = true
}

variable "openai_api_key" {
  type      = string
  sensitive = true
}

variable "site_hostname" {
  type = string
}

variable "site_path" {
  type = string
}

variable "tenant_id" {
  type = string
}