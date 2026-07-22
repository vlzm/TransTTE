// Runtime config for the TransTTE UI on GitHub Pages (task D1).
//
// window.API_BASE points at the Azure Container Apps FQDN from task E (no trailing
// slash). index.js sends /health and /get_path here. If it is ever wrong/dead, the
// warmup spinner will poll forever and never clear — that is intentional (never
// expose a cold/unknown API).
window.API_BASE = "https://transtte-api.ambitioustree-14375a19.westeurope.azurecontainerapps.io";
