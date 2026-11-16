import store from 'kolibri.coreVue.vuex.store';
import { ERROR_CONSTANTS } from '../../constants';

jest.unmock('../client');
const client = require('../client').default;

function reject400(data) {
  // An axios adapter that fails the request the way the server would.
  return config =>
    Promise.reject(Object.assign(new Error('400'), { config, response: { status: 400, data } }));
}

describe('grade band rejection snackbar', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.spyOn(store, 'commit').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    store.commit.mockRestore();
  });

  it("shows the server's message for GRADE_BAND_NOT_ALLOWED", async () => {
    const message = 'Not allowed for class "Grade 4 A" (grade band G4-5): "X".';
    await expect(
      client({
        url: '/api/lessons/lesson/',
        method: 'post',
        adapter: reject400([{ id: ERROR_CONSTANTS.GRADE_BAND_NOT_ALLOWED, metadata: { message } }]),
      })
    ).rejects.toBeTruthy();
    jest.runAllTimers();
    expect(store.commit).toHaveBeenCalledWith(
      'CORE_CREATE_SNACKBAR',
      expect.objectContaining({ text: message })
    );
  });

  it('ignores other validation errors', async () => {
    await expect(
      client({
        url: '/api/lessons/lesson/',
        method: 'post',
        adapter: reject400([{ id: ERROR_CONSTANTS.UNIQUE, metadata: { message: 'dup' } }]),
      })
    ).rejects.toBeTruthy();
    jest.runAllTimers();
    expect(store.commit).not.toHaveBeenCalledWith('CORE_CREATE_SNACKBAR', expect.anything());
  });
});
