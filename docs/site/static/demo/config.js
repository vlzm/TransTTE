// Runtime config for the TransTTE UI on GitHub Pages (task D1).
//
// Set window.API_BASE to the Azure Container Apps FQDN produced by task E (E3),
// e.g. "https://transtte-api.westeurope.azurecontainerapps.io" (no trailing slash).
// Until this is filled with the real FQDN, the warmup spinner will poll a dead
// host and never clear — that is intentional (never expose a cold/unknown API).
window.API_BASE = "https://REPLACE-ME.azurecontainerapps.io"; // TODO(task E3): real ACA FQDN
