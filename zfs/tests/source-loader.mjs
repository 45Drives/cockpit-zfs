import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';

export function sourceFor(file) {
    return readFileSync(new URL(`../src/${file}`, import.meta.url), 'utf8');
}

export function loadFunction(file, name, dependencies = {}) {
    const source = sourceFor(file);
    const match = new RegExp(`^(?:export )?(?:async )?function ${name}(?:<[^\\n]+>)?\\(`, 'm').exec(source);
    assert.ok(match, `Live declaration for ${name}`);
    const tail = source.slice(match.index);
    const end = /^}\r?$/m.exec(tail);
    assert.ok(end, `End of declaration for ${name}`);
    const declaration = tail.slice(0, end.index + end[0].length).replace(/^export /, '');
    const code = stripTypeScriptTypes(declaration);
    return new Function(...Object.keys(dependencies), `${code}\nreturn ${name};`)(...Object.values(dependencies));
}

export function loadManagerMethod(name, dependencies = {}) {
    const source = sourceFor('../../houston-common/houston-common-lib/lib/managers/zfs/manager.ts');
    const match = new RegExp(`^  async ${name}\\(`, 'm').exec(source);
    assert.ok(match, `Manager method ${name}`);
    const tail = source.slice(match.index);
    const end = /^  }\r?$/m.exec(tail);
    assert.ok(end, `End of manager method ${name}`);
    const declaration = tail.slice(0, end.index + end[0].length).replace(/^  async /, 'async function ');
    const code = stripTypeScriptTypes(declaration);
    return new Function(...Object.keys(dependencies), `${code}\nreturn ${name};`)(...Object.values(dependencies));
}