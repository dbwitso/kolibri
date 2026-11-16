import { validateUsername } from 'kolibri.utils.validators';

describe('validateUsername', () => {
  it('accepts a username with a dot (MindSpark usernames)', () => {
    expect(validateUsername('kalonda.kamona')).toBe(true);
  });

  it('accepts letters, numbers and underscores', () => {
    expect(validateUsername('learner_01')).toBe(true);
  });

  it('still rejects other punctuation and spaces', () => {
    ['kalonda kamona', 'kalonda-kamona', 'a@b', 'a,b', 'a?b', 'a/b'].forEach(username => {
      expect(validateUsername(username)).toBe(false);
    });
  });
});
