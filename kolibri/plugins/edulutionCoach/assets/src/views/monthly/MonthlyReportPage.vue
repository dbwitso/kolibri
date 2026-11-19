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
            @click="go({ period: option.value })"
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
            @click="go({ date: undefined })"
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

        <!-- Headline figures: on every view -->
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
      </template>
    </KPageContainer>

    <template v-if="report">
      <!-- One card, in full ("View all") -->
      <KPageContainer v-if="openCard" class="card-page" :class="{ dim: loading }">
        <BackLink :to="overviewRoute" :text="$tr('allCards')" class="hide-in-print" />
        <h2>
          <KLabeledIcon :icon="openCard.icon" :label="openCard.title" />
        </h2>
        <p class="card-note" :style="{ color: $themeTokens.annotation }">
          {{ openCard.description }}
        </p>
        <TopicProgressList
          v-if="openCard.id === 'topics'"
          :topics="report.topics"
          :learnerCount="report.learners.length"
        />
        <component :is="openCard.component" v-else :report="report" :full="true" />
      </KPageContainer>

      <!-- All the cards: a preview each, "View all" for the rest. Printing
           shows every card in full, but never the learner list. -->
      <KGrid v-else gutter="16" class="cards" :class="{ dim: loading }">
        <KGridItem
          v-for="card in shownCards"
          :key="card.id"
          :layout12="{ span: printing ? 12 : 6 }"
          :class="{ 'hide-in-print': card.id === 'learners' }"
        >
          <Block
            :allLinkText="coachString('viewAllAction')"
            :allLinkRoute="cardRoute(card.id)"
            :showAllLink="!printing"
          >
            <template #title>
              <KLabeledIcon :icon="card.icon" :label="card.title" />
            </template>
            <p class="card-note" :style="{ color: $themeTokens.annotation }">
              {{ card.description }}
            </p>
            <TopicProgressList
              v-if="card.id === 'topics'"
              :topics="printing ? report.topics : report.topics.slice(0, 3)"
              :learnerCount="report.learners.length"
            />
            <component :is="card.component" v-else :report="report" :full="printing" />
          </Block>
        </KGridItem>
      </KGrid>

      <KPageContainer class="definitions-container">
        <p class="definitions" :style="{ color: $themeTokens.annotation }">
          {{ $tr('definitions') }}
        </p>
      </KPageContainer>
    </template>
  </CoachAppBarPage>

</template>


<script>

  import TimeDuration from 'kolibri.coreVue.components.TimeDuration';
  import CoachAppBarPage from '../CoachAppBarPage';
  import commonCoach from '../common';
  import TopicProgressList from '../common/TopicProgressList';
  import Block from '../home/HomePage/Block';
  import CSVExporter from '../../csv/exporter';
  import ClassReportResource from '../../apiResources/classReport';
  import ActivityCard from './cards/ActivityCard';
  import GenderCard from './cards/GenderCard';
  import LearnersCard from './cards/LearnersCard';
  import TrendCard from './cards/TrendCard';
  import { isoDate, noon, percent, monthlyString, GENDER_KEYS } from './monthlyStrings';

  const PERIODS = ['day', 'week', 'month'];

  export default {
    name: 'MonthlyReportPage',
    components: {
      Block,
      CoachAppBarPage,
      TimeDuration,
      TopicProgressList,
    },
    mixins: [commonCoach],
    data() {
      return {
        today: isoDate(new Date()),
        report: null,
        loading: false,
        error: false,
        printing: false,
      };
    },
    computed: {
      // The period and date are in the address, so "View all", Back and a
      // shared link keep them.
      period() {
        const period = this.$route.query.period;
        return PERIODS.includes(period) ? period : 'month';
      },
      anchor() {
        const date = this.$route.query.date;
        return /^\d{4}-\d{2}-\d{2}$/.test(date || '') ? date : this.today;
      },
      cards() {
        return [
          {
            id: 'activity',
            icon: 'inProgress',
            title: this.$tr('activityCard'),
            description: this.$tr('activityDescription'),
            component: ActivityCard,
          },
          {
            id: 'gender',
            icon: 'people',
            title: this.$tr('genderCard'),
            description: this.$tr('genderDescription'),
            component: GenderCard,
          },
          {
            id: 'trend',
            icon: 'reports',
            title: this.$tr('trendCard'),
            description: this.$tr('trendDescription'),
            component: TrendCard,
          },
          {
            id: 'topics',
            icon: 'topic',
            title: this.$tr('topicsCard'),
            description: this.$tr('topicsDescription'),
          },
          {
            id: 'learners',
            icon: 'person',
            title: this.$tr('learnersCard'),
            description: this.$tr('learnersDescription'),
            component: LearnersCard,
          },
        ];
      },
      shownCards() {
        return this.cards.filter(card => card.id !== 'topics' || this.report.topics.length);
      },
      openCard() {
        return this.cards.find(card => card.id === this.$route.params.section) || null;
      },
      overviewRoute() {
        return this.cardRoute(undefined);
      },
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
        if (this.report.period === 'month') {
          return this.$formatDate(start, { month: 'long', year: 'numeric' });
        }
        if (this.report.period === 'week') {
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
      tiles() {
        const all = this.report.totals.ALL;
        const active = all.active_learners;
        return [
          {
            key: 'reached',
            icon: 'star',
            label: this.$tr('reachedTile'),
            value: all.reached_cumulative,
            sub: this.$tr('reachedSub', {
              percent: percent(all.reached_cumulative, all.enrolled_learners) || '0%',
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
              percent: percent(active, all.enrolled_learners) || '0%',
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
      // The address for a card (or, with no id, all the cards), keeping the
      // period and date.
      cardRoute(section) {
        return {
          name: 'MonthlyReportPage',
          params: { classId: this.classId, section },
          query: this.$route.query,
        };
      },
      go(changes) {
        const query = { ...this.$route.query, ...changes };
        Object.keys(query).forEach(key => query[key] === undefined && delete query[key]);
        this.$router.replace({ ...this.cardRoute(this.$route.params.section), query });
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
        this.go({ date: isoDate(date) });
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
        const rows = GENDER_KEYS.map(gender => ({
          centre_code: this.report.centre_code,
          class: this.className,
          period: this.report.period,
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
          { name: monthlyString('sessionsColumn'), key: 'sessions' },
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
          { name: monthlyString('completedColumn'), key: 'completions' },
          {
            name: monthlyString('reachedColumn'),
            key: 'reached',
            format: row => (row.reached ? 1 : 0),
          },
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
      // Every card in full (the learner list stays out), then print.
      print() {
        if (this.openCard) {
          window.print();
          return;
        }
        this.printing = true;
        this.$nextTick(() => {
          window.print();
          this.printing = false;
        });
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
      allCards: { message: 'All figures', context: 'Back link from one card to all the cards.' },
      activityCard: { message: 'Activity', context: 'Card title.' },
      activityDescription: {
        message: 'When learners came and what they did, through the period.',
        context: "Under the 'Activity' card title.",
      },
      genderCard: { message: 'Girls and boys', context: 'Card title.' },
      genderDescription: {
        message: 'The same figures as the monthly report sent to UNESCO.',
        context: "Under the 'Girls and boys' card title.",
      },
      trendCard: { message: 'The last six months', context: 'Card title.' },
      trendDescription: {
        message: 'How reach and attendance have changed, month by month.',
        context: "Under the 'The last six months' card title.",
      },
      topicsCard: { message: 'Topic progress', context: 'Card title.' },
      topicsDescription: {
        message: "The band's topics in order, to date. A learner has completed a topic when they have finished all its resources.",
        context: "Under the 'Topic progress' card title.",
      },
      learnersCard: { message: 'Each learner', context: 'Card title.' },
      learnersDescription: {
        message: 'Learners to follow up first: not yet reached, or did not come. View all for everyone.',
        context: "Under the 'Each learner' card title. Names are shown to the coach only.",
      },
      definitions: {
        message:
          'Reached: finished at least one resource. Active: signed in at least once in the period. Teacher channels are not counted. Days run midnight to midnight, Lusaka time.',
        context: 'Definitions at the foot of the Monthly reports page.',
      },
      loggedInMinutesColumn: { message: 'Logged in (minutes)', context: 'CSV column.' },
      watchingMinutesColumn: { message: 'Watching (minutes)', context: 'CSV column.' },
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
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    margin-top: 16px;
  }

  .dim {
    opacity: 0.5;
    transition: opacity 0.2s;
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

  .card-page {
    margin-top: 16px;
  }

  .card-note {
    margin-top: 0;
    font-size: 14px;
  }

  .definitions-container {
    margin-top: 16px;
  }

  .definitions {
    margin: 0;
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
