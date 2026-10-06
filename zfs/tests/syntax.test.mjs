import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import test from 'node:test';

test('frontend TypeScript and Vue script blocks have valid syntax', () => {
    const root = new URL('../src/', import.meta.url);
    let checked = 0;
    for (const file of readdirSync(root, { recursive: true })) {
        if (!/\.(ts|vue)$/.test(file) || file.endsWith('.d.ts')) continue;
        const source = readFileSync(new URL(file, root), 'utf8');
        const scripts = file.endsWith('.vue')
            ? [...source.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map(match => match[1])
            : [source];
        for (const script of scripts) {
            assert.doesNotThrow(() => stripTypeScriptTypes(script, { mode: 'transform' }), file);
            checked++;
        }
    }
    assert.ok(checked > 0);
});