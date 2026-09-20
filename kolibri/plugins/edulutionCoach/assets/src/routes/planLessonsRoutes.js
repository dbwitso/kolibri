import store from 'kolibri.coreVue.vuex.store';
import {
  showLessonResourceContentPreview,
  showLessonResourceSelectionRootPage,
  showLessonResourceSelectionTopicPage,
  showLessonSelectionContentPreview,
  showLessonResourceSearchPage,
  showLessonResourceBookmarks,
  showLessonResourceBookmarksMain,
} from '../modules/lessonResources/handlers';
import { showLessonSummaryPage } from '../modules/lessonSummary/handlers';
import { LessonsPageNames } from '../constants/lessonsConstants';
import { PageNames } from '../constants';

import { useLessons } from '../composables/useLessons';

import { classIdParamRequiredGuard } from './utils';

const CLASS = '/:classId?/plan';
const LESSON = '/lessons/:lessonId';
const ALL_LESSONS = '/lessons';
const SELECTION = '/selection';
const TOPIC = '/topic/:topicId';
const SEARCH = '/search/:searchTerm';
const PREVIEW = '/preview/:contentId';

function path(...args) {
  return args.join('');
}

const { showLessonsRootPage } = useLessons();

export default [
  {
    name: LessonsPageNames.PLAN_LESSONS_ROOT,
    path: path(CLASS, ALL_LESSONS),
    component: () => import(/* webpackChunkName: "LessonsRootPage" */ '../views/plan/LessonsRootPage'),
    handler(toRoute, fromRoute, next) {
      if (classIdParamRequiredGuard(toRoute, PageNames.PLAN_PAGE, next)) {
        return;
      }
      showLessonsRootPage(store, toRoute.params.classId);
    },
    meta: {
      titleParts: ['lessonsLabel', 'CLASS_NAME'],
    },
  },
  {
    name: LessonsPageNames.LESSON_CREATION_ROOT,
    path: path(CLASS, ALL_LESSONS, '/new'),
    component: () => import(/* webpackChunkName: "LessonCreationPage" */ '../views/plan/LessonCreationPage'),
  },
  {
    name: LessonsPageNames.SUMMARY,
    path: path(CLASS, LESSON),
    component: () => import(/* webpackChunkName: "LessonSummaryPage" */ '../views/plan/LessonSummaryPage'),
    handler(toRoute, fromRoute, next) {
      if (classIdParamRequiredGuard(toRoute, PageNames.PLAN_PAGE, next)) {
        return;
      }
      return showLessonSummaryPage(store, toRoute.params);
    },
    meta: {
      titleParts: ['LESSON_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'LessonEditDetailsPage',
    path: path(CLASS, LESSON, '/edit'),
    component: () => import(/* webpackChunkName: "LessonEditDetailsPage" */ '../views/plan/LessonEditDetailsPage'),
  },
  {
    name: LessonsPageNames.SELECTION_ROOT,
    path: path(CLASS, LESSON, SELECTION),
    component: () => import(/* webpackChunkName: "LessonResourceSelectionPage" */ '../views/plan/LessonResourceSelectionPage'),
    handler(toRoute) {
      showLessonResourceSelectionRootPage(store, toRoute.params);
    },
  },
  {
    name: LessonsPageNames.SELECTION,
    path: path(CLASS, LESSON, SELECTION, TOPIC),
    component: () => import(/* webpackChunkName: "LessonResourceSelectionPage" */ '../views/plan/LessonResourceSelectionPage'),
    handler(toRoute, fromRoute) {
      // HACK if last page was LessonContentPreviewPage, then we need to make sure
      // to immediately autosave just in case a change was made there. This gets
      // called whether or not a change is made, because we don't track changes
      // enough steps back.
      let preHandlerPromise;
      if (fromRoute.name === LessonsPageNames.SELECTION_CONTENT_PREVIEW) {
        preHandlerPromise = store.dispatch('lessonSummary/saveLessonResources', {
          lessonId: toRoute.params.lessonId,
          resources: store.state.lessonSummary.workingResources,
        });
      } else {
        preHandlerPromise = Promise.resolve();
      }
      preHandlerPromise.then(() => {
        showLessonResourceSelectionTopicPage(store, toRoute.params);
      });
    },
  },
  {
    name: LessonsPageNames.SELECTION_SEARCH,
    path: path(CLASS, LESSON, SELECTION, SEARCH),
    component: () => import(/* webpackChunkName: "LessonResourceSelectionPage" */ '../views/plan/LessonResourceSelectionPage'),
    handler(toRoute) {
      showLessonResourceSearchPage(store, toRoute.params, toRoute.query);
    },
  },
  {
    name: LessonsPageNames.LESSON_SELECTION_BOOKMARKS,
    path: path(CLASS, LESSON, SELECTION, TOPIC),
    component: () => import(/* webpackChunkName: "LessonResourceSelectionPage" */ '../views/plan/LessonResourceSelectionPage'),
    handler(toRoute, fromRoute) {
      let preHandlerPromise;
      if (fromRoute.name === LessonsPageNames.SELECTION_CONTENT_PREVIEW) {
        preHandlerPromise = store.dispatch('lessonSummary/saveLessonResources', {
          lessonId: toRoute.params.lessonId,
          resources: store.state.lessonSummary.workingResources,
        });
      } else {
        preHandlerPromise = Promise.resolve();
      }
      preHandlerPromise.then(() => {
        showLessonResourceBookmarks(store, toRoute.params, toRoute.query);
      });
    },
  },
  {
    name: LessonsPageNames.LESSON_SELECTION_BOOKMARKS_MAIN,
    path: path(CLASS, LESSON, SELECTION),
    component: () => import(/* webpackChunkName: "LessonResourceSelectionPage" */ '../views/plan/LessonResourceSelectionPage'),
    handler(toRoute) {
      showLessonResourceBookmarksMain(store, toRoute.params, toRoute.query);
    },
  },
  {
    name: LessonsPageNames.SELECTION_CONTENT_PREVIEW,
    path: path(CLASS, LESSON, SELECTION, PREVIEW),
    component: () => import(/* webpackChunkName: "PlanLessonSelectionContentPreview" */ '../views/plan/PlanLessonSelectionContentPreview'),
    handler(toRoute) {
      showLessonSelectionContentPreview(store, toRoute.params, toRoute.query);
    },
  },
  {
    name: LessonsPageNames.RESOURCE_CONTENT_PREVIEW,
    path: path(CLASS, LESSON, '/resource', PREVIEW),
    component: () => import(/* webpackChunkName: "PlanLessonSelectionContentPreview" */ '../views/plan/PlanLessonSelectionContentPreview'),
    props(data) {
      let backRoute;
      // If linked from the Reports section, go back there
      if (data.query.last === 'LessonReportEditDetailsPage') {
        backRoute = {
          name: 'LessonReportEditDetailsPage',
        };
      } else {
        backRoute = {
          name: LessonsPageNames.SUMMARY,
        };
      }
      return {
        showSelectOptions: false,
        backRoute,
      };
    },
    handler(toRoute) {
      showLessonResourceContentPreview(store, toRoute.params);
    },
  },
];
