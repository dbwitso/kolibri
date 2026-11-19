<template>

  <!-- The last six months. Preview: learners reached; full: also active
       learners, and a table of every figure by month. -->
  <div>
    <KGrid gutter="24">
      <KGridItem :layout12="{ span: full ? 6 : 12 }" :layout8="{ span: full ? 4 : 8 }">
        <h3 class="chart-title">
          {{ $tr('reachedChart') }}
        </h3>
        <BarChart
          :bars="bars('reached_cumulative')"
          :max="enrolled"
          :ariaLabel="$tr('reachedChart')"
          :maxBarWidth="48"
        />
      </KGridItem>
      <KGridItem v-if="full" :layout12="{ span: 6 }" :layout8="{ span: 4 }">
        <h3 class="chart-title">
          {{ $tr('activeChart') }}
        </h3>
        <BarChart
          :bars="bars('active_learners')"
          :max="enrolled"
          :ariaLabel="$tr('activeChart')"
          :color="$themeTokens.primaryDark"
          :maxBarWidth="48"
        />
      </KGridItem>
    </KGrid>
    <div v-if="full" class="scroll">
      <CoreTable>
        <template #headers>
          <th>{{ $tr('monthColumn') }}</th>
          <th class="num">
            {{ monthlyString('enrolledColumn') }}
          </th>
          <th class="num">
            {{ monthlyString('activeColumn') }}
          </th>
          <th class="num">
            {{ monthlyString('reachedColumn') }}
          </th>
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
        </template>
        <template #tbody>
          <tbody>
            <tr v-for="month in report.trend" :key="month.month">
              <td>{{ monthName(month.month) }}</td>
              <td class="num">
                {{ $formatNumber(month.enrolled_learners) }}
              </td>
              <td class="num">
                {{ $formatNumber(month.active_learners) }}
              </td>
              <td class="num">
                {{ $formatNumber(month.reached_cumulative) }}
              </td>
              <td class="num">
                {{ $formatNumber(month.reached_new) }}
              </td>
              <td class="num">
                {{ $formatNumber(month.completions) }}
              </td>
              <td class="num">
                {{ $formatNumber(month.sessions) }}
              </td>
              <td class="num">
                <TimeDuration :seconds="month.video_watch_seconds" />
              </td>
            </tr>
          </tbody>
        </template>
      </CoreTable>
    </div>
  </div>

</template>


<script>

  import CoreTable from 'kolibri.coreVue.components.CoreTable';
  import TimeDuration from 'kolibri.coreVue.components.TimeDuration';
  import BarChart from '../../common/BarChart';
  import { monthlyString, noon } from '../monthlyStrings';

  export default {
    name: 'TrendCard',
    components: { CoreTable, BarChart, TimeDuration },
    props: {
      report: { type: Object, required: true },
      full: { type: Boolean, default: false },
    },
    computed: {
      enrolled() {
        return Math.max(this.report.totals.ALL.enrolled_learners, 1);
      },
    },
    methods: {
      monthlyString,
      monthName(month, short) {
        return this.$formatDate(noon(month + '-01'), {
          month: short ? 'short' : 'long',
          year: short ? undefined : 'numeric',
        });
      },
      bars(field) {
        return this.report.trend.map(month => {
          const label = this.monthName(month.month, true);
          return { key: month.month, label, value: month[field], title: `${label}: ${month[field]}` };
        });
      },
    },
    $trs: {
      reachedChart: {
        message: 'Learners reached, by the end of each month',
        context: 'Chart title.',
      },
      activeChart: { message: 'Active learners each month', context: 'Chart title.' },
      monthColumn: { message: 'Month', context: 'Table column.' },
    },
  };

</script>


<style lang="scss" scoped>

  .chart-title {
    margin: 0 0 8px;
    font-size: 15px;
  }

  .scroll {
    margin-top: 24px;
    overflow-x: auto;
  }

  .num {
    text-align: right;
  }

</style>
