import { get } from '@vueuse/core';
import store from 'kolibri.coreVue.vuex.store';
import router from 'kolibri.coreVue.router';
import useUser from 'kolibri.coreVue.composables.useUser';
import useChannels from '../composables/useChannels';
import { PageNames, ClassesPageNames, KolibriStudioId } from '../constants';
import { showKnowledgemap } from '../modules/examViewer/handlers';
import assessmentsEnabled from '../assessmentsEnabled';

import classesRoutes from './classesRoutes';

const { channelsMap, fetchChannels } = useChannels();
const { isUserLoggedIn } = useUser();

function unassignedContentGuard(next) {
  const { canAccessUnassignedContent } = store.getters;
  if (!canAccessUnassignedContent) {
    // Learners who may only see assigned content go to Home, which lists
    // their lessons. (Signed-out users have no Home, so go to classes.)
    const name = get(isUserLoggedIn) ? PageNames.HOME : ClassesPageNames.ALL_CLASSES;
    next({ name, replace: true });
    // True so the caller stops: it must not go on to load the page.
    return true;
  }
  return false;
}

const optionalDeviceIdPathSegment = `/:deviceId([a-f0-9]{32}|${KolibriStudioId})?`;

export default [
  {
    name: PageNames.ROOT,
    path: '/',
    redirect: () => {
      if (get(isUserLoggedIn)) {
        return { name: PageNames.HOME, replace: true };
      }
      return { name: PageNames.LIBRARY, replace: true };
    },
  },
  {
    name: PageNames.HOME,
    path: '/home',
    component: () => import(/* webpackChunkName: "HomePage" */ '../views/HomePage'),
    handler(to, from, next) {
      if (!get(isUserLoggedIn)) {
        next({ name: PageNames.LIBRARY, replace: true });
        return;
      }
      store.commit('CORE_SET_PAGE_LOADING', true);
    },
  },
  // Next class routes under home page
  ...classesRoutes.map(route => {
    return {
      ...route,
      path: `/home${route.path}`,
    };
  }),
  {
    name: PageNames.LIBRARY,
    path: '/library' + optionalDeviceIdPathSegment,
    handler: (to, from, next) => {
      if (unassignedContentGuard(next)) {
        return;
      }
      if (!get(isUserLoggedIn) && to.params.deviceId) {
        next({ name: PageNames.LIBRARY, replace: true });
        return;
      }
      store.commit('CORE_SET_PAGE_LOADING', true);
    },
    component: () => import(/* webpackChunkName: "LibraryPage" */ '../views/LibraryPage'),
    props: route => {
      return {
        deviceId: route.params.deviceId,
      };
    },
  },
  {
    name: PageNames.CONTENT_UNAVAILABLE,
    path: '/resources-unavailable',
    handler: () => {
      store.commit('SET_PAGE_NAME', PageNames.CONTENT_UNAVAILABLE);
      store.commit('CORE_SET_PAGE_LOADING', false);
      store.commit('CORE_SET_ERROR', null);
    },
    component: () => import(/* webpackChunkName: "ContentUnavailablePage" */ '../views/ContentUnavailablePage'),
  },
  {
    // Handle historic channel page with redirect
    name: 'TopicsPage',
    path: '/topics/:channel_id',
    handler: (to, from, next) => {
      if (unassignedContentGuard(next)) {
        return;
      }
      return fetchChannels().then(() => {
        const { channel_id } = to.params;
        const channel = get(channelsMap)[channel_id];
        if (channel) {
          const id = get(channelsMap)[channel_id].root;
          router.replace({
            name: PageNames.TOPICS_TOPIC,
            params: {
              id,
            },
          });
          return;
        }
        router.replace({ name: PageNames.ROOT });
      });
    },
    component: () => import(/* webpackChunkName: "TopicsPage" */ '../views/TopicsPage'),
  },
  {
    // Handle redirect for links without the /folder appended
    path: `/topics${optionalDeviceIdPathSegment}/t/:id`,
    redirect: `/topics${optionalDeviceIdPathSegment}/t/:id/:subtopic?/folders`,
  },
  // Have to put TOPICS_TOPIC_SEARCH before TOPICS_TOPIC to ensure
  // search gets picked up before being interpreted as a subtopic id.
  {
    name: PageNames.TOPICS_TOPIC_SEARCH,
    path: `/topics${optionalDeviceIdPathSegment}/t/:id/search`,
    handler: (toRoute, fromRoute, next) => {
      if (unassignedContentGuard(next)) {
        return;
      }
      showKnowledgemap(store, { contentId: toRoute.params.id });
    },
    component: () => import(/* webpackChunkName: "TopicsPage" */ '../views/TopicsPage'),
    props: true,
  },
  {
    name: PageNames.TOPICS_TOPIC,
    path: `/topics${optionalDeviceIdPathSegment}/t/:id/:subtopic?/folders`,
    handler: (toRoute, fromRoute, next) => {
      if (unassignedContentGuard(next)) {
        return;
      }
      showKnowledgemap(store, { contentId: toRoute.params.id });
    },
    component: () => import(/* webpackChunkName: "TopicsPage" */ '../views/TopicsPage'),
    props: true,
  },
  {
    name: PageNames.TOPICS_CONTENT,
    path: `/topics${optionalDeviceIdPathSegment}/c/:id`,
    component: () => import(/* webpackChunkName: "TopicsContentPage" */ '../views/TopicsContentPage'),
    props: true,
  },
  {
    name: PageNames.BOOKMARKS,
    path: '/bookmarks',
    handler: (to, from, next) => {
      if (unassignedContentGuard(next)) {
        return;
      }
      store.commit('SET_PAGE_NAME', PageNames.BOOKMARKS);
      store.commit('CORE_SET_PAGE_LOADING', false);
      next();
    },
    component: () => import(/* webpackChunkName: "BookmarkPage" */ '../views/BookmarkPage.vue'),
  },
  {
    name: PageNames.EXPLORE_LIBRARIES,
    path: '/explore_libraries',
    component: () => import(/* webpackChunkName: "ExploreLibrariesPage" */ '../views/ExploreLibrariesPage'),
    handler: (to, from, next) => {
      if (unassignedContentGuard(next)) {
        return;
      }
      if (!get(isUserLoggedIn)) {
        next({ name: PageNames.LIBRARY, replace: true });
        return;
      }
    },
  },
  {
    name: PageNames.ASSESSMENT_HISTORY,
    path: '/assessmentHistory',
    handler: (to, from, next) => {
      if (!get(isUserLoggedIn) || !assessmentsEnabled) {
        next({ name: PageNames.ROOT, replace: true });
      }
    },
    component: () => import(/* webpackChunkName: "AssessmentHistoryPage" */ '../views/AssessmentHistoryPage')
  },
  {
    path: '*',
    redirect: '/',
  },
];
