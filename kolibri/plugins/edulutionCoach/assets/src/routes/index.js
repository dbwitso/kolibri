import store from 'kolibri.coreVue.vuex.store';
import router from 'kolibri.coreVue.router';
import { ClassesPageNames } from '../../../../edulution/assets/src/constants';
import { PageNames } from '../constants';
import reportRoutes from './reportRoutes';
import planRoutes from './planRoutes';
import { classIdParamRequiredGuard } from './utils';

// Every route below has an explicit `name:` rather than relying on Vue
// Router's fallback of reading `component.name` (see
// kolibri/core/assets/src/router.js's initRoutes), which only works for a
// synchronously-available component object, not a lazy () => import(...).

export default [
  ...planRoutes,
  ...reportRoutes,
  {
    name: 'AllFacilitiesPage',
    path: '/facilities/:subtopicName?',
    component: () => import(/* webpackChunkName: "AllFacilitiesPage" */ '../views/AllFacilitiesPage'),
    props: true,
    handler() {
      store.dispatch('notLoading');
    },
  },
  {
    name: 'CoachClassListPage',
    path: '/:facility_id?/classes/:subtopicName?',
    component: () => import(/* webpackChunkName: "CoachClassListPage" */ '../views/CoachClassListPage'),
    props: true,
    handler(toRoute) {
      // loading state is handled locally
      store.dispatch('notLoading');
      // if user only has access to one facility, facility_id will not be accessible from URL,
      // but always defaulting to userFacilityId would cause problems for multi-facility admins
      const facilityId = toRoute.params.facility_id || store.getters.userFacilityId;
      store.dispatch('setClassList', facilityId).then(
        () => {
          if (!store.getters.classListPageEnabled) {
            // If no class list page, redirect to the first (and only) class and
            // to the originally-selected subtopic, if available
            router.replace({
              name: toRoute.params.subtopicName || PageNames.HOME_PAGE,
              params: { classId: store.state.classList[0].id },
            });
            return;
          }
        },
        error => store.dispatch('handleApiError', { error, reloadOnReconnect: true })
      );
    },
    meta: {
      titleParts: ['classesLabel'],
    },
  },
  {
    name: PageNames.HOME_PAGE,
    path: '/:classId?/home',
    component: () => import(/* webpackChunkName: "HomePage" */ '../views/home/HomePage'),
    handler: (toRoute, fromRoute, next) => {
      if (classIdParamRequiredGuard(toRoute, PageNames.HOME_PAGE, next)) {
        return;
      }
      store.dispatch('notLoading');
    },
    meta: {
      titleParts: ['CLASS_NAME'],
    },
  },
  {
    name: 'HomeActivityPage',
    path: '/:classId/home/activity',
    component: () => import(/* webpackChunkName: "HomeActivityPage" */ '../views/home/HomeActivityPage'),
    handler() {
      store.dispatch('notLoading');
    },
    meta: {
      titleParts: ['activityLabel', 'CLASS_NAME'],
    },
  },
  {
    name: ClassesPageNames.CLASS_LEARNERS_LIST_VIEWER,
    path: '/:classId/learners',
    component: () => import(/* webpackChunkName: "ClassLearnersListPage" */ '../views/ClassLearnersListPage'),
    handler() {
      store.dispatch('notLoading');
    },
  },
  {
    name: 'StatusTestPage',
    path: '/about/statuses',
    component: () => import(/* webpackChunkName: "StatusTestPage" */ '../views/common/status/StatusTestPage'),
    handler() {
      store.dispatch('notLoading');
    },
  },
  {
    name: 'CoachPrompts',
    path: '/coach-prompts',
    component: () => import(/* webpackChunkName: "CoachPrompts" */ '../views/CoachPrompts'),
    handler() {
      store.dispatch('notLoading');
    },
  },
  {
    path: '/',
    // Redirect to AllFacilitiesPage if a superuser and device has > 1 facility
    beforeEnter(to, from, next) {
      if (store.getters.userIsMultiFacilityAdmin) {
        next({ name: 'AllFacilitiesPage', replace: true });
      } else {
        next({ name: 'CoachClassListPage', replace: true });
      }
    },
  },
];
