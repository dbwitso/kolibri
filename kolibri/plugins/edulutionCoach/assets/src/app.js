import { get } from '@vueuse/core';
import useUser from 'kolibri.coreVue.composables.useUser';
import redirectBrowser from 'kolibri.utils.redirectBrowser';
import { setChannelInfo } from 'kolibri.coreVue.vuex.actions';
import router from 'kolibri.coreVue.router';
import PageRoot from 'kolibri.coreVue.components.PageRoot';
import KolibriApp from 'kolibri_app';
import routes from './routes';
import pluginModule from './modules/pluginModule';
import { classSectionFor } from './routes/utils';
import fillClassId from './routes/fillClassId';
import { featureForRoute } from './coachFeatures';
import { PageNames } from './constants';

class CoachToolsModule extends KolibriApp {
  get stateSetters() {
    return [setChannelInfo];
  }
  get routes() {
    return routes;
  }
  get RootVue() {
    return PageRoot;
  }
  get pluginModule() {
    return pluginModule;
  }
  ready() {
    // Links built without the class (getRoute('SELECTION_ROOT'), ...) get the
    // class being viewed (see routes/fillClassId.js). getRoute is created
    // when the routes are set up, so wrap it there, before any page renders.
    const initRoutes = router.initRoutes.bind(router);
    router.initRoutes = routes => {
      const vueRouter = initRoutes(routes);
      const wrapped = fillClassId(
        router.getRoute,
        name => router.getRouteDefinition(name),
        () => vueRouter.currentRoute.params.classId || this.store.state.classSummary.id
      );
      router.getRoute = wrapped;
      vueRouter.getRoute = wrapped;
      return vueRouter;
    };
    const { isLearnerOnlyImport } = useUser();
    router.beforeEach((to, from, next) => {
      if (get(isLearnerOnlyImport)) {
        redirectBrowser();
        return;
      }
      // Learners (and signed-out users) get the class list page, which says
      // the page is for coaches and admins. Any other page would ask the
      // server for class data, be refused, and show a blank page.
      const { isCoach, isAdmin, isSuperuser } = this.store.getters;
      if (!(isCoach || isAdmin || isSuperuser) && to.name !== 'CoachClassListPage') {
        next({ name: 'CoachClassListPage', replace: true });
        return;
      }
      // Quizzes or groups turned off for this facility: their pages (an old
      // link or bookmark) open the Class home instead.
      const feature = featureForRoute(to);
      if (feature && !this.store.getters.coachFeatures[feature]) {
        next(
          to.params.classId
            ? { name: PageNames.HOME_PAGE, params: { classId: to.params.classId }, replace: true }
            : { name: 'CoachClassListPage', replace: true }
        );
        return;
      }
      const section = !to.params.classId && classSectionFor(to);
      // A link from inside a class that leaves the class out (e.g. a lesson's
      // Options > Manage resources or Edit details: Vue Router never fills in
      // the optional :classId from the current page) stays in that class.
      const currentClass = from.params.classId || this.store.state.classSummary.id;
      if (section && currentClass && to.name) {
        next({
          name: to.name,
          params: { ...to.params, classId: currentClass },
          query: to.query,
          replace: true,
        });
        return;
      }
      // No class at all yet (e.g. Reports from the menu): choose one first.
      if (section) {
        next({
          name: this.store.getters.userIsMultiFacilityAdmin
            ? 'AllFacilitiesPage'
            : 'CoachClassListPage',
          params: { subtopicName: section },
          replace: true,
        });
        return;
      }
      this.store.dispatch('loading');
      const promises = [];
      // Clear the snackbar at every navigation to prevent it from re-appearing
      // when the next page component mounts.
      if (this.store.state.core.snackbar.isVisible) {
        this.store.dispatch('clearSnackbar');
      }
      this.store.commit('SET_PAGE_NAME', to.name);
      if (
        to.name &&
        !['CoachClassListPage', 'StatusTestPage', 'CoachPrompts', 'AllFacilitiesPage'].includes(
          to.name
        )
      ) {
        if (to.params.classId)
          promises.push(this.store.dispatch('initClassInfo', to.params.classId));
      } else {
        this.store.dispatch('coachNotifications/stopPolling');
      }
      if (this.store.getters.isSuperuser && this.store.state.core.facilities.length === 0) {
        promises.push(this.store.dispatch('getFacilities').catch(() => {}));
      }
      if (promises.length > 0) {
        Promise.all(promises).then(next, error => {
          this.store.dispatch('handleApiError', { error });
        });
      } else {
        next();
      }
    });

    router.afterEach((toRoute, fromRoute) => {
      this.store.dispatch('resetModuleState', { toRoute, fromRoute });
    });
    super.ready();
  }
}

export default new CoachToolsModule();
