<template>

  <!-- Activity over the period: a chart (preview: active learners), and in
       full a choice of figure and a table by day or hour. -->
  <div>
    <KSelect
      v-if="full"
      class="hide-in-print metric-select"
      :label="$tr('showLabel')"
      :options="metricOptions"
      :value="metricOption"
      @change="option => (metric = option.value)"
    />
    <h3 class="chart-title">
      {{ chartTitle }}
    </h3>
    <BarChart
      :bars="bars"
      :ariaLabel="chartTitle"
      :showValues="full || report.series.length <= 7"
      :height="full ? 200 : 140"
      :maxBarWidth="report.period === 'week' ? 56 : 28"
    />
    <div v-if="full" class="scroll">
      <CoreTable>
        <template #headers>
          <th>{{ report.period === 'day' ? $tr('hourColumn') : $tr('dayColumn') }}</th>
          <th v-for="key in metrics" :key="key" class="num">
            {{ monthlyString(key) }}
          </th>
        </template>
        <template #tbody>
          <tbody>
            <tr v-for="row in rows" :key="row.key">
              <td>{{ row.label }}</td>
              <td v-for="key in metrics" :key="key" class="num">
                {{ $formatNumber(row[key]) }}
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
  import BarChart from '../../common/BarChart';
  import { monthlyString, noon } from '../monthlyStrings';

  const METRICS = ['active_learners', 'sessions', 'completions', 'video_watch_seconds'];

  export default {
    name: 'ActivityCard',
    components: { CoreTable, BarChart },
    props: {
      report: { type: Object, required: true },
      full: { type: Boolean, default: false },
    },
    data() {
      return { metric: 'active_learners', metrics: METRICS };
    },
    computed: {
      metricOptions() {
        return METRICS.map(value => ({ value, label: monthlyString(value) }));
      },
      metricOption() {
        return this.metricOptions.find(option => option.value === this.metric);
      },
      chartTitle() {
        const metric = this.metricOption.label;
        return this.report.period === 'day'
          ? this.$tr('byHour', { metric })
          : this.$tr('byDay', { metric });
      },
      // Each bucket with its label; minutes rather than seconds watching.
      rows() {
        return this.report.series.map(row => ({
          ...row,
          video_watch_seconds: Math.round(row.video_watch_seconds / 60),
          label: this.label(row.key),
        }));
      },
      bars() {
        return this.rows.map(row => ({
          key: String(row.key),
          label: this.report.period === 'month' ? String(noon(row.key).getDate()) : row.label,
          value: row[this.metric],
          title: `${row.label}: ${row[this.metric]}`,
        }));
      },
    },
    methods: {
      monthlyString,
      label(key) {
        if (this.report.period === 'day') {
          return String(key).padStart(2, '0') + ':00';
        }
        if (this.report.period === 'week') {
          return this.$formatDate(noon(key), { weekday: 'short', day: 'numeric' });
        }
        return this.$formatDate(noon(key), { weekday: 'short', day: 'numeric', month: 'short' });
      },
    },
    $trs: {
      showLabel: { message: 'Show', context: 'Label of the chart’s figure selector.' },
      byDay: { message: '{metric} by day', context: 'Chart title, e.g. "Active learners by day".' },
      byHour: {
        message: '{metric} by hour',
        context: 'Chart title for a single day, e.g. "Sessions by hour".',
      },
      dayColumn: { message: 'Day', context: 'Table column.' },
      hourColumn: { message: 'Hour', context: 'Table column.' },
    },
  };

</script>


<style lang="scss" scoped>

  .metric-select {
    width: 240px;
    margin: 0 0 8px;
  }

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
