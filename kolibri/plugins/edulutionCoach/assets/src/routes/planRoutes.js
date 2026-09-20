import store from 'kolibri.coreVue.vuex.store';
import { PageNames } from '../constants';
import { useGroups } from '../composables/useGroups';
import planLessonsRoutes from './planLessonsRoutes';
import planExamRoutes from './planExamRoutes';
import planAssessmentRoutes from './planAssessmentRoutes';

const { showGroupsPage } = useGroups();

export default [
  ...planLessonsRoutes,
  ...planExamRoutes,
  ...planAssessmentRoutes,
  {
    name: PageNames.PLAN_PAGE,
    path: '/:classId?/plan',
    redirect: '/:classId?/plan/lessons',
  },
  {
    name: 'GroupsPage',
    path: '/:classId/plan/groups',
    component: () => import(/* webpackChunkName: "GroupsPage" */ '../views/plan/GroupsPage'),
    handler(to) {
      showGroupsPage(store, to.params.classId);
    },
    meta: {
      titleParts: ['groupsLabel', 'CLASS_NAME'],
    },
  },
  {
    name: 'GroupMembersPage',
    path: '/:classId/plan/groups/:groupId',
    component: () => import(/* webpackChunkName: "GroupMembersPage" */ '../views/plan/GroupMembersPage'),
    handler(to) {
      showGroupsPage(store, to.params.classId);
    },
    meta: {
      titleParts: ['membersLabel', 'GROUP_NAME', 'CLASS_NAME'],
    },
  },
  {
    name: 'GroupEnrollPage',
    path: '/:classId/plan/groups/:groupId/enroll',
    component: () => import(/* webpackChunkName: "GroupEnrollPage" */ '../views/plan/GroupEnrollPage'),
    handler(to) {
      showGroupsPage(store, to.params.classId);
    },
  },
];
