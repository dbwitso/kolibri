<template>

  <CoachAppBarPage
    :authorized="userIsAuthorized"
    authorizedRole="adminOrCoach"
    :showSubNav="true"
  >
    <KPageContainer>
      <div class="heading">
        <div>
          <h1 class="title">
            <KLabeledIcon icon="schedule" :label="$tr('title')" />
          </h1>
          <p class="subtitle" :style="{ color: $themeTokens.annotation }">
            {{ className }}<template v-if="report && report.centre_code">
              · {{ report.centre_code }}
            </template>
          </p>
        </div>
        <div class="actions hide-in-print">
          <KButton
            appearance="flat-button"
            icon="download"
            :text="$tr('downloadSummary')"
            :disabled="!report"
            @click="downloadSummary"
          />
          <KButton
            appearance="flat-button"
            icon="download"
            :text="$tr('downloadLearners')"
            :disabled="!report"
            @click="downloadLearners"
          />
          <KButton
            appearance="raised-button"
            :primary="true"
            icon="print"
            :text="$tr('printSummary')"
            :disabled="!report"
            @click="print"
          />
        </div>
      </div>
      <p class="hide-in-print share-note" :style="{ color: $themeTokens.annotation }">
        {{ $tr('shareNote') }}
      </p>

      <!-- Day, week or month, and which one -->
      <div class="hide-in-print period-bar" :style="{ borderColor: $themeTokens.fineLine }">
        <div class="period-choice" role="group" :aria-label="$tr('periodLabel')">
          <KButton
            v-for="option in periodOptions"
            :key="option.value"
            :appearance="period === option.value ? 'raised-button' : 'flat-button'"
            :primary="period === option.value"
            :text="option.label"
            :aria-pressed="String(period === option.value)"
            @click="setPeriod(option.value)"
          />
        </div>
        <div class="period-step">
          <KIconButton
            icon="chevronLeft"
            :ariaLabel="$tr('previousPeriod')"
            :tooltip="$tr('previousPeriod')"
            @click="step(-1)"
          />
          <span class="period-label">{{ periodLabel }}</span>
          <KIconButton
            icon="chevronRight"
            :ariaLabel="$tr('nextPeriod')"
            :tooltip="$tr('nextPeriod')"
            :disabled="isCurrentPeriod"
            @click="step(1)"
          />
          <KButton
            v-if="!isCurrentPeriod"
            appearance="basic-link"
            :text="$tr('backToNow')"
            @click="anchor = today"
          />
        </div>
      </div>
      <h2 class="print-only">
        {{ periodLabel }}
      </h2>

      <KCircularLoader v-if="loading && !report" class="loader" />
      <p v-else-if="error" :style="{ color: $themeTokens.error }">
        {{ $tr('loadError') }}
      </p>

      <template v-if="report">
        <p v-if="notes.length" class="notes" :style="{ color: $themeTokens.annotation }">
          <span v-for="note in notes" :key="note">{{ note }} </span>
        </p>

        <!-- Headline figures -->
        <div class="tiles" :class="{ dim: loading }">
          <div
            v-for="tile in tiles"
            :key="tile.key"
            class="tile"
            :style="{ borderColor: $themeTokens.fineLine, backgroundColor: $themeTokens.surface }"
          >
            <div class="tile-label" :style="{ color: $themeTokens.annotation }">
              <KIcon :icon="tile.icon" :color="$themeTokens.primary" class="tile-icon" />
              {{ tile.label }}
            </div>
            <div class="tile-value">
              <TimeDuration v-if="tile.seconds !== undefined" :seconds="tile.seconds" />
              <template v-else>
                {{ $formatNumber(tile.value) }}
              </template>
            </div>
            <div class="tile-sub" :style="{ color: $themeTokens.annotation }">
              {{ tile.sub }}
            </div>
          </div>
        </div>

        <!-- Activity over the period -->
        <section class="section">
          <div class="section-heading">
            <h2>{{ chartTitle }}</h2>
            <KSelect
              class="hide-in-print metric-select"
              :label="$tr('showLabel')"
              :options="metricOptions"
              :value="metricOption"
              @change="option => (metric = option.value)"
            />
          </div>
          <BarChart
            :bars="chartBars"
            :ariaLabel="chartTitle"
            :showValues="report.series.length <= 31"
            :height="170"
            :maxBarWidth="shownPeriod === 'week' ? 56 : 28"
          />
        </section>

        <!-- Girls and boys -->
        <section class="section">
          <h2>{{ $tr('byGenderTitle') }}</h2>
          <p class="section-note" :style="{ color: $themeTokens.annotation }">
            {{ $tr('byGenderDescription') }}
          </p>
          <div class="scroll">
            <CoreTable>
              <template #headers>
                <th>{{ $tr('groupColumn') }}</th>
                <th class="num">
                  {{ $tr('enrolledColumn') }}
                </th>
                <th class="num">
                  {{ $tr('activeColumn') }}
                </th>
                <th class="num">
                  {{ $tr('reachedColumn') }}
                </th>
                <th class="num">
                  {{ $tr('newlyReachedColumn') }}
                </th>
                <th class="num">
                  {{ $tr('completedColumn') }}
                </th>
                <th class="num">
                  {{ $tr('sessionsColumn') }}
                </th>
                <th class="num">
                  {{ $tr('watchingColumn') }}
                </th>
              </template>
              <template #tbody>
                <tbody>
                  <tr
                    v-for="row in genderRows"
                    :key="row.key"
                    :class="{ total: row.key === 'ALL' }"
                  >
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
                  </tr>
                </tbody>
              </template>
            </CoreTable>
          </div>
        </section>

        <!-- The last six months -->
        <section class="section">
          <h2>{{ $tr('trendTitle') }}</h2>
          <KGrid gutter="24">
            <KGridItem :layout12="{ span: 6 }" :layout8="{ span: 4 }">
              <h3 class="chart-title">
                {{ $tr('trendReached') }}
              </h3>
              <BarChart
                :bars="trendBars('reached_cumulative')"
                :max="Math.max(report.totals.ALL.enrolled_learners, 1)"
                :ariaLabel="$tr('trendReached')"
                :maxBarWidth="48"
              />
            </KGridItem>
            <KGridItem :layout12="{ span: 6 }" :layout8="{ span: 4 }">
              <h3 class="chart-title">
                {{ $tr('trendActive') }}
              </h3>
              <BarChart
                :bars="trendBars('active_learners')"
                :max="Math.max(report.totals.ALL.enrolled_learners, 1)"
                :ariaLabel="$tr('trendActive')"
                :color="$themeTokens.primaryDark"
                :maxBarWidth="48"
              />
            </KGridItem>
          </KGrid>
        </section>

        <!-- Topics of the band, to date -->
        <section v-if="report.topics.length" class="section">
          <h2>{{ $tr('topicsTitle') }}</h2>
          <p class="section-note" :style="{ color: $themeTokens.annotation }">
            {{ $tr('topicsDescription') }}
          </p>
          <TopicProgressList :topics="report.topics" :learnerCount="report.learners.length" />
        </section>

        <!-- Each learner: names, so for the coach only, never printed -->
        <section class="hide-in-print section">
          <h2>{{ $tr('learnersTitle') }}</h2>
          <p class="section-note" :style="{ color: $themeTokens.annotation }">
            {{ $tr('learnersDescription') }}
          </p>
          <div class="scroll">
            <CoreTable :emptyMessage="coachString('learnerListEmptyState')">
              <template #headers>
                <th>{{ coachString('nameLabel') }}</th>
                <th class="num">
                  {{ $tr('sessionsColumn') }}
                </th>
                <th class="num">
                  {{ $tr('loggedInColumn') }}
                </th>
                <th class="num">
                  {{ $tr('watchingColumn') }}
                </th>
                <th class="num">
                  {{ $tr('completedColumn') }}
                </th>
                <th>{{ $tr('reachedColumn') }}</th>
                <th>{{ coachString('lastActivityLabel') }}</th>
              </template>
              <template #tbody>
                <tbody>
                  <tr v-for="row in report.learners" :key="row.id">
                    <td>
                      <KRouterLink
                        :text="row.name"
                        :to="classRoute('ReportsLearnerReportPage', { learnerId: row.id })"
                        icon="person"
                      />
                    </td>
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
                    <td>
                      <KLabeledIcon
                        v-if="row.reached"
                        :icon="row.reached_new ? 'star' : 'correct'"
                        :color="row.reached_new ? $themeTokens.mastered : $themeTokens.correct"
                        :label="row.reached_new ? $tr('newlyReached') : $tr('reached')"
                      />
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
        </section>

        <p class="definitions" :style="{ color: $themeTokens.annotation }">
          {{ $tr('definitions') }}
        </p>
      </template>
    </KPageContainer>
  </CoachAppBarPage>

</template>


<script>

  import ElapsedTime from 'kolibri.coreVue.components.ElapsedTime';
  import TimeDuration from 'kolibri.coreVue.components.TimeDuration';
  import CoachAppBarPage from '../CoachAppBarPage';
  import commonCoach from '../common';
  import BarChart from '../common/BarChart';
  import TopicProgressList from '../common/TopicProgressList';
  import CSVExporter from '../../csv/exporter';
  import ClassReportResource from '../../apiResources/classReport';

  // A date as YYYY-MM-DD, in the browser's time zone.
  function isoDate(date) {
    const pad = n => String(n).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  }

  // Midday of a YYYY-MM-DD date, so formatting never shifts the day.
  function noon(iso) {
    return new Date(String(iso).slice(0, 10) + 'T12:00:00');
  }

  const METRICS = ['active_learners', 'sessions', 'completions', 'video_watch_seconds'];

  export default {
    name: 'MonthlyReportPage',
    components: {
      BarChart,
      CoachAppBarPage,
      ElapsedTime,
      TimeDuration,
      TopicProgressList,
    },
    mixins: [commonCoach],
    data() {
      const today = isoDate(new Date());
      return {
        period: 'month',
        anchor: today,
        today,
        metric: 'active_learners',
        report: null,
        loading: false,
        error: false,
      };
    },
    computed: {
      periodOptions() {
        return [
          { value: 'day', label: this.$tr('day') },
          { value: 'week', label: this.$tr('week') },
          { value: 'month', label: this.$tr('month') },
        ];
      },
      periodLabel() {
        if (!this.report) {
          return '';
        }
        const start = noon(this.report.start);
        if (this.shownPeriod === 'month') {
          return this.$formatDate(start, { month: 'long', year: 'numeric' });
        }
        if (this.shownPeriod === 'week') {
          const last = new Date(start);
          last.setDate(last.getDate() + 6);
          return this.$tr('weekOf', {
            start: this.$formatDate(start, { day: 'numeric', month: 'short' }),
            end: this.$formatDate(last, { day: 'numeric', month: 'short', year: 'numeric' }),
          });
        }
        return this.$formatDate(start, {
          weekday: 'long',
          day: 'numeric',
          month: 'long',
          year: 'numeric',
        });
      },
      // The period of the report on screen.
      shownPeriod() {
        return this.report ? this.report.period : this.period;
      },
      isCurrentPeriod() {
        return !this.report || !this.report.complete;
      },
      notes() {
        const notes = [];
        if (this.report && !this.report.complete) {
          notes.push(this.$tr('notOverYet'));
        }
        if (this.report && this.report.class_record_month) {
          notes.push(this.$tr('fromClassRecord'));
        }
        return notes;
      },
      all() {
        return this.report.totals.ALL;
      },
      tiles() {
        const all = this.all;
        const active = all.active_learners;
        return [
          {
            key: 'reached',
            icon: 'star',
            label: this.$tr('reachedTile'),
            value: all.reached_cumulative,
            sub: this.$tr('reachedSub', {
              percent: this.percent(all.reached_cumulative, all.enrolled_learners) || '0%',
              enrolled: all.enrolled_learners,
              newly: all.reached_new,
            }),
          },
          {
            key: 'active',
            icon: 'people',
            label: this.$tr('activeTile'),
            value: active,
            sub: this.$tr('ofEnrolled', {
              percent: this.percent(active, all.enrolled_learners) || '0%',
            }),
          },
          {
            key: 'sessions',
            icon: 'inProgress',
            label: this.$tr('sessionsTile'),
            value: all.sessions,
            sub: this.$tr('perActiveLearner', {
              value: active ? (all.sessions / active).toFixed(1) : '0',
            }),
          },
          {
            key: 'watching',
            icon: 'video',
            label: this.$tr('watchingTile'),
            seconds: all.video_watch_seconds,
            sub: this.$tr('averagePerLearner', {
              minutes: active ? Math.round(all.video_watch_seconds / active / 60) : 0,
            }),
          },
          {
            key: 'logged',
            icon: 'person',
            label: this.$tr('loggedInTile'),
            seconds: all.logged_in_seconds,
            sub: this.$tr('averagePerLearner', {
              minutes: active ? Math.round(all.logged_in_seconds / active / 60) : 0,
            }),
          },
          {
            key: 'completed',
            icon: 'correct',
            label: this.$tr('completedTile'),
            value: all.completions,
            sub: this.$tr('completedSub'),
          },
        ];
      },
      metricOptions() {
        return METRICS.map(value => ({ value, label: this.$tr(value) }));
      },
      metricOption() {
        return this.metricOptions.find(option => option.value === this.metric);
      },
      chartTitle() {
        const by = { day: 'byHour', week: 'byDay', month: 'byDay' }[this.shownPeriod];
        return this.$tr(by, { metric: this.metricOption.label });
      },
      chartBars() {
        const isMinutes = this.metric === 'video_watch_seconds';
        return this.report.series.map(row => {
          const value = isMinutes ? Math.round(row[this.metric] / 60) : row[this.metric];
          let label;
          if (this.shownPeriod === 'day') {
            label = String(row.key).padStart(2, '0');
          } else if (this.shownPeriod === 'week') {
            label = this.$formatDate(noon(row.key), { weekday: 'short' });
          } else {
            label = String(noon(row.key).getDate());
          }
          return { key: String(row.key), label, value, title: `${label}: ${value}` };
        });
      },
      genderRows() {
        const labels = {
          FEMALE: this.$tr('girls'),
          MALE: this.$tr('boys'),
          NOT_SPECIFIED: this.$tr('notSpecified'),
          ALL: this.$tr('allLearners'),
        };
        return ['FEMALE', 'MALE', 'NOT_SPECIFIED', 'ALL'].map(key => ({
          key,
          label: labels[key],
          ...this.report.totals[key],
        }));
      },
    },
    watch: {
      period() {
        this.fetch();
      },
      anchor() {
        this.fetch();
      },
    },
    created() {
      this.fetch();
    },
    methods: {
      fetch() {
        // Only the latest request's answer is shown, when a coach clicks
        // through periods faster than the answers arrive.
        const request = (this.lastRequest = (this.lastRequest || 0) + 1);
        this.loading = true;
        this.error = false;
        return ClassReportResource.fetchModel({
          id: this.classId,
          getParams: { period: this.period, date: this.anchor },
          force: true,
        })
          .then(report => {
            if (request === this.lastRequest) {
              this.report = report;
            }
          })
          .catch(() => {
            if (request === this.lastRequest) {
              this.error = true;
            }
          })
          .then(() => {
            if (request === this.lastRequest) {
              this.loading = false;
            }
          });
      },
      setPeriod(period) {
        this.period = period;
      },
      step(direction) {
        const date = noon(this.anchor);
        if (this.period === 'day') {
          date.setDate(date.getDate() + direction);
        } else if (this.period === 'week') {
          date.setDate(date.getDate() + 7 * direction);
        } else {
          date.setDate(1);
          date.setMonth(date.getMonth() + direction);
        }
        this.anchor = isoDate(date);
      },
      percent(part, whole) {
        return whole ? Math.round((100 * part) / whole) + '%' : '';
      },
      trendBars(field) {
        return this.report.trend.map(month => {
          const label = this.$formatDate(noon(month.month + '-01'), { month: 'short' });
          return { key: month.month, label, value: month[field], title: `${label}: ${month[field]}` };
        });
      },
      fileLabel() {
        return `${this.className} ${this.periodLabel}`;
      },
      // Counts only, one row per gender: fit to send to partners.
      downloadSummary() {
        const fields = [
          'enrolled_learners',
          'active_learners',
          'sessions',
          'reached_new',
          'reached_cumulative',
          'completions',
          'video_watch_seconds',
          'logged_in_seconds',
        ];
        const columns = [
          { name: 'centre_code', key: 'centre_code' },
          { name: 'class', key: 'class' },
          { name: 'period', key: 'period' },
          { name: 'start', key: 'start' },
          { name: 'end', key: 'end' },
          { name: 'gender', key: 'gender' },
          ...fields.map(key => ({ name: key, key })),
        ];
        const rows = ['FEMALE', 'MALE', 'NOT_SPECIFIED', 'ALL'].map(gender => ({
          centre_code: this.report.centre_code,
          class: this.className,
          period: this.period,
          start: this.report.start.slice(0, 10),
          end: this.report.end.slice(0, 10),
          gender,
          ...this.report.totals[gender],
        }));
        new CSVExporter(columns, this.$tr('summaryFile', { label: this.fileLabel() })).export(rows);
      },
      downloadLearners() {
        const columns = [
          { name: this.coachString('nameLabel'), key: 'name' },
          { name: this.$tr('sessionsColumn'), key: 'sessions' },
          {
            name: this.$tr('loggedInMinutesColumn'),
            key: 'logged_in_seconds',
            format: row => Math.round(row.logged_in_seconds / 60),
          },
          {
            name: this.$tr('watchingMinutesColumn'),
            key: 'video_watch_seconds',
            format: row => Math.round(row.video_watch_seconds / 60),
          },
          { name: this.$tr('completedColumn'), key: 'completions' },
          { name: this.$tr('reachedColumn'), key: 'reached', format: row => (row.reached ? 1 : 0) },
          {
            name: this.coachString('lastActivityLabel'),
            key: 'last_active',
            format: row => row.last_active || '',
          },
        ];
        new CSVExporter(columns, this.$tr('learnersFile', { label: this.fileLabel() })).export(
          this.report.learners
        );
      },
      print() {
        window.print();
      },
    },
    $trs: {
      title: {
        message: 'Monthly reports',
        context: "Title of the coach's page with the class's LSHE figures by day, week and month.",
      },
      shareNote: {
        message:
          'The summary and the printed page hold counts only, no learner names, so they can be shared with partners such as UNESCO. The learner list is for you only.',
        context: 'Note on the Monthly reports page about what may be shared outside the school.',
      },
      downloadSummary: {
        message: 'Download summary',
        context: 'Button: downloads a CSV of the period’s figures by gender, with no names.',
      },
      downloadLearners: {
        message: 'Download learner list',
        context: 'Button: downloads a CSV with a row per learner, with names.',
      },
      printSummary: {
        message: 'Print summary',
        context: 'Button: prints the page without the learner list (no names).',
      },
      periodLabel: {
        message: 'Report period',
        context: 'Accessible name for the Day / Week / Month buttons.',
      },
      day: { message: 'Day', context: 'Report period option.' },
      week: { message: 'Week', context: 'Report period option.' },
      month: { message: 'Month', context: 'Report period option.' },
      previousPeriod: { message: 'Previous', context: 'Button: the previous day, week or month.' },
      nextPeriod: { message: 'Next', context: 'Button: the next day, week or month.' },
      backToNow: { message: 'Back to today', context: 'Link: the current day, week or month.' },
      weekOf: {
        message: '{start} – {end}',
        context: 'A week, Monday to Sunday, e.g. "16 Nov – 22 Nov 2026".',
      },
      loadError: {
        message: 'The report could not be loaded. Check the connection and try again.',
        context: 'Error on the Monthly reports page.',
      },
      notOverYet: {
        message: 'This period is not over yet: figures so far.',
        context: 'Note on the Monthly reports page for the current day, week or month.',
      },
      fromClassRecord: {
        message:
          "Learners are counted from the class list saved for this month's report, so these figures match it.",
        context: 'Note on the Monthly reports page for a finished month already reported.',
      },
      reachedTile: { message: 'Learners reached', context: 'Headline figure (UNESCO measure).' },
      reachedSub: {
        message: '{percent} of {enrolled, number} enrolled · {newly, number} new this period',
        context:
          "Under 'Learners reached': share of enrolled learners who have finished at least one resource, and how many did so for the first time in the period.",
      },
      activeTile: { message: 'Active learners', context: 'Headline figure.' },
      ofEnrolled: {
        message: '{percent} of enrolled learners came',
        context: "Under 'Active learners'.",
      },
      sessionsTile: { message: 'Sessions', context: 'Headline figure: times learners signed in.' },
      perActiveLearner: {
        message: 'about {value} per active learner',
        context: "Under 'Sessions'.",
      },
      watchingTile: { message: 'Time watching', context: 'Headline figure: video time.' },
      loggedInTile: { message: 'Time logged in', context: 'Headline figure.' },
      averagePerLearner: {
        message: 'about {minutes, number} min per active learner',
        context: 'Under a time figure: the average per learner who came.',
      },
      completedTile: { message: 'Resources completed', context: 'Headline figure.' },
      completedSub: {
        message: 'videos and activities finished',
        context: "Under 'Resources completed'.",
      },
      showLabel: { message: 'Show', context: 'Label of the chart’s figure selector.' },
      active_learners: { message: 'Active learners', context: 'Chart figure option.' },
      sessions: { message: 'Sessions', context: 'Chart figure option.' },
      completions: { message: 'Resources completed', context: 'Chart figure option.' },
      video_watch_seconds: { message: 'Minutes watching', context: 'Chart figure option.' },
      byDay: { message: '{metric} by day', context: 'Chart title, e.g. "Active learners by day".' },
      byHour: {
        message: '{metric} by hour',
        context: 'Chart title for a single day, e.g. "Sessions by hour".',
      },
      byGenderTitle: { message: 'Girls and boys', context: 'Section title.' },
      byGenderDescription: {
        message: 'The same figures as the monthly report sent to UNESCO.',
        context: "Under the 'Girls and boys' section title.",
      },
      groupColumn: { message: 'Learners', context: 'Table column: girls, boys, all.' },
      enrolledColumn: { message: 'Enrolled', context: 'Table column.' },
      activeColumn: { message: 'Active', context: 'Table column.' },
      reachedColumn: { message: 'Reached', context: 'Table column (UNESCO measure).' },
      newlyReachedColumn: { message: 'Newly reached', context: 'Table column.' },
      completedColumn: { message: 'Completed', context: 'Table column: resources finished.' },
      sessionsColumn: { message: 'Sessions', context: 'Table column.' },
      watchingColumn: { message: 'Watching', context: 'Table column: video time.' },
      loggedInColumn: { message: 'Logged in', context: 'Table column: time signed in.' },
      loggedInMinutesColumn: { message: 'Logged in (minutes)', context: 'CSV column.' },
      watchingMinutesColumn: { message: 'Watching (minutes)', context: 'CSV column.' },
      girls: { message: 'Girls', context: 'Table row.' },
      boys: { message: 'Boys', context: 'Table row.' },
      notSpecified: { message: 'Not specified', context: 'Table row: gender not recorded.' },
      allLearners: { message: 'All learners', context: 'Table row: total.' },
      trendTitle: { message: 'The last six months', context: 'Section title.' },
      trendReached: {
        message: 'Learners reached, by the end of each month',
        context: 'Chart title.',
      },
      trendActive: { message: 'Active learners each month', context: 'Chart title.' },
      topicsTitle: { message: 'Topic progress', context: 'Section title.' },
      topicsDescription: {
        message: "The band's topics in order, to date. A learner has completed a topic when they have finished all its resources.",
        context: "Under the 'Topic progress' section title.",
      },
      learnersTitle: { message: 'Each learner', context: 'Section title.' },
      learnersDescription: {
        message: 'For this period. Learners marked with a star were reached for the first time.',
        context: "Under the 'Each learner' section title.",
      },
      reached: { message: 'Reached', context: 'A learner has finished at least one resource.' },
      newlyReached: {
        message: 'Newly reached',
        context: 'A learner finished their first resource in this period.',
      },
      definitions: {
        message:
          'Reached: finished at least one resource. Active: signed in at least once in the period. Teacher channels are not counted. Days run midnight to midnight, Lusaka time.',
        context: 'Definitions at the foot of the Monthly reports page.',
      },
      summaryFile: { message: 'LSHE summary {label}', context: 'Downloaded file name.' },
      learnersFile: { message: 'LSHE learners {label}', context: 'Downloaded file name.' },
    },
  };

</script>


<style lang="scss" scoped>

  .heading {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    align-items: flex-start;
    justify-content: space-between;
  }

  .title {
    margin: 0;
  }

  .subtitle {
    margin: 4px 0 0;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .share-note {
    margin: 8px 0 16px;
    font-size: 14px;
  }

  .period-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
    border-top: 1px solid;
    border-bottom: 1px solid;
  }

  .period-choice {
    display: flex;
    gap: 4px;
  }

  .period-step {
    display: flex;
    gap: 4px;
    align-items: center;
  }

  .period-label {
    min-width: 180px;
    font-weight: bold;
    text-align: center;
  }

  .loader {
    margin: 48px auto;
  }

  .notes {
    margin: 12px 0 0;
    font-size: 14px;
  }

  .tiles {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 12px;
    margin-top: 16px;
    transition: opacity 0.2s;

    &.dim {
      opacity: 0.5;
    }
  }

  .tile {
    padding: 16px;
    border: 1px solid;
    border-radius: 8px;
  }

  .tile-label {
    font-size: 14px;
  }

  .tile-icon {
    position: relative;
    top: 3px;
    margin-right: 4px;
  }

  .tile-value {
    margin: 4px 0;
    font-size: 30px;
    font-weight: bold;
  }

  .tile-sub {
    font-size: 13px;
  }

  .section {
    margin-top: 32px;
    break-inside: avoid;
  }

  .section-heading {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    align-items: flex-end;
    justify-content: space-between;
  }

  .metric-select {
    width: 220px;
    margin: 0;
  }

  .section-note {
    margin-top: -8px;
    font-size: 14px;
  }

  .chart-title {
    font-size: 15px;
  }

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

  .definitions {
    margin-top: 32px;
    font-size: 13px;
  }

  .print-only {
    display: none;
  }

  @media print {
    .hide-in-print {
      display: none !important;
    }

    .print-only {
      display: block;
    }
  }

</style>
