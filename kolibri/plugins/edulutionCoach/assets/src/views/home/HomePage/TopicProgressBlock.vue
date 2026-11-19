<template>

  <!-- The class's grade band topics in channel order, with the same
       progress bar and wording as the lessons block, so a coach sees what
       has been taught and what to teach next. -->
  <Block
    :allLinkText="coachString('viewAllAction')"
    :allLinkRoute="classRoute('HomePage')"
    :showAllLink="false"
  >
    <template #title>
      <KLabeledIcon icon="topic" :label="$tr('topicProgressLabel')" />
    </template>
    <p :style="{ color: $themeTokens.annotation }">
      {{ $tr('description') }}
    </p>
    <BlockItem
      v-for="topic in shown"
      :key="topic.id"
    >
      <KFixedGrid numCols="4">
        <KFixedGridItem span="2">
          <h3 class="title">
            {{ topic.title }}
          </h3>
        </KFixedGridItem>
        <KFixedGridItem span="2" alignment="right">
          <span v-if="topic.inActiveLesson || topic.isNext" class="tag">
            <KIcon
              :icon="topic.inActiveLesson ? 'lesson' : 'forward'"
              :color="$themeTokens.primary"
              class="tag-icon"
            />
            {{ topic.inActiveLesson ? $tr('inLessonLabel') : $tr('nextLabel') }}
          </span>
        </KFixedGridItem>
        <KFixedGridItem>
          <ProgressSummaryBar :tally="topic.tally" class="dashboard-bar" />
        </KFixedGridItem>
        <KFixedGridItem>
          <StatusSummary :tally="topic.tally" />
        </KFixedGridItem>
      </KFixedGrid>
    </BlockItem>
    <BlockItem v-if="table.length > maxTopics">
      <KButton
        appearance="basic-link"
        :text="showAll ? $tr('showFewer') : $tr('showAll', { count: table.length })"
        @click="showAll = !showAll"
      />
    </BlockItem>
  </Block>

</template>


<script>

  import commonCoach from '../../common';
  import ProgressSummaryBar from '../../common/status/ProgressSummaryBar';
  import Block from './Block';
  import BlockItem from './BlockItem';

  export default {
    name: 'TopicProgressBlock',
    components: {
      Block,
      BlockItem,
      ProgressSummaryBar,
    },
    mixins: [commonCoach],
    data() {
      // Five topics fit without pushing the other blocks far down on a
      // tablet, where the blocks stack in one column.
      return { showAll: false, maxTopics: 5 };
    },
    computed: {
      shown() {
        return this.showAll ? this.table : this.table.slice(0, this.maxTopics);
      },
      table() {
        const topics = this.$store.state.classSummary.bandTopics;
        // The first topic, in channel order, that no active lesson covers
        // and some learner has not finished: what to teach next.
        const next = topics.find(
          topic => !topic.in_active_lesson && topic.completed < this.learners.length
        );
        return topics.map(topic => ({
          id: topic.id,
          title: topic.title,
          inActiveLesson: topic.in_active_lesson,
          isNext: Boolean(next) && next.id === topic.id,
          tally: {
            completed: topic.completed,
            started: topic.started,
            notStarted: topic.not_started,
            helpNeeded: 0,
          },
        }));
      },
    },
    $trs: {
      topicProgressLabel: {
        message: 'Topic progress',
        context:
          "Title of the Class home block showing the topics of the class's grade band and how many learners finished each.",
      },
      description: {
        message: "Your class's topics in order. A learner has completed a topic when they have finished all its resources.",
        context: "Description in the 'Topic progress' block on the coach's Class home.",
      },
      inLessonLabel: {
        message: 'In a lesson',
        context:
          "Label next to a topic in the 'Topic progress' block when one of its resources is in a lesson learners can see.",
      },
      showAll: {
        message: 'Show all {count, number} topics',
        context: "Button in the 'Topic progress' block that shows every topic of the band.",
      },
      showFewer: {
        message: 'Show fewer topics',
        context: "Button in the 'Topic progress' block that goes back to the first five topics.",
      },
      nextLabel: {
        message: 'Next to teach',
        context:
          "Label next to the first topic in the 'Topic progress' block that is not yet in a lesson and not finished by every learner.",
      },
    },
  };

</script>


<style lang="scss" scoped>

  .title {
    margin-bottom: 8px;
  }

  .tag {
    font-size: 14px;
    white-space: nowrap;
  }

  .tag-icon {
    position: relative;
    top: 3px;
    margin-right: 4px;
  }

  .dashboard-bar {
    margin-bottom: 8px;
  }

</style>
