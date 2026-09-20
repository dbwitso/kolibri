import store from 'kolibri.coreVue.vuex.store';
import { PageNames } from '../constants';
import {
  generateExerciseDetailHandler,
  exerciseRootRedirectHandler,
} from '../modules/exerciseDetail/handlers';
import { generateExamReportDetailHandler, generateAssessmentReportDetailHandler } from '../modules/examReportDetail/handlers';
import {
  generateQuestionDetailHandler,
  questionRootRedirectHandler,
} from '../modules/questionDetail/handlers';
import { generateQuestionListHandler } from '../modules/questionList/handlers';
import { generateResourceHandler } from '../modules/resourceDetail/handlers';
import { classIdParamRequiredGuard } from './utils';

const ACTIVITY = '/activity';
const CLASS = '/:classId?/reports';
const GROUPS = '/groups';
const GROUP = '/groups/:groupId';
const LEARNERS = '/learners';
const ATTENDANCE = '/attendance';
const LEARNER = '/learners/:learnerId';
const LESSONS = '/lessons';
const LESSON = '/lessons/:lessonId';
const QUIZZES = '/quizzes';
const QUIZ = '/quizzes/:quizId';
const ASSESSMENTS = '/assessments';
const ASSESSMENT = '/assessments/:quizId';
const QUESTIONS = '/questions';
const QUESTION = '/questions/:questionId';
const TRY = '/try/:tryIndex';
const INTERACTION = '/interactions/:interactionIndex';
const EXERCISE = '/exercises/:exerciseId';
const RESOURCES = '/resources';
const RESOURCE = '/resources/:resourceId';

function path(...args) {
  return args.join('');
}

function defaultHandler() {
  store.dispatch('notLoading');
}

// Each report page component below is lazy-loaded via dynamic import() instead
// of the old '../views/reports/allReportsPages' barrel, which statically
// imported all ~47 report pages into this bundle regardless of which one a
// coach actually visits. Every route below has an explicit `name:` (rather
// than relying on Vue Router's fallback of reading `component.name`, which
// only works for a synchronously-available component object - see
// kolibri/core/assets/src/router.js's initRoutes) - each name matches the
// name: option declared inside that page's own .vue file.

export default [
  {
    name: PageNames.REPORTS_PAGE,
    path: path(CLASS),
    redirect: { name: 'ReportsClassOverviewPage' },
  },
  {
    name: 'ReportsClassOverviewPage',
    path: path(CLASS, '/overview'),
    component: () => import(/* webpackChunkName: "ReportsClassOverviewPage" */ '../views/reports/ReportsClassOverviewPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupActivityPage',
    path: path(CLASS, GROUP, ACTIVITY),
    component: () => import(/* webpackChunkName: "ReportsGroupActivityPage" */ '../views/reports/ReportsGroupActivityPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['activityLabel', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupLearnerListPage',
    path: path(CLASS, GROUP, LEARNERS),
    component: () => import(/* webpackChunkName: "ReportsGroupLearnerListPage" */ '../views/reports/ReportsGroupLearnerListPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['membersLabel', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupListPage',
    path: path(CLASS, GROUPS),
    component: () => import(/* webpackChunkName: "ReportsGroupListPage" */ '../views/reports/ReportsGroupListPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['groupsLabel', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupReportLessonLearnerPage',
    path: path(CLASS, GROUP, LESSON, LEARNER),
    component: () => import(/* webpackChunkName: "ReportsGroupReportLessonLearnerPage" */ '../views/reports/ReportsGroupReportLessonLearnerPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['learnersLabel', 'LESSON_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupReportLessonExerciseLearnerListPage',
    path: path(CLASS, GROUP, LESSON, EXERCISE, LEARNERS),
    component: () => import(/* webpackChunkName: "ReportsGroupReportLessonExerciseLearnerListPage" */ '../views/reports/ReportsGroupReportLessonExerciseLearnerListPage'),
    handler: generateResourceHandler(['exerciseId']),
    meta: {
      titleParts: ['learnersLabel', 'EXERCISE_NAME', 'LESSON_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, GROUP, LESSON, EXERCISE, LEARNER),
    name: PageNames.REPORTS_GROUP_REPORT_LESSON_EXERCISE_LEARNER_PAGE_ROOT,
    beforeEnter: (to, from, next) => {
      const { params } = to;
      return exerciseRootRedirectHandler(
        params,
        'ReportsGroupReportLessonExerciseLearnerPage',
        next
      );
    },
    meta: {
      titleParts: ['LEARNER_NAME', 'EXERCISE_NAME', 'LESSON_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupReportLessonExerciseLearnerPage',
    path: path(CLASS, GROUP, LESSON, EXERCISE, LEARNER, TRY, QUESTION, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsGroupReportLessonExerciseLearnerPage" */ '../views/reports/ReportsGroupReportLessonExerciseLearnerPage'),
    handler: generateExerciseDetailHandler(['groupId', 'learnerId', 'lessonId', 'exerciseId']),
    meta: {
      // Leaves out attempt and interaction
      titleParts: ['LEARNER_NAME', 'EXERCISE_NAME', 'LESSON_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },

  {
    name: 'ReportsGroupReportLessonExerciseQuestionListPage',
    path: path(CLASS, GROUP, LESSON, EXERCISE, QUESTIONS),
    component: () => import(/* webpackChunkName: "ReportsGroupReportLessonExerciseQuestionListPage" */ '../views/reports/ReportsGroupReportLessonExerciseQuestionListPage'),
    handler: generateQuestionListHandler(['groupId', 'lessonId', 'exerciseId']),
    meta: {
      titleParts: ['questionsLabel', 'EXERCISE_NAME', 'LESSON_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, GROUP, LESSON, EXERCISE, QUESTION),
    name: PageNames.REPORTS_GROUP_REPORT_LESSON_EXERCISE_QUESTION_PAGE_ROOT,
    beforeEnter: (to, from, next) => {
      const { params } = to;
      return questionRootRedirectHandler(
        params,
        'ReportsGroupReportLessonExerciseQuestionPage',
        next
      );
    },
  },
  {
    name: 'ReportsGroupReportLessonExerciseQuestionPage',
    path: path(CLASS, GROUP, LESSON, EXERCISE, QUESTION, LEARNER, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsGroupReportLessonExerciseQuestionPage" */ '../views/reports/ReportsGroupReportLessonExerciseQuestionPage'),
    handler: generateQuestionDetailHandler(['groupId', 'lessonId', 'exerciseId', 'questionId']),
    meta: {
      // Leaves out info on question
      titleParts: ['questionLabel', 'EXERCISE_NAME', 'LESSON_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupReportLessonPage',
    path: path(CLASS, GROUP, LESSON, RESOURCES),
    component: () => import(/* webpackChunkName: "ReportsGroupReportLessonPage" */ '../views/reports/ReportsGroupReportLessonPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['LESSON_NAME', 'LEARNER_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupReportLessonLearnerListPage',
    path: path(CLASS, GROUP, LESSON, LEARNERS),
    component: () => import(/* webpackChunkName: "ReportsGroupReportLessonLearnerListPage" */ '../views/reports/ReportsGroupReportLessonLearnerListPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['LESSON_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupReportLessonResourceLearnerListPage',
    path: path(CLASS, GROUP, LESSON, RESOURCE, LEARNERS),
    component: () => import(/* webpackChunkName: "ReportsGroupReportLessonResourceLearnerListPage" */ '../views/reports/ReportsGroupReportLessonResourceLearnerListPage'),
    handler: generateResourceHandler(['resourceId']),
    meta: {
      titleParts: ['learnersLabel', 'RESOURCE_NAME', 'LESSON_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupReportPage',
    path: path(CLASS, GROUP, '/reports'),
    component: () => import(/* webpackChunkName: "ReportsGroupReportPage" */ '../views/reports/ReportsGroupReportPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['reportsLabel', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupReportQuizLearnerListPage',
    path: path(CLASS, GROUP, QUIZ, LEARNERS),
    component: () => import(/* webpackChunkName: "ReportsGroupReportQuizLearnerListPage" */ '../views/reports/ReportsGroupReportQuizLearnerListPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['learnersLabel', 'QUIZ_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, GROUP, QUIZ, LEARNER),
    name: PageNames.REPORTS_GROUP_REPORT_QUIZ_LEARNER_PAGE_ROOT,
    redirect: to => {
      const { params } = to;
      return {
        name: 'ReportsGroupReportQuizLearnerPage',
        params: {
          ...params,
          questionId: 0,
          interactionIndex: 0,
          tryIndex: 0,
        },
      };
    },
  },
  {
    name: 'ReportsGroupReportQuizLearnerPage',
    path: path(CLASS, GROUP, QUIZ, LEARNER, TRY, QUESTION, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsGroupReportQuizLearnerPage" */ '../views/reports/ReportsGroupReportQuizLearnerPage'),
    handler: generateExamReportDetailHandler(['groupId', 'learnerId', 'quizId']),
    meta: {
      titleParts: ['LEARNER_NAME', 'QUIZ_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsGroupReportQuizQuestionListPage',
    path: path(CLASS, GROUP, QUIZ, QUESTIONS),
    component: () => import(/* webpackChunkName: "ReportsGroupReportQuizQuestionListPage" */ '../views/reports/ReportsGroupReportQuizQuestionListPage'),
    handler: generateQuestionListHandler(['groupId', 'quizId']),
    meta: {
      titleParts: ['questionsLabel', 'QUIZ_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, GROUP, QUIZ, QUESTION),
    name: PageNames.REPORTS_GROUP_REPORT_QUIZ_QUESTION_PAGE_ROOT,
    beforeEnter: (to, from, next) => {
      const { params } = to;
      return questionRootRedirectHandler(
        params,
        'ReportsGroupReportQuizQuestionPage',
        next
      );
    },
  },
  {
    name: 'ReportsGroupReportQuizQuestionPage',
    path: path(CLASS, GROUP, QUIZ, QUESTION, LEARNER, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsGroupReportQuizQuestionPage" */ '../views/reports/ReportsGroupReportQuizQuestionPage'),
    handler: generateQuestionDetailHandler(['groupId', 'quizId', 'questionId']),
    meta: {
      titleParts: ['questionsLabel', 'QUIZ_NAME', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, LEARNER, ACTIVITY, EXERCISE),
    name: PageNames.REPORTS_LEARNER_ACTIVITY_EXERCISE_PAGE_ROOT,
    beforeEnter: (to, from, next) => {
      const { params } = to;
      return exerciseRootRedirectHandler(
        params,
        'ReportsLearnerActivityExercisePage',
        next
      );
    },
    meta: {
      titleParts: ['EXERCISE_NAME', 'LEARNER_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLearnerActivityExercisePage',
    path: path(CLASS, LEARNER, ACTIVITY, EXERCISE, QUESTION, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsLearnerActivityExercisePage" */ '../views/reports/ReportsLearnerActivityExercisePage'),
    handler: generateExerciseDetailHandler(['learnerId', 'exerciseId']),
    meta: {
      titleParts: ['EXERCISE_NAME', 'LEARNER_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLearnerActivityPage',
    path: path(CLASS, LEARNER, ACTIVITY),
    component: () => import(/* webpackChunkName: "ReportsLearnerActivityPage" */ '../views/reports/ReportsLearnerActivityPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['activityLabel', 'LEARNER_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLearnerListPage',
    path: path(CLASS, LEARNERS),
    component: () => import(/* webpackChunkName: "ReportsLearnerListPage" */ '../views/reports/ReportsLearnerListPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['learnersLabel', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsAttendanceListPage',
    path: path(CLASS, ATTENDANCE),
    component: () => import(/* webpackChunkName: "ReportsAttendanceListPage" */ '../views/reports/ReportsAttendanceListPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['attendanceLabel', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, LEARNER, LESSON, EXERCISE),
    name: PageNames.REPORTS_LEARNER_REPORT_LESSON_EXERCISE_PAGE_ROOT,
    beforeEnter: (to, from, next) => {
      const { params } = to;
      return exerciseRootRedirectHandler(
        params,
        'ReportsLearnerReportLessonExercisePage',
        next
      );
    },
    meta: {
      titleParts: ['EXERCISE_NAME', 'LESSON_NAME', 'LEARNER_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLearnerReportLessonExercisePage',
    path: path(CLASS, LEARNER, LESSON, EXERCISE, TRY, QUESTION, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsLearnerReportLessonExercisePage" */ '../views/reports/ReportsLearnerReportLessonExercisePage'),
    handler: generateExerciseDetailHandler(['learnerId', 'lessonId', 'exerciseId']),
    meta: {
      titleParts: ['EXERCISE_NAME', 'LESSON_NAME', 'LEARNER_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLearnerReportLessonPage',
    path: path(CLASS, LEARNER, LESSON),
    component: () => import(/* webpackChunkName: "ReportsLearnerReportLessonPage" */ '../views/reports/ReportsLearnerReportLessonPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['LESSON_NAME', 'LEARNER_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLearnerReportPage',
    path: path(CLASS, LEARNER, '/reports'),
    component: () => import(/* webpackChunkName: "ReportsLearnerReportPage" */ '../views/reports/ReportsLearnerReportPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['reportsLabel', 'LEARNER_NAME', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, LEARNER, QUIZ),
    name: PageNames.REPORTS_LEARNER_REPORT_QUIZ_PAGE_ROOT,
    redirect: to => {
      const { params } = to;
      return {
        name: 'ReportsLearnerReportQuizPage',
        params: {
          ...params,
          questionId: 0,
          interactionIndex: 0,
        },
      };
    },
  },
  {
    name: 'ReportsLearnerReportQuizPage',
    path: path(CLASS, LEARNER, QUIZ, TRY, QUESTION, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsLearnerReportQuizPage" */ '../views/reports/ReportsLearnerReportQuizPage'),
    handler: generateExamReportDetailHandler(['learnerId', 'quizId']),
    meta: {
      titleParts: ['QUIZ_NAME', 'LEARNER_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'LessonReportEditDetailsPage',
    path: path(CLASS, LESSON, '/edit'),
    component: () => import(/* webpackChunkName: "LessonEditDetailsPage" */ '../views/plan/LessonEditDetailsPage'),
    props: {
      showResourcesTable: true,
    },
    handler: defaultHandler,
  },
  {
    name: 'ReportsLessonExerciseLearnerListPage',
    path: path(CLASS, LESSON, EXERCISE, LEARNERS),
    component: () => import(/* webpackChunkName: "ReportsLessonExerciseLearnerListPage" */ '../views/reports/ReportsLessonExerciseLearnerListPage'),
    handler: generateResourceHandler(['exerciseId']),
    meta: {
      titleParts: ['learnersLabel', 'EXERCISE_NAME', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, LESSON, EXERCISE, LEARNER),
    name: PageNames.REPORTS_LESSON_EXERCISE_LEARNER_PAGE_ROOT,
    beforeEnter: (to, from, next) => {
      const { params, query } = to;
      return exerciseRootRedirectHandler(
        params,
        'ReportsLessonExerciseLearnerPage',
        next,
        query
      );
    },
    meta: {
      titleParts: ['LEARNER_NAME', 'EXERCISE_NAME', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },

  {
    name: 'ReportsLessonExerciseLearnerPage',
    path: path(CLASS, LESSON, EXERCISE, LEARNER, TRY, QUESTION, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsLessonExerciseLearnerPage" */ '../views/reports/ReportsLessonExerciseLearnerPage'),
    handler: generateExerciseDetailHandler(['learnerId', 'lessonId', 'exerciseId']),
    meta: {
      titleParts: ['LEARNER_NAME', 'EXERCISE_NAME', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLessonExerciseQuestionListPage',
    path: path(CLASS, LESSON, EXERCISE, QUESTIONS),
    component: () => import(/* webpackChunkName: "ReportsLessonExerciseQuestionListPage" */ '../views/reports/ReportsLessonExerciseQuestionListPage'),
    handler: generateQuestionListHandler(['lessonId', 'exerciseId']),
    meta: {
      titleParts: ['questionsLabel', 'EXERCISE_NAME', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },

  {
    path: path(CLASS, LESSON, EXERCISE, QUESTION),
    name: PageNames.REPORTS_LESSON_EXERCISE_QUESTION_PAGE_ROOT,
    beforeEnter: (to, from, next) => {
      const { params } = to;
      return questionRootRedirectHandler(
        params,
        'ReportsLessonExerciseQuestionPage',
        next
      );
    },
  },
  {
    name: 'ReportsLessonExerciseQuestionPage',
    path: path(CLASS, LESSON, EXERCISE, QUESTION, LEARNER, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsLessonExerciseQuestionPage" */ '../views/reports/ReportsLessonExerciseQuestionPage'),
    handler: generateQuestionDetailHandler(['lessonId', 'exerciseId', 'questionId']),
    meta: {
      // No info on question
      titleParts: ['EXERCISE_NAME', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, LESSON, LEARNER, EXERCISE),
    name: PageNames.REPORTS_LESSON_LEARNER_EXERCISE_PAGE_ROOT,
    beforeEnter: (to, from, next) => {
      const { params } = to;
      return exerciseRootRedirectHandler(params, 'ReportsLessonLearnerExercisePage', next);
    },
    meta: {
      titleParts: ['EXERCISE_NAME', 'LEARNER_NAME', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLessonLearnerExercisePage',
    path: path(CLASS, LESSON, LEARNER, EXERCISE, TRY, QUESTION, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsLessonLearnerExercisePage" */ '../views/reports/ReportsLessonLearnerExercisePage'),
    handler: generateExerciseDetailHandler(['learnerId', 'lessonId', 'exerciseId']),
    meta: {
      // Leaves out attempt and interaction numbers
      titleParts: ['LEARNER_NAME', 'EXERCISE_NAME', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLessonLearnerListPage',
    path: path(CLASS, LESSON, LEARNERS),
    component: () => import(/* webpackChunkName: "ReportsLessonLearnerListPage" */ '../views/reports/ReportsLessonLearnerListPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['learnersLabel', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLessonLearnerPage',
    path: path(CLASS, LESSON, LEARNER),
    component: () => import(/* webpackChunkName: "ReportsLessonLearnerPage" */ '../views/reports/ReportsLessonLearnerPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['LEARNER_NAME', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLessonListPage',
    path: path(CLASS, LESSONS),
    component: () => import(/* webpackChunkName: "ReportsLessonListPage" */ '../views/reports/ReportsLessonListPage'),
    handler(toRoute, fromRoute, next) {
      if (classIdParamRequiredGuard(toRoute, PageNames.REPORTS_PAGE, next)) {
        return;
      }
      defaultHandler();
    },
    meta: {
      titleParts: ['lessonsLabel', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLessonManagerPage',
    path: path(CLASS, LESSON, '/manager'),
    component: () => import(/* webpackChunkName: "ReportsLessonManagerPage" */ '../views/reports/ReportsLessonManagerPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['manageResourcesAction', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLessonReportPage',
    path: path(CLASS, LESSON, RESOURCES),
    component: () => import(/* webpackChunkName: "ReportsLessonReportPage" */ '../views/reports/ReportsLessonReportPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['reportLabel', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsLessonResourceLearnerListPage',
    path: path(CLASS, LESSON, RESOURCE, LEARNERS),
    component: () => import(/* webpackChunkName: "ReportsLessonResourceLearnerListPage" */ '../views/reports/ReportsLessonResourceLearnerListPage'),
    handler: generateResourceHandler(['resourceId']),
    meta: {
      titleParts: ['RESOURCE_NAME', 'LESSON_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'QuizReportEditDetailsPage',
    path: path(CLASS, QUIZ, '/edit'),
    component: () => import(/* webpackChunkName: "QuizEditDetailsPage" */ '../views/plan/QuizEditDetailsPage'),
    handler: defaultHandler,
  },
  {
    name: 'ReportsQuizLearnerListPage',
    path: path(CLASS, QUIZ, LEARNERS),
    component: () => import(/* webpackChunkName: "ReportsQuizLearnerListPage" */ '../views/reports/ReportsQuizLearnerListPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['learnersLabel', 'QUIZ_NAME', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, QUIZ, LEARNER),
    name: PageNames.REPORTS_QUIZ_LEARNER_PAGE_ROOT,
    redirect: to => {
      const { params } = to;
      return {
        name: 'ReportsQuizLearnerPage',
        params: {
          ...params,
          questionId: 0,
          tryIndex: 0,
          interactionIndex: 0,
        },
      };
    },
  },
  {
    name: 'ReportsQuizLearnerPage',
    path: path(CLASS, QUIZ, LEARNER, TRY, QUESTION, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsQuizLearnerPage" */ '../views/reports/ReportsQuizLearnerPage'),
    handler: generateExamReportDetailHandler(['learnerId', 'quizId']),
    meta: {
      // Leaves out question and interaction numbers
      titleParts: ['LEARNER_NAME', 'QUIZ_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsQuizListPage',
    path: path(CLASS, QUIZZES),
    component: () => import(/* webpackChunkName: "ReportsQuizListPage" */ '../views/reports/ReportsQuizListPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['quizzesLabel', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsQuizPreviewPage',
    path: path(CLASS, QUIZ, '/preview'),
    component: () => import(/* webpackChunkName: "ReportsQuizPreviewPage" */ '../views/reports/ReportsQuizPreviewPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['previewLabel', 'QUIZ_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsQuizQuestionListPage',
    path: path(CLASS, QUIZ, QUESTIONS),
    component: () => import(/* webpackChunkName: "ReportsQuizQuestionListPage" */ '../views/reports/ReportsQuizQuestionListPage'),
    handler: generateQuestionListHandler(['quizId']),
    meta: {
      titleParts: ['questionsLabel', 'QUIZ_NAME', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, QUIZ, QUESTION),
    name: PageNames.REPORTS_QUIZ_QUESTION_PAGE_ROOT,
    beforeEnter: (to, from, next) => {
      const { params } = to;
      return questionRootRedirectHandler(params, 'ReportsQuizQuestionPage', next);
    },
  },
  {
    name: 'ReportsQuizQuestionPage',
    path: path(CLASS, QUIZ, QUESTION, LEARNER, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsQuizQuestionPage" */ '../views/reports/ReportsQuizQuestionPage'),
    handler: generateQuestionDetailHandler(['quizId', 'questionId']),
    meta: {
      // TODO Leaves out details about the question
      titleParts: ['QUIZ_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsAssessmentListPage',
    path: path(CLASS, ASSESSMENTS),
    component: () => import(/* webpackChunkName: "ReportsAssessmentListPage" */ '../views/reports/ReportsAssessmentListPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['assessmentsLabel', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, GROUP, ASSESSMENT, LEARNER),
    name: PageNames.REPORTS_GROUP_REPORT_ASSESSMENT_LEARNER_PAGE_ROOT,
    redirect: to => {
      const { params } = to;
      return {
        name: 'ReportsGroupReportAssessmentLearnerPage',
        params: {
          ...params,
          questionId: 0,
          interactionIndex: 0,
          tryIndex: 0,
        },
      };
    },
  },
  {
    name: 'ReportsAssessmentLearnerListPage',
    path: path(CLASS, ASSESSMENT, LEARNERS),
    component: () => import(/* webpackChunkName: "ReportsAssessmentLearnerListPage" */ '../views/reports/ReportsAssessmentLearnerListPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['learnersLabel', 'QUIZ_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsAssessmentQuestionListPage',
    path: path(CLASS, ASSESSMENT, QUESTIONS),
    component: () => import(/* webpackChunkName: "ReportsAssessmentQuestionListPage" */ '../views/reports/ReportsAssessmentQuestionListPage.vue'),
    handler: generateQuestionListHandler(['quizId']),
    meta: {
      titleParts: ['questionsLabel', 'QUIZ_NAME', 'CLASS_NAME'],
    },
  },
  {
    path: path(CLASS, ASSESSMENT, LEARNER),
    name: PageNames.REPORTS_ASSESSMENT_LEARNER_PAGE_ROOT,
    redirect: to => {
      const { params } = to;
      return {
        name: 'ReportsAssessmentLearnerPage',
        params: {
          ...params,
          questionId: 0,
          tryIndex: 0,
          interactionIndex: 0,
        },
      };
    },
  },
  {
    name: 'ReportsAssessmentLearnerPage',
    path: path(CLASS, ASSESSMENT, LEARNER, TRY, QUESTION, INTERACTION),
    component: () => import(/* webpackChunkName: "ReportsAssessmentLearnerPage" */ '../views/reports/ReportsAssessmentLearnerPage'),
    handler: generateAssessmentReportDetailHandler(['learnerId', 'quizId']),
    meta: {
      // Leaves out question and interaction numbers
      titleParts: ['LEARNER_NAME', 'QUIZ_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'ReportsAssessmentPreviewPage',
    path: path(CLASS, ASSESSMENT, '/preview'),
    component: () => import(/* webpackChunkName: "ReportsAssessmentPreviewPage" */ '../views/reports/ReportsAssessmentPreviewPage'),
    handler: defaultHandler,
    meta: {
      titleParts: ['previewLabel', 'QUIZ_NAME', 'CLASS_NAME'],
    },
  },
];
