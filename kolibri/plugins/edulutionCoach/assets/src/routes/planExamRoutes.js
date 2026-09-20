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
  showPracticeQuizCreationRootPage,
  showPracticeQuizCreationTopicPage,
  showPracticeQuizCreationPreviewPage,
} from '../modules/examCreation/handlers';
import { showExamsPage } from '../modules/examsRoot/handlers';

export default [
  {
    name: PageNames.EXAMS,
    path: '/:classId/plan/quizzes',
    component: () => import(/* webpackChunkName: "CoachExamsPage" */ '../views/plan/CoachExamsPage'),
    handler(toRoute) {
      showExamsPage(store, toRoute.params.classId);
    },
    meta: {
      titleParts: ['quizzesLabel', 'CLASS_NAME'],
    },
  },
  {
    name: PageNames.EXAM_CREATION_ROOT,
    path: '/:classId/plan/quizzes/new/',
    component: () => import(/* webpackChunkName: "CreateExamPage" */ '../views/plan/CreateExamPage'),
    handler: toRoute => {
      showExamCreationRootPage(store, toRoute.params);
    },
  },
  {
    name: PageNames.EXAM_CREATION_PRACTICE_QUIZ,
    path: '/:classId/plan/quizzes/new/practice_quiz',
    component: () => import(/* webpackChunkName: "CreatePracticeQuizPage" */ '../views/plan/CreateExamPage/CreatePracticeQuizPage.vue'),
    handler: toRoute => {
      showPracticeQuizCreationRootPage(store, toRoute.params);
    },
  },
  {
    name: PageNames.EXAM_CREATION_SELECT_PRACTICE_QUIZ_TOPIC,
    path: '/:classId/plan/quizzes/new/practice_quiz/topic/:topicId',
    component: () => import(/* webpackChunkName: "CreatePracticeQuizPage" */ '../views/plan/CreateExamPage/CreatePracticeQuizPage.vue'),
    handler: toRoute => {
      showPracticeQuizCreationTopicPage(store, toRoute.params);
    },
  },
  {
    name: PageNames.EXAM_CREATION_TOPIC,
    path: '/:classId/plan/quizzes/new/topic/:topicId',
    component: () => import(/* webpackChunkName: "CreateExamPage" */ '../views/plan/CreateExamPage'),
    handler: toRoute => {
      showExamCreationTopicPage(store, toRoute.params);
    },
  },
  {
    name: PageNames.EXAM_CREATION_BOOKMARKS,
    path: '/:classId/plan/quizzes/new/bookmark/:topicId',
    component: () => import(/* webpackChunkName: "CreateExamPage" */ '../views/plan/CreateExamPage'),
    handler: toRoute => {
      showExamCreationBookmarksPage(store, toRoute.params);
    },
  },
  {
    name: PageNames.EXAM_CREATION_BOOKMARKS_MAIN,
    path: '/:classId/plan/quizzes/new/bookmarks',
    component: () => import(/* webpackChunkName: "CreateExamPage" */ '../views/plan/CreateExamPage'),
    handler: toRoute => {
      showExamCreationAllBookmarks(store, toRoute.params);
    },
  },
  {
    name: PageNames.EXAM_CREATION_SEARCH,
    path: '/:classId/plan/quizzes/new/search/:searchTerm',
    component: () => import(/* webpackChunkName: "CreateExamPage" */ '../views/plan/CreateExamPage'),
    handler: toRoute => {
      showExamCreationSearchPage(store, toRoute.params, toRoute.query);
    },
  },
  {
    name: PageNames.EXAM_CREATION_QUESTION_SELECTION,
    path: '/:classId/plan/quizzes/new/finalize',
    component: () => import(/* webpackChunkName: "CreateExamPreview" */ '../views/plan/CreateExamPage/CreateExamPreview.vue'),
    handler: (toRoute, fromRoute) => {
      showExamCreationQuestionSelectionPage(store, toRoute, fromRoute);
    },
  },
  {
    name: PageNames.EXAM_CREATION_PRACTICE_QUIZ_PREVIEW,
    path: '/:classId/plan/quizzes/new/practice_quiz/preview/',
    component: () => import(/* webpackChunkName: "PlanPracticeQuizPreviewPage" */ '../views/plan/CreateExamPage/PlanPracticeQuizPreviewPage'),
    handler: toRoute => {
      showPracticeQuizCreationPreviewPage(store, toRoute.params);
    },
  },
  {
    name: PageNames.EXAM_CREATION_PREVIEW,
    path: '/:classId/plan/quizzes/new/preview/',
    component: () => import(/* webpackChunkName: "PlanQuizPreviewPage" */ '../views/plan/PlanQuizPreviewPage'),
    handler: (toRoute, fromRoute) => {
      showExamCreationPreviewPage(store, toRoute.params, fromRoute);
    },
  },
  {
    name: 'QuizSummaryPage',
    path: '/:classId/plan/quizzes/:quizId',
    component: () => import(/* webpackChunkName: "QuizSummaryPage" */ '../views/plan/QuizSummaryPage'),
    meta: {
      titleParts: ['QUIZ_NAME', 'quizzesLabel', 'CLASS_NAME'],
    },
  },
  {
    name: 'QuizEditDetailsPage',
    path: '/:classId/plan/quizzes/:quizId/edit',
    component: () => import(/* webpackChunkName: "QuizEditDetailsPage" */ '../views/plan/QuizEditDetailsPage'),
  },
];
