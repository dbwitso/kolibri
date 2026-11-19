import { ContentNodeResource } from 'kolibri.resources';

/*
 * What comes after a resource, for the "Keep going" step after a learner
 * finishes it.
 *
 * The content tree endpoint returns at most 12 children of a folder
 * (NUM_CHILDREN in kolibri/core/content/api.py), so looking a resource up
 * in that list fails from the 13th item on, and taking "the item after it"
 * then gave the folder's first item: a resource the learner had already
 * done. The content list endpoint returns every child, so these helpers
 * use it. For a restricted learner it returns only content they may see
 * (their lessons' resources and the folders above them), so the next item
 * is never one they cannot open.
 */

/**
 * Every child of a folder, in channel order.
 * @param {string} parentId
 * @param {{ includeCoachContent: boolean, baseurl: string }} options
 * @returns {Promise<Object[]>}
 */
export function fetchChildren(parentId, { includeCoachContent = false, baseurl } = {}) {
  const getParams = { parent: parentId, include_coach_content: includeCoachContent };
  if (baseurl) {
    getParams.baseurl = baseurl;
  }
  return ContentNodeResource.fetchCollection({ getParams }).then(nodes =>
    [...(nodes || [])].sort((a, b) => a.lft - b.lft)
  );
}

// The first resource in a folder, looking inside sub-folders in order.
function firstResourceIn(node, options) {
  if (node.is_leaf) {
    return Promise.resolve(node);
  }
  return fetchChildren(node.id, options).then(children => {
    const search = index =>
      index >= children.length
        ? Promise.resolve(null)
        : firstResourceIn(children[index], options).then(found => found || search(index + 1));
    return search(0);
  });
}

/**
 * The resource after `contentNode`: the next one in its folder, or, after a
 * folder's last resource, the first resource of the next folder (going up a
 * level when a folder is the last of its own folder).
 *
 * @param {Object} contentNode a resource with `parent` and `ancestors`
 * @param {{ includeCoachContent: boolean, baseurl: string }} options
 * @returns {Promise<{ node: Object, topic: Object } | null>} `topic` is the
 *   new folder when the next resource is in one, else null
 */
export function findNextContent(contentNode, options = {}) {
  return fetchChildren(contentNode.parent, options).then(siblings => {
    const index = siblings.findIndex(node => node.id === contentNode.id);
    if (index !== -1 && index + 1 < siblings.length) {
      const next = siblings[index + 1];
      if (next.is_leaf) {
        return { node: next, topic: null };
      }
      return firstResourceIn(next, options).then(node => (node ? { node, topic: next } : null));
    }
    // Last in its folder: move on to the next folder. ancestors runs from
    // the channel's root down to the resource's own folder.
    const ancestors = contentNode.ancestors || [];
    const climb = level => {
      if (level < 1) {
        return Promise.resolve(null);
      }
      const folderId = ancestors[level].id;
      return fetchChildren(ancestors[level - 1].id, options).then(folders => {
        const at = folders.findIndex(node => node.id === folderId);
        const later = at === -1 ? [] : folders.slice(at + 1);
        const tryLater = i =>
          i >= later.length
            ? climb(level - 1)
            : firstResourceIn(later[i], options).then(node =>
                node ? { node, topic: later[i].is_leaf ? null : later[i] } : tryLater(i + 1)
              );
        return tryLater(0);
      });
    };
    return climb(ancestors.length - 1);
  });
}
