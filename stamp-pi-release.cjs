const {randomUUID} = require('node:crypto');
const {readFileSync, writeFileSync} = require('node:fs');

const version = randomUUID();
const html = readFileSync('pi.html', 'utf8');
const stamped = html
    .replace('name="pi-release" content="local"', 'name="pi-release" content="' + version + '"')
    .replaceAll('?release=local', '?release=' + version);
if (stamped === html) throw new Error('Missing Pi release markers in pi.html');

writeFileSync('pi.html', stamped);
writeFileSync('pi-release.json', JSON.stringify({
    version,
    branch: process.env.VERCEL_GIT_COMMIT_REF || null,
    commit: process.env.VERCEL_GIT_COMMIT_SHA || null,
    environment: process.env.VERCEL_ENV || null,
}) + '\n');
