// Preload with NODE_OPTIONS to record only bounded Safe-Settings write attempts.
const diagnostics = require('node:diagnostics_channel')
const fs = require('node:fs')
const path = require('node:path')
const expectedOrigin = process.env.SAFE_SETTINGS_TRACE_API_ORIGIN || 'https://api.github.com'
const root = path.resolve(__dirname, '..')
const configDirectory = path.join(root, 'config')
if (fs.lstatSync(configDirectory).isSymbolicLink()) throw new Error('config must be a real directory')
const readAuthority = (name) => {
  const file = path.join(configDirectory, name)
  if (fs.lstatSync(file).isSymbolicLink()) throw new Error(`${name} must not be a symlink`)
  const resolved = fs.realpathSync(file)
  if (!resolved.startsWith(`${root}${path.sep}`)) throw new Error(`${name} must resolve inside the checkout`)
  return JSON.parse(fs.readFileSync(resolved, 'utf8'))
}
const organizationConfig = readAuthority('organization.json')
const repositoriesConfig = readAuthority('repositories.json')
const organization = repositoriesConfig.organization
const adminRepository = organizationConfig.admin_repository
const repositoryEntries = repositoriesConfig.repositories
const validName = (name) => typeof name === 'string'
  && (name === '.github' || /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name))
if (organization !== 'Samwise-OS' || repositoriesConfig.organization_id !== 349008063
  || organizationConfig.organization !== 'Samwise-OS' || organizationConfig.organization_id !== 349008063
  || adminRepository !== 'admin'
  || !Array.isArray(repositoryEntries)) {
  throw new Error('Repository authority manifests must identify the authorized Samwise-OS organization and admin repository')
}
const repositoryNames = repositoryEntries.map((entry) => entry && entry.name)
if (repositoryNames.some((name) => !validName(name))
  || new Set(repositoryNames).size !== repositoryNames.length
  || repositoryNames.includes(adminRepository)) {
  throw new Error('Repository authority manifests contain invalid or duplicate managed names')
}
const managed = new Set([adminRepository, ...repositoryNames])
const receipt = {
  observed_requests: 0,
  observed_expected_origin_requests: 0,
  observed_managed_repository_requests: 0,
  managed_config_mutation_requests: 0,
  unclassified_managed_writes: 0,
  trace_errors: 0,
}

diagnostics.channel('undici:request:create').subscribe((event) => {
  try {
    const request = event && event.request
    if (!request) throw new Error('request metadata missing')
    receipt.observed_requests += 1
    if (String(request.origin).replace(/\/$/, '') !== expectedOrigin) return
    receipt.observed_expected_origin_requests += 1
    const path = String(request.path).split('?', 1)[0]
    const parts = path.match(/^\/repos\/([^/]+)\/([^/]+)(\/.*)?$/i)
    if (!parts || parts[1].toLowerCase() !== organization.toLowerCase()
      || !managed.has(parts[2].toLowerCase())) return
    receipt.observed_managed_repository_requests += 1
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
  const supported = receipt.observed_expected_origin_requests > 0
    && receipt.observed_managed_repository_requests > 0
    && receipt.trace_errors === 0
    && receipt.unclassified_managed_writes === 0
  fs.writeSync(1, `SAFE_SETTINGS_HTTP_RECEIPT ${JSON.stringify({ ...receipt, supported })}\n`)
  if (!supported && (process.exitCode == null || process.exitCode === 0)) process.exitCode = 78
})
