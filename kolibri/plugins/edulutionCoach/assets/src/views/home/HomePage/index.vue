<template>
  <CoachAppBarPage
    :authorized="userIsAuthorized"
    authorizedRole="adminOrCoach"
    :showSubNav="true"
  >
    <KGrid gutter="16">
      <KGridItem>
        <OverviewBlock />
      </KGridItem>
      <KGridItem>
        <TodayBlock />
      </KGridItem>
      <KGridItem :layout12="{ span: 6 }">
        <KGrid gutter="16">
          <KGridItem>
            <LessonsBlock />
          </KGridItem>
          <KGridItem v-if="hasBandTopics">
            <TopicProgressBlock />
          </KGridItem>
          <!-- Only when the class has quizzes. -->
          <KGridItem v-if="exams.length > 0">
            <QuizzesBlock />
          </KGridItem>
        </KGrid>
      </KGridItem>
      <KGridItem :layout12="{ span: 6 }">
        <KGrid gutter="16">
          <KGridItem>
            <ThisWeekBlock />
          </KGridItem>
          <KGridItem>
            <NotReachedBlock />
          </KGridItem>
          <KGridItem>
            <ActivityBlock />
          </KGridItem>
          <!-- Hidden when assessments are turned off (LSHE): it would only
               ever be empty. -->
          <KGridItem v-if="assessmentsEnabled">
            <AssessmentBlock />
          </KGridItem>
        </KGrid>
      </KGridItem>
    </KGrid>
  </CoachAppBarPage>
</template>


<script>

  import CoachAppBarPage from '../../CoachAppBarPage';
  import commonCoach from '../../common';
  import assessmentsEnabled from '../../../assessmentsEnabled';
  import OverviewBlock from './OverviewBlock';
  import ActivityBlock from './ActivityBlock';
  import LessonsBlock from './LessonsBlock';
  import QuizzesBlock from './QuizzesBlock';
  import ThisWeekBlock from './ThisWeekBlock';
  import TodayBlock from './TodayBlock';
  import AssessmentBlock from './AssessmentBlock.vue';
  import NotReachedBlock from './NotReachedBlock';
  import TopicProgressBlock from './TopicProgressBlock';

  export default {
    name: 'HomePage',
    components: {
      CoachAppBarPage,
      OverviewBlock,
      ActivityBlock,
      LessonsBlock,
      QuizzesBlock,
      ThisWeekBlock,
      TodayBlock,
      AssessmentBlock,
      NotReachedBlock,
      TopicProgressBlock,
    },
    mixins: [commonCoach],
    data() {
      return { assessmentsEnabled };
    },
    computed: {
      hasBandTopics() {
        return this.$store.state.classSummary.bandTopics.length > 0;
      },
    },
  };

</script>

