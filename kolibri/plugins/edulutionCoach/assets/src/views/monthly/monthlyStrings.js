import { createTranslator } from 'kolibri.utils.i18n';

// Wording shared by the Monthly reports page and its cards.
export const monthlyStrings = createTranslator('MonthlyReportStrings', {
  learnersColumn: { message: 'Learners', context: 'Table column: girls, boys, all.' },
  enrolledColumn: { message: 'Enrolled', context: 'Table column.' },
  activeColumn: { message: 'Active', context: 'Table column: learners who came.' },
  reachedColumn: { message: 'Reached', context: 'Table column (UNESCO measure).' },
  newlyReachedColumn: { message: 'Newly reached', context: 'Table column.' },
  completedColumn: { message: 'Completed', context: 'Table column: resources finished.' },
  sessionsColumn: { message: 'Sessions', context: 'Table column.' },
  watchingColumn: { message: 'Watching', context: 'Table column: video time.' },
  loggedInColumn: { message: 'Logged in', context: 'Table column: time signed in.' },
  girls: { message: 'Girls', context: 'Table row.' },
  boys: { message: 'Boys', context: 'Table row.' },
  notSpecified: { message: 'Not specified', context: 'Table row: gender not recorded.' },
  allLearners: { message: 'All learners', context: 'Table row: total.' },
  active_learners: { message: 'Active learners', context: 'Chart figure.' },
  sessions: { message: 'Sessions', context: 'Chart figure.' },
  completions: { message: 'Resources completed', context: 'Chart figure.' },
  video_watch_seconds: { message: 'Minutes watching', context: 'Chart figure.' },
  reached: { message: 'Reached', context: 'A learner has finished at least one resource.' },
  newlyReached: {
    message: 'Newly reached',
    context: 'A learner finished their first resource in this period.',
  },
  notActive: {
    message: 'Did not come',
    context: 'A learner did not sign in during the period.',
  },
  notReached: {
    message: 'Not yet reached',
    context: 'A learner has not finished any resource yet.',
  },
});

// One of the strings above.
export function monthlyString(key, args) {
  return monthlyStrings.$tr(key, args);
}

// A date as YYYY-MM-DD, in the browser's time zone.
export function isoDate(date) {
  const pad = n => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

// Midday of a YYYY-MM-DD date (or the date part of an ISO time), so
// formatting it never shifts the day.
export function noon(iso) {
  return new Date(String(iso).slice(0, 10) + 'T12:00:00');
}

export function percent(part, whole) {
  return whole ? Math.round((100 * part) / whole) + '%' : '';
}

export const GENDER_KEYS = ['FEMALE', 'MALE', 'NOT_SPECIFIED', 'ALL'];

export function genderLabel(key) {
  return {
    FEMALE: monthlyString('girls'),
    MALE: monthlyString('boys'),
    NOT_SPECIFIED: monthlyString('notSpecified'),
    ALL: monthlyString('allLearners'),
  }[key];
}
