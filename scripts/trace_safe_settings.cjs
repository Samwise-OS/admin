// Preload with NODE_OPTIONS to record only bounded Safe-Settings write attempts.
const diagnostics = require('node:diagnostics_channel')
const fs = require('node:fs')
const expectedOrigin = process.env.SAFE_SETTINGS_TRACE_API_ORIGIN || 'https://api.github.com'
const managed = new Set(['admin', 'baseline-canary'])
const receipt = { observed_requests: 0, managed_config_mutation_requests: 0, unclassified_managed_writes: 0, trace_errors: 0 }

diagnostics.channel('undici:request:create').subscribe((event) => {
  try {
    const request = event && event.request
    if (!request) throw new Error('request metadata missing')
    receipt.observed_requests += 1
    if (String(request.origin).replace(/\/$/, '') !== expectedOrigin) return
    const path = String(request.path).split('?', 1)[0]
    const parts = path.match(/^\/repos\/([^/]+)\/([^/]+)(\/.*)?$/i)
    if (!parts || parts[1].toLowerCase() !== 'samwise-os' || !managed.has(parts[2].toLowerCase())) return
    const method = String(request.method).toUpperCase()
    const suffix = parts[3] || ''
    if ((method === 'POST' || method === 'PATCH') && /^\/check-runs(?:\/\d+)?$/.test(suffix)) return
    if (method === 'PATCH' && suffix === '') receipt.managed_config_mutation_requests += 1
    else if (method === 'POST' && suffix === '/rulesets') receipt.managed_config_mutation_requests += 1
    else if ((method === 'PUT' || method === 'DELETE') && /^\/rulesets\/\d+$/.test(suffix)) receipt.managed_config_mutation_requests += 1
    else if (/^(POST|PATCH|PUT|DELETE)$/.test(method)) receipt.unclassified_managed_writes += 1
  } catch {
    receipt.trace_errors += 1
  }
})

process.on('exit', () => {
  const supported = receipt.observed_requests > 0 && receipt.trace_errors === 0 && receipt.unclassified_managed_writes === 0
  fs.writeSync(1, `SAFE_SETTINGS_HTTP_RECEIPT ${JSON.stringify({ ...receipt, supported })}\n`)
  if (!supported && (process.exitCode == null || process.exitCode === 0)) process.exitCode = 78
})
