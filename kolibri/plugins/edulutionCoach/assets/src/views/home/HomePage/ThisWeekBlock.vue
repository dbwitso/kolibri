<template>

  <!-- Who came each day this week and for how long, from the class
       summary (class_summary_api.get_week_attendance). "View all" opens
       the attendance report, which has every learner and any date range. -->
  <Block
    :allLinkText="coachString('viewAllAction')"
    :allLinkRoute="classRoute('ReportsAttendanceListPage')"
    :showAllLink="true"
  >
    <template #title>
      <KLabeledIcon icon="people" :label="$tr('thisWeekLabel')" />
    </template>
    <p :style="{ color: $themeTokens.annotation }">
      {{ $tr('description') }}
    </p>
    <div
      class="chart"
      role="img"
      :aria-label="chartLabel"
      :style="{ borderBottomColor: $themeTokens.fineLine }"
    >
      <div v-for="day in days" :key="day.date" class="column">
        <span class="count">{{ day.learners === null ? '' : $formatNumber(day.learners) }}</span>
        <div
          class="bar"
          :style="{
            height: day.height,
            backgroundColor: day.learners === null ? $themeTokens.fineLine : $themeTokens.primary,
          }"
        ></div>
      </div>
    </div>
    <div class="labels" aria-hidden="true">
      <span
        v-for="day in days"
        :key="day.date"
        :style="{ color: $themeTokens.annotation }"
      >{{ day.label }}</span>
    </div>
    <p v-if="!week.active_learners" class="stats" :style="{ color: $themeTokens.annotation }">
      {{ $tr('nobodyYet') }}
    </p>
    <KGrid v-else gutter="16" class="stats">
      <KGridItem :layout4="{ span: 2 }" :layout8="{ span: 4 }" :layout12="{ span: 6 }">
        <div class="stat">
          <TimeDuration :seconds="week.avg_seconds_logged_in" />
        </div>
        <div :style="{ color: $themeTokens.annotation }">
          {{ $tr('avgLoggedIn') }}
        </div>
      </KGridItem>
      <KGridItem :layout4="{ span: 2 }" :layout8="{ span: 4 }" :layout12="{ span: 6 }">
        <div class="stat">
          <TimeDuration :seconds="week.avg_seconds_watching" />
        </div>
        <div :style="{ color: $themeTokens.annotation }">
          {{ $tr('avgWatching') }}
        </div>
      </KGridItem>
    </KGrid>
  </Block>

</template>


<script>

  import TimeDuration from 'kolibri.coreVue.components.TimeDuration';
  import commonCoach from '../../common';
  import Block from './Block';

  const BAR_MAX_PX = 100;

  export default {
    name: 'ThisWeekBlock',
    components: {
      Block,
      TimeDuration,
    },
    mixins: [commonCoach],
    computed: {
      week() {
        return (
          this.$store.state.classSummary.weekAttendance || {
            days: [],
            avg_seconds_logged_in: 0,
            avg_seconds_watching: 0,
          }
        );
      },
      days() {
        const total = Math.max(this.learners.length, 1);
        return this.week.days.map(day => ({
          date: day.date,
          learners: day.learners,
          // Midday, so the weekday is right in any time zone.
          label: this.$formatDate(new Date(day.date + 'T12:00:00'), { weekday: 'short' }),
          height:
            day.learners === null
              ? '2px'
              : Math.max(Math.round((day.learners / total) * BAR_MAX_PX), 2) + 'px',
        }));
      },
      chartLabel() {
        const counts = this.days
          .filter(day => day.learners !== null)
          .map(day => `${day.label} ${day.learners}`)
          .join(', ');
        return this.$tr('chartLabel', { counts });
      },
    },
    $trs: {
      thisWeekLabel: {
        message: 'This week',
        context: "Title of the Class home block showing the class's attendance this week.",
      },
      description: {
        message: 'Learners who came each day, and the average time per learner.',
        context: "Description in the 'This week' block on the coach's Class home.",
      },
      chartLabel: {
        message: 'Learners who came each day this week: {counts}',
        context:
          "Screen-reader description of the bar chart in the 'This week' block; {counts} lists each day and its number of learners.",
      },
      nobodyYet: {
        message: 'No learner has come yet this week.',
        context: "Shown in the 'This week' block when no learner has signed in since Monday.",
      },
      avgLoggedIn: {
        message: 'average time logged in',
        context: "Label under the average time each learner was logged in this week.",
      },
      avgWatching: {
        message: 'average time watching',
        context: "Label under the average video watching time per learner this week.",
      },
    },
  };

</script>


<style lang="scss" scoped>

  .chart {
    display: flex;
    gap: 8px;
    align-items: flex-end;
    height: 130px;
    padding: 0 4px;
    border-bottom-style: solid;
    border-bottom-width: 1px;
  }

  .column {
    display: flex;
    flex: 1 1 0;
    flex-direction: column;
    gap: 4px;
    align-items: center;
    justify-content: flex-end;
    height: 100%;
  }

  .count {
    font-size: 12px;
  }

  .bar {
    width: 100%;
    max-width: 40px;
    border-radius: 4px 4px 0 0;
  }

  .labels {
    display: flex;
    gap: 8px;
    padding: 6px 4px 0;
    font-size: 12px;

    span {
      flex: 1 1 0;
      text-align: center;
    }
  }

  .stats {
    margin-top: 16px;
  }

  .stat {
    font-size: 20px;
    font-weight: bold;
  }

</style>
