import store from 'kolibri.coreVue.vuex.store';
import { PageNames } from '../constants';
import {
  showExamCreationRootPage,
  showExamCreationTopicPage,
  showExamCreationBookmarksPage,
  showExamCreationAllBookmarks,
  showExamCreationSearchPage,
  showExamCreationQuestionSelectionPage,
  showExamCreationPreviewPage,
  showPracticeQuizCreationPreviewPage,
} from '../modules/assessmentCreation/handlers';
import { showExamsPage } from '../modules/examsRoot/handlers';

export default [
  {
    name: PageNames.ASSESSMENTS,
    path: '/:classId/plan/assessments',
    component: () => import(/* webpackChunkName: "CoachAssessmentsPage" */ '../views/plan/CoachAssessmentsPage/index.vue'),
    handler(toRoute) {
      showExamsPage(store, toRoute.params.classId);
    },
    meta: {
      titleParts: ['assessmentLabel', 'CLASS_NAME'],
    },
  },
  {
    name: PageNames.ASSESSMENT_CREATION_ROOT,
    path: '/:classId/plan/assessments/new/',
    component: () => import(/* webpackChunkName: "CreateAssessmentPage" */ '../views/plan/CreateAssessmentPage/index.vue'),
    handler: toRoute => {
      showExamCreationRootPage(store, toRoute.params);
    },
  },
  {
    name: PageNames.ASSESSMENT_CREATION_TOPIC,
    path: '/:classId/plan/assessments/new/topic/:topicId',
    component: () => import(/* webpackChunkName: "CreateAssessmentPage" */ '../views/plan/CreateAssessmentPage/index.vue'),
    handler: toRoute => {
      showExamCreationTopicPage(store, toRoute.params);
    },
  },
  {
    name: PageNames.ASSESSMENT_CREATION_BOOKMARKS,
    path: '/:classId/plan/assessments/new/bookmark/:topicId',
    component: () => import(/* webpackChunkName: "CreateAssessmentPage" */ '../views/plan/CreateAssessmentPage/index.vue'),
    handler: toRoute => {
      showExamCreationBookmarksPage(store, toRoute.params);
    },
  },
  {
    name: PageNames.ASSESSMENT_CREATION_BOOKMARKS_MAIN,
    path: '/:classId/plan/assessments/new/bookmarks',
    component: () => import(/* webpackChunkName: "CreateAssessmentPage" */ '../views/plan/CreateAssessmentPage/index.vue'),
    handler: toRoute => {
      showExamCreationAllBookmarks(store, toRoute.params);
    },
  },
  {
    name: PageNames.ASSESSMENT_CREATION_SEARCH,
    path: '/:classId/plan/assessments/new/search/:searchTerm',
    component: () => import(/* webpackChunkName: "CreateAssessmentPage" */ '../views/plan/CreateAssessmentPage/index.vue'),
    handler: toRoute => {
      showExamCreationSearchPage(store, toRoute.params, toRoute.query);
    },
  },
  {
    name: PageNames.ASSESSMENT_CREATION_QUESTION_SELECTION,
    path: '/:classId/plan/assessments/new/finalize',
    component: () => import(/* webpackChunkName: "CreateAssessmentPreviewPage" */ '../views/plan/CreateAssessmentPage/CreateAssessmentPreview.vue'),
    handler: (toRoute, fromRoute) => {
      showExamCreationQuestionSelectionPage(store, toRoute, fromRoute);
    },
  },
  {
    name: PageNames.ASSESSMENT_CREATION_PRACTICE_QUIZ_PREVIEW,
    path: '/:classId/plan/assessments/new/practice_assessment/preview/',
    component: () => import(/* webpackChunkName: "PlanPracticeQuizPreviewPageAssessment" */ '../views/plan/CreateAssessmentPage/PlanPracticeQuizPreviewPage.vue'),
    handler: toRoute => {
      showPracticeQuizCreationPreviewPage(store, toRoute.params);
    },
  },
  {
    name: PageNames.ASSESSMENT_CREATION_PREVIEW,
    path: '/:classId/plan/assessments/new/preview/',
    component: () => import(/* webpackChunkName: "PlanQuizPreviewPage" */ '../views/plan/PlanQuizPreviewPage.vue'),
    handler: (toRoute, fromRoute) => {
      showExamCreationPreviewPage(store, toRoute.params, fromRoute);
    },
  },
  {
    name: PageNames.ASSESSMENT_QUIZ_SUMMARY,
    path: '/:classId/plan/assessments/:assessmentId',
    component: () => import(/* webpackChunkName: "AssessmentSummaryPage" */ '../views/plan/AssessmentSummaryPage/index.vue'),
    meta: {
      titleParts: ['assessmentLabel', 'CLASS_NAME'],
    },
  },
];
