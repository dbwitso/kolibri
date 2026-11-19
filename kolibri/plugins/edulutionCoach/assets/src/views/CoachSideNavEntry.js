import navComponents from 'kolibri.utils.navComponents';
import urls from 'kolibri.urls';
import coreStrings from 'kolibri.utils.coreStrings';
import { UserKinds } from 'kolibri.coreVue.vuex.constants';
import { createTranslator } from 'kolibri.utils.i18n';
import baseRoutes from '../routes/baseRoutes';
import { coachStrings } from './common/commonCoachStrings';

const sideNavStrings = createTranslator('CoachSideNavEntry', {
  lessonGuideLabel: {
    message: 'Lesson guide',
    context:
      'Coach menu link to the prompts that help a coach plan a lesson (objective, steps to create a lesson).',
  },
});

const sideNavConfig = {
  name: 'CoachSideNavEntry',
  get url() {
    return urls['kolibri:kolibri.plugins.edulutionCoach:edulutionCoach']();
  },
  get routes() {
    // No Plan entry here (nor in the tablet bottom bar, which uses this
    // list): coaches plan from the Plan tab inside a class, where the
    // class is always known.
    return [
      {
        label: coreStrings.$tr('classHome'),
        route: baseRoutes.classHome.path,
        name: baseRoutes.classHome.name,
        icon: 'dashboard',
      },
      {
        label: coachStrings.$tr('reportsLabel'),
        route: baseRoutes.reports.path,
        name: baseRoutes.reports.name,
        icon: 'reports',
      },
      {
        label: coachStrings.$tr('attendanceLabel'),
        route: baseRoutes.attendance.path,
        name: baseRoutes.attendance.name,
        icon: 'people',
      },
      {
        label: sideNavStrings.$tr('lessonGuideLabel'),
        route: baseRoutes.lessonGuide.path,
        name: baseRoutes.lessonGuide.name,
        icon: 'lesson',
      },
    ];
  },
  get label() {
    return coreStrings.$tr('coachLabel');
  },
  icon: 'coach',
  role: UserKinds.COACH,
  priority: 10,
  fullFacilityOnly: true,
};

navComponents.register(sideNavConfig);

export default sideNavConfig;
