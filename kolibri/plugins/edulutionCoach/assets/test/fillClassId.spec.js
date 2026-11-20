import fillClassId from '../src/routes/fillClassId';

const definitions = {
  SELECTION_ROOT: { path: '/:classId?/plan/lessons/:lessonId/selection' },
  ReportsLessonLearnerPage: { path: '/:classId?/reports/lessons/:lessonId/learners/:learnerId' },
  CoachClassListPage: { path: '/:facility_id?/classes/:subtopicName?' },
};
const getRoute = (name, params = {}, query = {}) => ({ name, params, query });
const getDefinition = name => definitions[name];

describe('fillClassId', () => {
  const inClass = fillClassId(getRoute, getDefinition, () => 'classA');

  it('adds the current class to a class page link that left it out', () => {
    expect(inClass('SELECTION_ROOT', {}, { last: 'X' })).toEqual({
      name: 'SELECTION_ROOT',
      params: { classId: 'classA' },
      query: { last: 'X' },
    });
    expect(inClass('ReportsLessonLearnerPage', { learnerId: 'l1' }).params).toEqual({
      learnerId: 'l1',
      classId: 'classA',
    });
  });

  it('keeps a class the link names (e.g. another class)', () => {
    expect(inClass('SELECTION_ROOT', { classId: 'classB' }).params.classId).toBe('classB');
  });

  it('leaves links to pages without a class alone', () => {
    expect(inClass('CoachClassListPage', {}).params).toEqual({});
  });

  it('adds nothing when no class is being viewed', () => {
    const noClass = fillClassId(getRoute, getDefinition, () => null);
    expect(noClass('SELECTION_ROOT', {}).params).toEqual({});
  });
});
