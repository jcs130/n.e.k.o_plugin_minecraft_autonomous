/** Distributor-only build. Keep the canonical core external and shared with the body. */
import {createRequire} from 'node:module';
import {readFile, writeFile} from 'node:fs/promises';
import {resolve, relative, isAbsolute} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';

const [checkout, esbuildModule, pack] = process.argv.slice(2).map(value => resolve(value));
if (!checkout || !esbuildModule || !pack) throw Error('Supply explicit checkout, esbuild module and output pack paths');
const revision = execFileSync('git', ['-C', checkout, 'rev-parse', 'HEAD'], {encoding:'utf8'}).trim();
const metadata = JSON.parse(await readFile(resolve(pack, 'source.json'), 'utf8'));
if (revision !== metadata.engine.source_revision) throw Error('Server source revision differs from the fixed engine source');
const entry = 'integrations/qiandengji/engine/index.ts';
const dirty = execFileSync('git', ['-C', checkout, 'status', '--porcelain', '--', 'integrations/qiandengji/engine'], {encoding:'utf8'});
if (dirty.trim()) throw Error('Build the original Git engine source, not a dirty working tree');
const {build, version} = createRequire(import.meta.url)(esbuildModule);
if (version !== '0.28.2') throw Error('Use the recorded esbuild 0.28.2');
const allowedImports = ['agent-mc-world/extension','agent-mc-world/tactics','vec3','node:path','node:crypto','node:zlib'];
const result = await build({absWorkingDir:checkout, entryPoints:[entry], bundle:true, write:false,
  format:'esm', platform:'node', target:'node22', packages:'external', sourcemap:false, metafile:true});
for (const name of Object.keys(result.metafile.inputs)) {
  const path = relative(checkout, resolve(checkout,name)).replaceAll('\\','/');
  if (isAbsolute(path) || !path.startsWith('integrations/qiandengji/engine/')) throw Error('Unexpected source dependency: '+path);
}
for (const output of Object.values(result.metafile.outputs)) for (const dep of output.imports) {
  if (!dep.external || !allowedImports.includes(dep.path))
    throw Error('Unexpected runtime import: '+dep.path);
}
const bytes = result.outputFiles[0].contents;
await writeFile(resolve(pack, 'engine.mjs'), bytes);
metadata.engine = {...metadata.engine, source_path:entry, bundler:'esbuild@'+version,
  sha256:createHash('sha256').update(bytes).digest('hex'), bytes:bytes.length,
  source_files:Object.keys(result.metafile.inputs).length, external:allowedImports};
await writeFile(resolve(pack, 'source.json'), JSON.stringify(metadata,null,2)+'\n');
console.log(JSON.stringify(metadata.engine));
