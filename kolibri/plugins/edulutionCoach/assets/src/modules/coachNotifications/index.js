import maxBy from 'lodash/maxBy';
import sortBy from 'lodash/sortBy';
import notificationsResource from '../../apiResources/notifications';
import { allNotifications, summarizedNotifications } from './getters';

// Seconds between checks for new notifications, per coach polling at the
// same time (the server reports how many), capped at POLL_MAX_FACTOR. One
// coach checks every 10 seconds, six or more every minute. Each check also
// writes a row on the server, so this keeps a centre server with many
// coaches and tablets from being polled every two seconds.
const POLL_BASE_MS = 10000;
const POLL_MAX_FACTOR = 6;

export default {
  namespaced: true,
  state: {
    currentClassroomId: null,
    notifications: [],
    // The pending check's timer, so there is only ever one polling loop.
    poller: null,
  },
  mutations: {
    SET_NOTIFICATIONS(state, notifications) {
      state.notifications = [...notifications];
    },
    APPEND_NOTIFICATIONS(state, notifications) {
      state.notifications = [...notifications, ...state.notifications];
    },
    INSERT_NOTIFICATIONS(state, notifications) {
      state.notifications = sortBy([state.notifications, ...notifications], '-id');
    },
    SET_CURRENT_CLASSROOM_ID(state, classroomId) {
      state.currentClassroomId = classroomId;
    },
    SET_POLLER(state, poller) {
      if (state.poller) {
        clearTimeout(state.poller);
      }
      state.poller = poller;
    },
  },
  getters: {
    allNotifications,
    summarizedNotifications,
    maxNotificationIndex(state) {
      if (state.notifications.length > 0) {
        // IDs are being converted to strings for some reason
        return maxBy(state.notifications, n => Number(n.id)).id;
      }
      return 0;
    },
  },
  actions: {
    stopPolling(store) {
      store.commit('SET_POLLER', null);
      store.commit('SET_CURRENT_CLASSROOM_ID', '');
      // Need to clear out 403 error in store to prevent auth message from showing
      // in other places.
      store.commit('CORE_SET_ERROR', '', { root: true });
    },
    fetchNotificationsForClass(store, classroomId) {
      // Always the class being opened: switching straight from one class to
      // another used to keep polling the first.
      store.commit('SET_CURRENT_CLASSROOM_ID', classroomId);
      return notificationsResource
        .fetchCollection({
          getParams: {
            classroom_id: classroomId,
          },
        })
        .then(data => {
          store.commit('SET_NOTIFICATIONS', data.results);
          store.dispatch('startingPolling', { coachesPolling: data.coaches_polling });
        })
        .catch(() => {
          store.dispatch('startingPolling', { coachesPolling: 0 });
        });
    },
    updateNotificationsForClass(store, { classroomId, after }) {
      // stop polling if not viewing a classroom anymore
      if (!store.state.currentClassroomId) {
        return;
      }
      return notificationsResource
        .fetchCollection({
          getParams: {
            classroom_id: classroomId,
            after,
          },
          force: true,
        })
        .then(data => {
          if (data.results.length > 0) {
            store.commit('APPEND_NOTIFICATIONS', data.results);
            store.dispatch('classSummary/updateWithNotifications', data.results, { root: true });
          }
          store.dispatch('startingPolling', { coachesPolling: data.coaches_polling });
        })
        .catch(() => {
          store.dispatch('startingPolling', { coachesPolling: 0 });
        });
    },
    moreNotificationsForClass(store, params) {
      const classroomId = store.state.currentClassroomId;
      const lastNotification = store.state.notifications.slice(-1)[0];
      // don't fetch if no current classroom
      if (!classroomId || !lastNotification || lastNotification.id <= 1) {
        return Promise.resolve(false);
      }
      const limit = 25;
      return notificationsResource
        .fetchCollection({
          getParams: {
            classroom_id: classroomId,
            before: lastNotification.id,
            limit,
            ...(params || {}),
          },
          force: true,
        })
        .then(data => {
          if (data.results.length > 0) {
            store.commit('INSERT_NOTIFICATIONS', data.results);
            return data.more_results;
          }
          return false;
        })
        .catch(() => {
          return false;
        });
    },
    startingPolling(store, { coachesPolling }) {
      const timeout = POLL_BASE_MS * Math.min(Math.max(coachesPolling, 1), POLL_MAX_FACTOR);
      // SET_POLLER cancels any pending check, so only one loop runs.
      store.commit(
        'SET_POLLER',
        setTimeout(() => {
          store.commit('SET_POLLER', null);
          if (!store.state.currentClassroomId) {
            return;
          }
          // Don't ask the server while the coach page is in a background
          // tab or the tablet screen is off; check again later.
          if (typeof document !== 'undefined' && document.hidden) {
            store.dispatch('startingPolling', { coachesPolling });
            return;
          }
          store.dispatch('updateNotificationsForClass', {
            classroomId: store.state.currentClassroomId,
            after: store.getters.maxNotificationIndex,
          });
        }, timeout)
      );
    },
  },
};
