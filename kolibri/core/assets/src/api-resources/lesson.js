import { Resource } from 'kolibri.lib.apiResource';

export default new Resource({
  name: 'lesson',
  fetchLessonsSizes(getParams = {}) {
    return this.fetchListCollection('size', getParams);
  },
  unlockLearnerResource(lessonId, { userId, contentnodeId } = {}) {
    return this.postDetailEndpoint('unlock-learner-resource', lessonId, {
      user_id: userId,
      contentnode_id: contentnodeId,
    });
  },
});
