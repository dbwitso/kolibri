/**
 * Wraps the router's getRoute(name, params, query) so a link to a page whose
 * path has :classId gets the current class when the caller left it out.
 *
 * Many coach pages build links as getRoute('SELECTION_ROOT') or
 * getRoute('ReportsLessonLearnerPage', { learnerId }), expecting the class to
 * carry over. But Plan and Reports paths start with an optional `:classId?`,
 * and Vue Router never fills in optional params from the current page, so
 * those links had no class: they opened the class list ("select a class")
 * instead of the page, e.g. a lesson's Options > Manage resources.
 *
 * @param {Function} getRoute the router's getRoute
 * @param {Function} getDefinition name -> route definition (with `path`)
 * @param {Function} currentClassId () -> the class being viewed, or null
 */
export default function fillClassId(getRoute, getDefinition, currentClassId) {
  return function getRouteWithClass(name, params = {}, query = {}) {
    const route = getRoute(name, params, query);
    const definition = getDefinition(name);
    if (
      definition &&
      typeof definition.path === 'string' &&
      definition.path.includes(':classId') &&
      !(route.params && route.params.classId)
    ) {
      const classId = currentClassId();
      if (classId) {
        route.params = { ...(route.params || {}), classId };
      }
    }
    return route;
  };
}
