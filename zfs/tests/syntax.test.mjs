import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import test from 'node:test';

const vueScriptPattern = /<script\b[^>]*>([\s\S]*?)<\/script\s*>/gi;

test('Vue syntax extraction checks uppercase and mixed-case script tags', () => {
    const source = '<SCRIPT setup lang="ts">const valid: number = 1;</SCRIPT><sCrIpT>const = ;</ScRiPt>';
    const scripts = [...source.matchAll(vueScriptPattern)].map(match => match[1]);
    assert.equal(scripts.length, 2);
    assert.doesNotThrow(() => stripTypeScriptTypes(scripts[0], { mode: 'transform' }));
    assert.throws(() => stripTypeScriptTypes(scripts[1], { mode: 'transform' }));
});

test('frontend TypeScript and Vue script blocks have valid syntax', () => {
    const root = new URL('../src/', import.meta.url);
    let checked = 0;
    for (const file of readdirSync(root, { recursive: true })) {
        if (!/\.(ts|vue)$/.test(file) || file.endsWith('.d.ts')) continue;
        const source = readFileSync(new URL(file, root), 'utf8');
        const scripts = file.endsWith('.vue')
            ? [...source.matchAll(vueScriptPattern)].map(match => match[1])
            : [source];
        for (const script of scripts) {
            assert.doesNotThrow(() => stripTypeScriptTypes(script, { mode: 'transform' }), file);
            checked++;
        }
    }
    assert.ok(checked > 0);
});
