import assert from 'node:assert/strict';
import test from 'node:test';
import {residentSelection} from '../ui/resident-selection.js';

const maid = {id:'maid',characterId:'original',bodyKind:'maid'};
const numen = {id:'numen',characterId:'original',bodyKind:'numen'};

test('the default selection retains the bound body across catalogue reordering', () => {
  assert.equal(residentSelection([numen, maid], '', 'original', 'maid'), maid);
  assert.equal(residentSelection([maid, numen], '', 'original', 'numen'), numen);
});

test('an explicit selection never silently changes to a different resident after refresh', () => {
  assert.equal(residentSelection([maid, numen], 'numen', 'original', 'maid'), numen);
  assert.equal(residentSelection([maid], 'numen', 'original', 'maid'), undefined);
  assert.equal(residentSelection([maid], '', '', ''), maid);
});
