// Presets edit a draft. They do not probe the network, save or connect.
export function connectionKind(server = {}) {
  const host = (server.host || '').trim().toLowerCase();
  if (!host && server.connection_type === 'custom') return 'custom';
  if (host === 'micro.kangqiang.site' && Number(server.port) === 25702) return 'qiandeng';
  return ['', 'localhost', '127.0.0.1', '::1', '[::1]'].includes(host) ? 'vanilla' : 'custom';
}

export function javaAddress(host, port) {
  if (typeof host !== 'string' || !Number.isInteger(port) || port < 1 || port > 65535) return '';
  host = host.trim();
  if (!host || !/^(?:[a-z0-9_.-]+|\[?[0-9a-f:.]+\]?)$/i.test(host)) return '';
  if (host.startsWith('[') !== host.endsWith(']') || (host.includes(':') && host.split(':').length < 3)) return '';
  if (host.includes(':') && !host.startsWith('[')) host = `[${host}]`;
  return `${host}:${port}`;
}

export function applyConnectionPreset(draft, preset) {
  if (!['vanilla', 'custom', 'qiandeng'].includes(preset)) throw new Error('Unknown connection preset');
  const server = draft.server || {};
  if (preset === connectionKind(server) && server.host) return {...draft, server: {...server}};
  const endpoint = preset === 'qiandeng' ? {host: 'micro.kangqiang.site', port: 25702} :
    {host: preset === 'vanilla' ? '127.0.0.1' : '', port: 25565};
  return {...draft, server: {...server, ...endpoint, version: '1.21.1',
    connection_type: preset === 'vanilla' ? 'local' : 'custom',
    ...('login_config_file' in server && {login_config_file: ''})}};
}
