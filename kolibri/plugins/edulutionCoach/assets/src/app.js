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
