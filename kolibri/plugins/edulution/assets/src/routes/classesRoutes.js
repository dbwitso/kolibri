import { get } from '@vueuse/core';
import store from 'kolibri.coreVue.vuex.store';
import router from 'kolibri.coreVue.router';
import { ClassesPageNames, PageNames } from '../constants';
import { showLessonPlaylist } from '../modules/lessonPlaylist/handlers';
import { showClassAssignmentsPage } from '../modules/classAssignments/handlers';
import { showAllClassesPage } from '../modules/classes/handlers';
import { showExam, showAssessment } from '../modules/examViewer/handlers';
import { showExamReport } from '../modules/examReportViewer/handlers';
import { inClasses } from '../composables/useCoreLearn';

function noClassesGuard() {
  const { canAccessUnassignedContent } = store.getters;
  if (!get(inClasses) && canAccessUnassignedContent) {
    // If there are no memberships and it is allowed, redirect to library page
    return router.replace({ name: PageNames.LIBRARY });
  }
  // Otherwise return nothing
  return;
}

export default [
  {
    name: ClassesPageNames.ALL_CLASSES,
    path: '/classes',
    handler: () => {
      return noClassesGuard() || showAllClassesPage(store);
    },
    component: () => import(/* webpackChunkName: "AllClassesPage" */ '../views/classes/AllClassesPage'),
  },
  {
    name: ClassesPageNames.CLASS_ASSIGNMENTS,
    path: '/classes/:classId',
    handler: toRoute => {
      const { classId } = toRoute.params;
      return noClassesGuard() || showClassAssignmentsPage(store, classId);
    },
    component: () => import(/* webpackChunkName: "ClassAssignmentsPage" */ '../views/classes/ClassAssignmentsPage.vue'),
  },
  {
    name: ClassesPageNames.LESSON_PLAYLIST,
    path: '/classes/:classId/lesson/:lessonId',
    handler: toRoute => {
      const { classId, lessonId } = toRoute.params;
      return noClassesGuard() || showLessonPlaylist(store, { classId, lessonId });
    },
    component: () => import(/* webpackChunkName: "LessonPlaylistPage" */ '../views/classes/LessonPlaylistPage'),
  },
  {
    name: ClassesPageNames.EXAM_VIEWER,
    path: '/classes/:classId/exam/:examId/:questionNumber',
    handler: (toRoute, fromRoute) => {
      if (noClassesGuard()) {
        return noClassesGuard();
      }
      const alreadyOnQuiz =
        fromRoute.name === ClassesPageNames.EXAM_VIEWER &&
        toRoute.params.examId === fromRoute.params.examId &&
        toRoute.params.classId === fromRoute.params.classId;
      showExam(store, toRoute.params, alreadyOnQuiz);
    },
    component: () => import(/* webpackChunkName: "ExamPage" */ '../views/ExamPage'),
  },
  {
    name: ClassesPageNames.EXAM_REPORT_VIEWER,
    path: '/classes/:classId/examReport/:examId/:tryIndex/:questionNumber/:questionInteraction',
    handler: toRoute => {
      if (noClassesGuard()) {
        return noClassesGuard();
      }
      showExamReport(store, toRoute.params);
    },
    component: () => import(/* webpackChunkName: "ExamReportViewer" */ '../views/LearnExamReportViewer'),
  },
  {
    name: ClassesPageNames.ASSESSMENT_VIEWER,
    path: '/classes/:classId/assessment/:examId/:questionNumber/:assessmentGroupId',
    handler: (toRoute, fromRoute) => {
      if (noClassesGuard()) {
        return noClassesGuard();
      }
      const alreadyOnAssessment =
        fromRoute.name === ClassesPageNames.ASSESSMENT_VIEWER &&
        toRoute.params.examId === fromRoute.params.examId &&
        toRoute.params.classId === fromRoute.params.classId &&
        toRoute.params.assessmentGroupId === fromRoute.params.assessmentGroupId;
      showAssessment(store, toRoute.params, alreadyOnAssessment);
    },
    component: () => import(/* webpackChunkName: "AssessmentPage" */ '../views/AssessmentPage/index.vue'),
  },
];
