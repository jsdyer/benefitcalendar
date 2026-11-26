import test from 'node:test';
import assert from 'node:assert/strict';
import {matches, localToday} from '../web/model.mjs';
test('regional subscriptions include Canada-wide programs and exclude other provincial programs', () => {
  const event = {program:'cpp', date:'2027-03-25', region:'CA'};
  assert.equal(matches(event, '', 'AB', '2027-01-01'), true);
  assert.equal(matches({...event, region:'ON'}, '', 'AB', ''), false);
  assert.equal(matches(event, 'oas', '', ''), false);
  assert.equal(matches(event, '', '', '2027-03-26'), false);
  assert.equal(localToday(new Date(2027, 2, 1)), '2027-03-01');
});
