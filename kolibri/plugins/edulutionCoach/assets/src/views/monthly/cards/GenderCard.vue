<template>

  <!-- Girls and boys: the UNESCO breakdown. Preview: reached and active;
       full: every figure. -->
  <div class="scroll">
    <CoreTable>
      <template #headers>
        <th>{{ monthlyString('learnersColumn') }}</th>
        <th class="num">
          {{ monthlyString('enrolledColumn') }}
        </th>
        <th class="num">
          {{ monthlyString('activeColumn') }}
        </th>
        <th class="num">
          {{ monthlyString('reachedColumn') }}
        </th>
        <template v-if="full">
          <th class="num">
            {{ monthlyString('newlyReachedColumn') }}
          </th>
          <th class="num">
            {{ monthlyString('completedColumn') }}
          </th>
          <th class="num">
            {{ monthlyString('sessionsColumn') }}
          </th>
          <th class="num">
            {{ monthlyString('watchingColumn') }}
          </th>
          <th class="num">
            {{ monthlyString('loggedInColumn') }}
          </th>
        </template>
      </template>
      <template #tbody>
        <tbody>
          <tr v-for="row in rows" :key="row.key" :class="{ total: row.key === 'ALL' }">
            <td>{{ row.label }}</td>
            <td class="num">
              {{ $formatNumber(row.enrolled_learners) }}
            </td>
            <td class="num">
              {{ $formatNumber(row.active_learners) }}
            </td>
            <td class="num">
              {{ $formatNumber(row.reached_cumulative) }}
              <span class="pct" :style="{ color: $themeTokens.annotation }">
                {{ percent(row.reached_cumulative, row.enrolled_learners) }}
              </span>
            </td>
            <template v-if="full">
              <td class="num">
                {{ $formatNumber(row.reached_new) }}
              </td>
              <td class="num">
                {{ $formatNumber(row.completions) }}
              </td>
              <td class="num">
                {{ $formatNumber(row.sessions) }}
              </td>
              <td class="num">
                <TimeDuration :seconds="row.video_watch_seconds" />
              </td>
              <td class="num">
                <TimeDuration :seconds="row.logged_in_seconds" />
              </td>
            </template>
          </tr>
        </tbody>
      </template>
    </CoreTable>
  </div>

</template>


<script>

  import CoreTable from 'kolibri.coreVue.components.CoreTable';
  import TimeDuration from 'kolibri.coreVue.components.TimeDuration';
  import { monthlyString, percent, GENDER_KEYS, genderLabel } from '../monthlyStrings';

  export default {
    name: 'GenderCard',
    components: { CoreTable, TimeDuration },
    props: {
      report: { type: Object, required: true },
      full: { type: Boolean, default: false },
    },
    computed: {
      rows() {
        // The preview leaves out "not specified" when nobody is in it.
        const keys = this.full
          ? GENDER_KEYS
          : GENDER_KEYS.filter(
            key => key !== 'NOT_SPECIFIED' || this.report.totals[key].enrolled_learners
          );
        return keys.map(key => ({ key, label: genderLabel(key), ...this.report.totals[key] }));
      },
    },
    methods: { monthlyString, percent },
  };

</script>


<style lang="scss" scoped>

  .scroll {
    overflow-x: auto;
  }

  .num {
    text-align: right;
  }

  .pct {
    margin-left: 4px;
    font-size: 12px;
  }

  .total td {
    font-weight: bold;
  }

</style>
