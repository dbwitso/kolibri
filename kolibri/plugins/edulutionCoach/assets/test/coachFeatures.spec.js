import coachFeatures, { featureForRoute } from '../src/coachFeatures';

jest.mock('plugin_data', () => ({
  coach_features: {
    facilityOff: { quizzes: false, groups: false },
    facilityQuizzesOff: { quizzes: false, groups: true },
  },
}));

function route(...paths) {
  return { matched: paths.map(path => ({ path })) };
}

describe('coachFeatures', () => {
  it('reads the facility settings', () => {
    expect(coachFeatures('facilityOff')).toEqual({ quizzes: false, groups: false });
    expect(coachFeatures('facilityQuizzesOff')).toEqual({ quizzes: false, groups: true });
  });

  it('is on for a facility with nothing set', () => {
    expect(coachFeatures('otherFacility')).toEqual({ quizzes: true, groups: true });
  });
});

describe('featureForRoute', () => {
  it('finds quiz pages in Plan and Reports', () => {
    expect(featureForRoute(route('/:classId/plan/quizzes/new/'))).toBe('quizzes');
    expect(featureForRoute(route('/:classId?/reports/quizzes/:quizId'))).toBe('quizzes');
    expect(featureForRoute(route('/:classId?/reports/learners/:learnerId/quizzes/:quizId'))).toBe(
      'quizzes'
    );
  });

  it('finds group pages in Plan and Reports', () => {
    expect(featureForRoute(route('/:classId/plan/groups/:groupId'))).toBe('groups');
    expect(featureForRoute(route('/:classId?/reports/groups/:groupId/lessons/:lessonId'))).toBe(
      'groups'
    );
  });

  it('leaves other pages alone', () => {
    expect(featureForRoute(route('/:classId?/plan/lessons'))).toBe(null);
    expect(featureForRoute(route('/:classId?/reports/attendance'))).toBe(null);
  });
});
