<template>

  <!-- Learners who have not finished any item yet: the LSHE "reached"
       measure, from the class summary. "View all" opens the existing
       Reports overview, which lists every learner needing attention. -->
  <Block
    :allLinkText="coachString('viewAllAction')"
    :allLinkRoute="classRoute('ReportsClassOverviewPage')"
    :showAllLink="notReached.length > 0"
  >
    <template #title>
      <KLabeledIcon
        icon="person"
        :label="$tr('notReachedLabel', { count: notReached.length })"
      />
    </template>
    <p v-if="learners.length === 0">
      {{ coachString('learnerListEmptyState') }}
    </p>
    <p v-else-if="notReached.length === 0">
      {{ $tr('allReached') }}
    </p>
    <template v-else>
      <p :style="{ color: $themeTokens.annotation }">
        {{ $tr('description') }}
      </p>
      <BlockItem
        v-for="row in shown"
        :key="row.id"
      >
        <KRouterLink
          :text="row.name"
          :to="classRoute('ReportsLearnerReportPage', { learnerId: row.id })"
          icon="person"
        />
        <div class="last-activity" :style="{ color: $themeTokens.annotation }">
          <ElapsedTime v-if="row.lastActivity" :date="row.lastActivity" />
          <span v-else>{{ $tr('noActivity') }}</span>
        </div>
      </BlockItem>
    </template>
  </Block>

</template>


<script>

  import ElapsedTime from 'kolibri.coreVue.components.ElapsedTime';
  import commonCoach from '../../common';
  import Block from './Block';
  import BlockItem from './BlockItem';

  const MAX_LEARNERS = 5;

  export default {
    name: 'NotReachedBlock',
    components: {
      Block,
      BlockItem,
      ElapsedTime,
    },
    mixins: [commonCoach],
    computed: {
      notReached() {
        const reached = new Set(this.$store.state.classSummary.reachedLearnerIds);
        const lastActivity = {};
        for (const row of this.learnerOverview) {
          lastActivity[row.learner_id] = row.last_activity;
        }
        return this.learners
          .filter(learner => !reached.has(learner.id))
          .map(learner => ({
            id: learner.id,
            name: learner.name,
            lastActivity: lastActivity[learner.id] || null,
          }))
          .sort((a, b) => (b.lastActivity || 0) - (a.lastActivity || 0));
      },
      shown() {
        return this.notReached.slice(0, MAX_LEARNERS);
      },
    },
    $trs: {
      notReachedLabel: {
        message: 'Not yet reached ({count, number})',
        context:
          "Title of the Class home block listing learners who have not finished any resource yet. 'Reached' is the LSHE programme's measure of a learner who has finished at least one resource.",
      },
      description: {
        message: 'These learners have not finished a resource yet. Help them get started.',
        context: "Description in the 'Not yet reached' block on the coach's Class home.",
      },
      allReached: {
        message: 'Every learner in this class has finished at least one resource.',
        context: "Shown in the 'Not yet reached' block when no learner is left to reach.",
      },
      noActivity: {
        message: 'No activity yet',
        context:
          "Shown next to a learner in the 'Not yet reached' block when they have never used Kolibri.",
      },
    },
  };

</script>


<style lang="scss" scoped>

  .last-activity {
    margin-top: 4px;
    font-size: 14px;
  }

</style>
