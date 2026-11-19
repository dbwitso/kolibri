<template>

  <!-- Each learner (names: for the coach only, never printed). Preview: the
       learners to follow up, those not reached or who did not come; full:
       everyone. -->
  <div>
    <p v-if="!full && shown.length === 0" :style="{ color: $themeTokens.annotation }">
      {{ $tr('nobodyToFollowUp') }}
    </p>
    <div v-else class="scroll">
      <CoreTable :emptyMessage="coachString('learnerListEmptyState')">
        <template #headers>
          <th>{{ coachString('nameLabel') }}</th>
          <th v-if="full" class="num">
            {{ monthlyString('sessionsColumn') }}
          </th>
          <th v-if="full" class="num">
            {{ monthlyString('loggedInColumn') }}
          </th>
          <th v-if="full" class="num">
            {{ monthlyString('watchingColumn') }}
          </th>
          <th v-if="full" class="num">
            {{ monthlyString('completedColumn') }}
          </th>
          <th>{{ full ? monthlyString('reachedColumn') : $tr('statusColumn') }}</th>
          <th>{{ coachString('lastActivityLabel') }}</th>
        </template>
        <template #tbody>
          <tbody>
            <tr v-for="row in shown" :key="row.id">
              <td>
                <KRouterLink
                  :text="row.name"
                  :to="classRoute('ReportsLearnerReportPage', { learnerId: row.id })"
                  icon="person"
                />
              </td>
              <template v-if="full">
                <td class="num">
                  {{ $formatNumber(row.sessions) }}
                </td>
                <td class="num">
                  <TimeDuration :seconds="row.logged_in_seconds" />
                </td>
                <td class="num">
                  <TimeDuration :seconds="row.video_watch_seconds" />
                </td>
                <td class="num">
                  {{ $formatNumber(row.completions) }}
                </td>
              </template>
              <td>
                <KLabeledIcon
                  v-if="row.reached && full"
                  :icon="row.reached_new ? 'star' : 'correct'"
                  :color="row.reached_new ? $themeTokens.mastered : $themeTokens.correct"
                  :label="row.reached_new
                    ? monthlyString('newlyReached')
                    : monthlyString('reached')"
                />
                <span v-else-if="!full" :style="{ color: $themeTokens.annotation }">
                  {{ row.reached
                    ? monthlyString('notActive')
                    : monthlyString('notReached') }}
                </span>
                <KEmptyPlaceholder v-else />
              </td>
              <td>
                <ElapsedTime v-if="row.last_active" :date="new Date(row.last_active)" />
                <KEmptyPlaceholder v-else />
              </td>
            </tr>
          </tbody>
        </template>
      </CoreTable>
    </div>
  </div>

</template>


<script>

  import ElapsedTime from 'kolibri.coreVue.components.ElapsedTime';
  import TimeDuration from 'kolibri.coreVue.components.TimeDuration';
  import commonCoach from '../../common';
  import { monthlyString } from '../monthlyStrings';

  const PREVIEW = 5;

  export default {
    name: 'LearnersCard',
    components: { ElapsedTime, TimeDuration },
    mixins: [commonCoach],
    props: {
      report: { type: Object, required: true },
      full: { type: Boolean, default: false },
    },
    computed: {
      // Not reached first, then those who did not come this period.
      followUp() {
        const notReached = this.report.learners.filter(row => !row.reached);
        const away = this.report.learners.filter(row => row.reached && !row.sessions);
        return [...notReached, ...away];
      },
      shown() {
        return this.full ? this.report.learners : this.followUp.slice(0, PREVIEW);
      },
    },
    methods: { monthlyString },
    $trs: {
      statusColumn: { message: 'Why', context: 'Table column: why a learner needs follow-up.' },
      nobodyToFollowUp: {
        message: 'Every learner came in this period and has been reached.',
        context: "Shown in the 'Each learner' card when no learner needs follow-up.",
      },
    },
  };

</script>


<style lang="scss" scoped>

  .scroll {
    overflow-x: auto;
  }

  .num {
    text-align: right;
  }

</style>
