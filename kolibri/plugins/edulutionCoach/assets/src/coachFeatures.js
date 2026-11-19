import plugin_data from 'plugin_data';

/**
 * Quizzes and groups, as the facility's admin set them on its Settings
 * page (coach_features.py). On unless turned off.
 *
 * @param {string} facilityId the class's facility, else the coach's own
 * @returns {{ quizzes: boolean, groups: boolean }}
 */
export default function coachFeatures(facilityId) {
  const features = (plugin_data.coach_features || {})[facilityId] || {};
  return {
    quizzes: features.quizzes !== false,
    groups: features.groups !== false,
  };
}

/**
 * The feature a coach route belongs to ('quizzes' or 'groups'), or null.
 * Every quiz page has /quizzes in its path and every group page /groups.
 */
export function featureForRoute(route) {
  const paths = route.matched.map(record => record.path);
  if (paths.some(path => path.includes('/quizzes'))) {
    return 'quizzes';
  }
  if (paths.some(path => path.includes('/groups'))) {
    return 'groups';
  }
  return null;
}
