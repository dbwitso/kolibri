<template>

  <!-- The class's grade band topics on the Class home (the list itself is
       shared with the Monthly reports page). -->
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
    <!-- Five topics fit without pushing the other blocks far down on a
         tablet, where the blocks stack in one column. -->
    <TopicProgressList
      :topics="$store.state.classSummary.bandTopics"
      :learnerCount="learners.length"
      :max="5"
    />
  </Block>

</template>


<script>

  import commonCoach from '../../common';
  import TopicProgressList from '../../common/TopicProgressList';
  import Block from './Block';

  export default {
    name: 'TopicProgressBlock',
    components: {
      Block,
      TopicProgressList,
    },
    mixins: [commonCoach],
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
    },
  };

</script>
