import { classSectionFor } from '../src/routes/utils';
import { PageNames } from '../src/constants';

jest.mock('kolibri.coreVue.vuex.store', () => ({}));

function route(...paths) {
  return { matched: paths.map(path => ({ path })) };
}

describe('classSectionFor', () => {
  it('sends a Reports page with no class to the Reports section', () => {
    expect(classSectionFor(route('/:classId?/reports/overview'))).toBe(PageNames.REPORTS_PAGE);
  });

  it('sends a Plan page with no class to the Plan section', () => {
    expect(classSectionFor(route('/:classId?/plan/lessons'))).toBe(PageNames.PLAN_PAGE);
  });

  it('sends other class pages to the class home', () => {
    expect(classSectionFor(route('/:classId?/home'))).toBe(PageNames.HOME_PAGE);
  });

  it('leaves pages that need no class alone', () => {
    expect(classSectionFor(route('/:facility_id?/classes/:subtopicName?'))).toBe(null);
    expect(classSectionFor(route('/about/statuses'))).toBe(null);
  });
});
