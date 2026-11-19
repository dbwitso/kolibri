import { ContentNodeResource } from 'kolibri.resources';
import { fetchChildren, findNextContent } from '../nextContent';

jest.mock('kolibri.resources', () => ({ ContentNodeResource: { fetchCollection: jest.fn() } }));

/*
 * A channel:
 *   root
 *   ├── topicA: a1 … a14   (more than the content tree's 12)
 *   ├── topicEmpty          (nothing the learner may see)
 *   ├── topicB
 *   │   └── subB: b1, b2
 *   └── unit2
 *       └── topicC: c1
 */
let lft = 0;
const node = (id, parent, isLeaf = true) => ({
  id,
  parent,
  is_leaf: isLeaf,
  title: id,
  lft: lft++,
});
const tree = {};
function add(n) {
  tree[n.parent] = tree[n.parent] || [];
  tree[n.parent].push(n);
  return n;
}
add(node('topicA', 'root', false));
const aItems = Array.from({ length: 14 }, (_, i) => add(node(`a${i + 1}`, 'topicA')));
add(node('topicEmpty', 'root', false));
const topicB = add(node('topicB', 'root', false));
add(node('subB', 'topicB', false));
add(node('b1', 'subB'));
add(node('b2', 'subB'));
const unit2 = add(node('unit2', 'root', false));
add(node('topicC', 'unit2', false));
add(node('c1', 'topicC'));

const ancestors = (...ids) => ids.map(id => ({ id, title: id }));

describe('nextContent', () => {
  beforeEach(() => {
    ContentNodeResource.fetchCollection.mockImplementation(({ getParams }) =>
      // Returned out of order: the helper sorts by channel order.
      Promise.resolve([...(tree[getParams.parent] || [])].reverse())
    );
  });

  it('lists every child of a folder in order', () => {
    return fetchChildren('topicA').then(children => {
      expect(children.map(c => c.id)).toEqual(aItems.map(a => a.id));
    });
  });

  it('goes to the next item even after the twelfth', () => {
    const a13 = { ...aItems[12], ancestors: ancestors('root', 'topicA') };
    return findNextContent(a13).then(next => {
      expect(next.node.id).toBe('a14');
      expect(next.topic).toBe(null);
    });
  });

  it('after the last item, goes to the first resource of the next topic', () => {
    const a14 = { ...aItems[13], ancestors: ancestors('root', 'topicA') };
    return findNextContent(a14).then(next => {
      // topicEmpty has nothing to open, so topicB, inside its sub-folder.
      expect(next.node.id).toBe('b1');
      expect(next.topic.id).toBe(topicB.id);
    });
  });

  it('climbs up a level when a topic is the last of its folder', () => {
    const b2 = { id: 'b2', parent: 'subB', ancestors: ancestors('root', 'topicB', 'subB') };
    return findNextContent(b2).then(next => {
      expect(next.node.id).toBe('c1');
      expect(next.topic.id).toBe(unit2.id);
    });
  });

  it('is null after the last resource of the channel', () => {
    const c1 = { id: 'c1', parent: 'topicC', ancestors: ancestors('root', 'unit2', 'topicC') };
    return findNextContent(c1).then(next => {
      expect(next).toBe(null);
    });
  });

  it('never goes back to the start of the folder', () => {
    // Before: a resource missing from the (12-item) list gave the first item.
    const a14 = { ...aItems[13], ancestors: ancestors('root', 'topicA') };
    return findNextContent(a14).then(next => {
      expect(next.node.id).not.toBe('a1');
    });
  });

  it('passes coach content and remote device settings through', () => {
    const a1 = { ...aItems[0], ancestors: ancestors('root', 'topicA') };
    return findNextContent(a1, { includeCoachContent: true, baseurl: 'http://peer' }).then(() => {
      expect(ContentNodeResource.fetchCollection).toHaveBeenCalledWith({
        getParams: { parent: 'topicA', include_coach_content: true, baseurl: 'http://peer' },
      });
    });
  });
});

