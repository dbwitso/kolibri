import store from 'kolibri.coreVue.vuex.store';
import { PageNames } from '../constants';

/**
 * The coach section a route needing a class belongs to, or null if the
 * route doesn't need one. The side menu and the bottom bar link to
 * Reports and Plan with the current page's class, so from a page with no
 * class they open #/reports or #/plan: the page then has no class data and
 * says the user must be a coach. Such a route is sent to the class list,
 * which opens the chosen class in this section.
 */
export function classSectionFor(route) {
  const paths = route.matched.map(record => record.path);
  if (!paths.some(path => path.includes(':classId'))) {
    return null;
  }
  // A page that needs nothing but the class (such as Attendance, which the
  // coach menu links to) opens itself once a class is chosen.
  const own = paths[paths.length - 1];
  if (route.name && (own.match(/:/g) || []).length === 1) {
    return route.name;
  }
  if (paths.some(path => path.includes('/reports'))) {
    return PageNames.REPORTS_PAGE;
  }
  if (paths.some(path => path.includes('/plan'))) {
    return PageNames.PLAN_PAGE;
  }
  return PageNames.HOME_PAGE;
}

export function classIdParamRequiredGuard(toRoute, subtopicName, next) {
  if (!toRoute.params.classId) {
    const redirectPage = store.getters.userIsMultiFacilityAdmin
      ? 'AllFacilitiesPage'
      : 'CoachClassListPage';

    next({
      name: redirectPage,
      params: { subtopicName },
    });
    store.commit('CORE_SET_PAGE_LOADING', false);
    return true;
  }
}
