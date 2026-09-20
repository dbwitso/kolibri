// IDEA kill these in favor of using vuex param autocomplete
// Lesson routes use an optional `:classId?` segment, and Vue Router does not
// reliably fill in optional segments from a `params` object on named-route
// navigation, so these build literal paths instead of using {name, params}.

// Creates a Link to the Lesson Summary Page
export function lessonSummaryLink({ classId, lessonId }) {
  return { path: `/${classId}/plan/lessons/${lessonId}` };
}

// Creates a Link to the Channel Browsing Page for a Lesson
export function selectionRootLink({ classId, lessonId }) {
  return { path: `/${classId}/plan/lessons/${lessonId}/selection` };
}
