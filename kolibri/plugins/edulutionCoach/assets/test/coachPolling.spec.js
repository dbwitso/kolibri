import Vue from 'vue';
import Vuex from 'vuex';
import notificationsResource from '../src/apiResources/notifications';
import coachNotifications from '../src/modules/coachNotifications';

jest.mock('../src/apiResources/notifications', () => ({ fetchCollection: jest.fn() }));

Vue.use(Vuex);

// coachNotifications commits CORE_SET_ERROR at the root when it stops.
function makeStore() {
  return new Vuex.Store({
    mutations: { CORE_SET_ERROR() {} },
    modules: { coachNotifications: { ...coachNotifications, state: () => ({ ...coachNotifications.state }) } },
    actions: { 'classSummary/updateWithNotifications'() {} },
  });
}

function setHidden(hidden) {
  Object.defineProperty(document, 'hidden', { configurable: true, get: () => hidden });
}

// Let the fetch promise and the actions it dispatches settle.
async function flush() {
  for (let i = 0; i < 5; i++) {
    await Promise.resolve();
  }
}

describe('coach notification polling', () => {
  let store;

  beforeEach(() => {
    jest.useFakeTimers();
    setHidden(false);
    notificationsResource.fetchCollection.mockReset();
    notificationsResource.fetchCollection.mockResolvedValue({ results: [], coaches_polling: 1 });
    store = makeStore();
  });

  afterEach(() => {
    store.dispatch('coachNotifications/stopPolling');
    jest.useRealTimers();
  });

  it('checks every 10 seconds, not every 2', async () => {
    await store.dispatch('coachNotifications/fetchNotificationsForClass', 'class1');
    await flush();
    expect(notificationsResource.fetchCollection).toHaveBeenCalledTimes(1);
    jest.advanceTimersByTime(9000);
    await flush();
    expect(notificationsResource.fetchCollection).toHaveBeenCalledTimes(1);
    jest.advanceTimersByTime(1000);
    await flush();
    expect(notificationsResource.fetchCollection).toHaveBeenCalledTimes(2);
  });

  it('keeps one loop when the coach opens another class', async () => {
    await store.dispatch('coachNotifications/fetchNotificationsForClass', 'class1');
    await store.dispatch('coachNotifications/fetchNotificationsForClass', 'class2');
    await flush();
    notificationsResource.fetchCollection.mockClear();
    jest.advanceTimersByTime(10000);
    await flush();
    expect(notificationsResource.fetchCollection).toHaveBeenCalledTimes(1);
    expect(notificationsResource.fetchCollection.mock.calls[0][0].getParams.classroom_id).toBe(
      'class2'
    );
  });

  it('waits while the page is hidden', async () => {
    await store.dispatch('coachNotifications/fetchNotificationsForClass', 'class1');
    await flush();
    notificationsResource.fetchCollection.mockClear();
    setHidden(true);
    jest.advanceTimersByTime(60000);
    await flush();
    expect(notificationsResource.fetchCollection).not.toHaveBeenCalled();
    setHidden(false);
    jest.advanceTimersByTime(10000);
    await flush();
    expect(notificationsResource.fetchCollection).toHaveBeenCalledTimes(1);
  });

  it('stops when the coach leaves the class', async () => {
    await store.dispatch('coachNotifications/fetchNotificationsForClass', 'class1');
    await flush();
    store.dispatch('coachNotifications/stopPolling');
    notificationsResource.fetchCollection.mockClear();
    jest.advanceTimersByTime(120000);
    await flush();
    expect(notificationsResource.fetchCollection).not.toHaveBeenCalled();
  });

  it('slows down to once a minute with many coaches', async () => {
    notificationsResource.fetchCollection.mockResolvedValue({ results: [], coaches_polling: 10 });
    await store.dispatch('coachNotifications/fetchNotificationsForClass', 'class1');
    await flush();
    notificationsResource.fetchCollection.mockClear();
    jest.advanceTimersByTime(59000);
    await flush();
    expect(notificationsResource.fetchCollection).not.toHaveBeenCalled();
    jest.advanceTimersByTime(1000);
    await flush();
    expect(notificationsResource.fetchCollection).toHaveBeenCalledTimes(1);
  });
});
