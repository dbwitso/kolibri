<template>

  <!-- A class's grade band topics in channel order, with the same progress
       bar and wording as lessons: which are in a lesson, which to teach
       next. Used by the Class home and the Monthly reports page. -->
  <div>
    <div
      v-for="topic in shown"
      :key="topic.id"
      class="topic"
      :style="{ borderBottomColor: $themeTokens.fineLine }"
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
    </div>
    <div v-if="max && table.length > max" class="topic">
      <KButton
        appearance="basic-link"
        :text="showAll ? $tr('showFewer') : $tr('showAll', { count: table.length })"
        @click="showAll = !showAll"
      />
    </div>
  </div>

</template>


<script>

  import commonCoach from '../common';
  import ProgressSummaryBar from './status/ProgressSummaryBar';

  export default {
    name: 'TopicProgressList',
    components: { ProgressSummaryBar },
    mixins: [commonCoach],
    props: {
      // As class_summary_api.get_band_topic_progress returns them.
      topics: {
        type: Array,
        required: true,
      },
      learnerCount: {
        type: Number,
        required: true,
      },
      // Show this many, with a button for the rest; null shows all.
      max: {
        type: Number,
        default: null,
      },
    },
    data() {
      return { showAll: false };
    },
    computed: {
      shown() {
        return this.showAll || !this.max ? this.table : this.table.slice(0, this.max);
      },
      table() {
        // The first topic, in channel order, that no active lesson covers
        // and some learner has not finished: what to teach next.
        const next = this.topics.find(
          topic => !topic.in_active_lesson && topic.completed < this.learnerCount
        );
        return this.topics.map(topic => ({
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
      inLessonLabel: {
        message: 'In a lesson',
        context:
          'Label next to a topic in the topic progress list when one of its resources is in a lesson learners can see.',
      },
      nextLabel: {
        message: 'Next to teach',
        context:
          'Label next to the first topic in the topic progress list that is not yet in a lesson and not finished by every learner.',
      },
      showAll: {
        message: 'Show all {count, number} topics',
        context: 'Button in the topic progress list that shows every topic of the band.',
      },
      showFewer: {
        message: 'Show fewer topics',
        context: 'Button in the topic progress list that goes back to the first few topics.',
      },
    },
  };

</script>


<style lang="scss" scoped>

  .topic {
    padding: 12px 0;

    &:not(:last-child) {
      border-bottom-style: solid;
      border-bottom-width: 1px;
    }
  }

  .title {
    margin: 0 0 8px;
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
