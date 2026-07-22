// Runtime config for the TransTTE UI (task D1).
//
// window.API_BASE is the origin the UI sends /health and /get_path to.
// Leave it empty here: when this page is served by the backend itself,
// index.js falls back to the current origin (same-origin, no CORS needed).
//
// The GitHub Pages copy of this file (docs/site/static/demo/config.js) instead
// points at the Azure Container Apps FQDN produced by task E.
window.API_BASE = "";
