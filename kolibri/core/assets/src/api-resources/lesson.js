import { Resource } from 'kolibri.lib.apiResource';

export default new Resource({
  name: 'lesson',
  fetchLessonsSizes(getParams = {}) {
    return this.fetchListCollection('size', getParams);
  },
  unlockLearnerResource(lessonId, { userId, contentnodeId } = {}) {
    // URL names reach the frontend with "-" turned into "_"
    // (url_path "unlock-learner-resource" on LessonViewset).
    return this.accessDetailEndpoint('patch', 'unlock_learner_resource', lessonId, {
      user_id: userId,
      contentnode_id: contentnodeId,
    });
  },
});
