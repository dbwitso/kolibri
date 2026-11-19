<template>

  <!-- The lesson the class is on now (the newest lesson learners can see)
       and who is signed in, with the two things a coach does next. -->
  <Block
    :allLinkText="coachString('viewAllAction')"
    :allLinkRoute="classRoute('ReportsLessonListPage', {})"
    :showAllLink="false"
  >
    <template #title>
      <KLabeledIcon icon="lesson" :label="$tr('todayLabel')" />
    </template>
    <KGrid gutter="16">
      <KGridItem :layout12="{ span: 7 }" :layout8="{ span: 8 }">
        <template v-if="current">
          <div class="annotation" :style="{ color: $themeTokens.annotation }">
            {{ $tr('currentLessonLabel') }}
          </div>
          <h3 class="lesson-title">
            {{ current.title }}
          </h3>
          <div class="details" :style="{ color: $themeTokens.annotation }">
            <span>{{ $tr('resourcesCount', { count: current.resourceCount }) }}</span>
            <span aria-hidden="true"> · </span>
            <Recipients
              :groupNames="current.groupNames"
              :hasAssignments="current.hasAssignments"
            />
          </div>
        </template>
        <p v-else>
          {{ $tr('noVisibleLesson') }}
        </p>
      </KGridItem>
      <KGridItem :layout12="{ span: 2 }" :layout8="{ span: 3 }">
        <div class="live">
          <span class="live-count">{{ $formatNumber(activeCount) }}</span>
          <span :style="{ color: $themeTokens.annotation }">
            {{ $tr('ofLearners', { total: learners.length }) }}
          </span>
        </div>
        <div class="annotation" :style="{ color: $themeTokens.annotation }">
          {{ $tr('onNowLabel') }}
        </div>
      </KGridItem>
      <KGridItem
        :layout12="{ span: 3, alignment: 'right' }"
        :layout8="{ span: 5 }"
      >
        <div class="actions">
          <KRouterLink
            v-if="current"
            appearance="raised-button"
            :primary="true"
            :text="$tr('openLessonAction')"
            :to="classRoute(LessonsPageNames.SUMMARY, { lessonId: current.id })"
          />
          <KRouterLink
            appearance="flat-button"
            :text="$tr('newLessonAction')"
            :to="classRoute(LessonsPageNames.LESSON_CREATION_ROOT, {})"
          />
        </div>
      </KGridItem>
    </KGrid>
  </Block>

</template>


<script>

  import commonCoach from '../../common';
  import { LessonsPageNames } from '../../../constants/lessonsConstants';
  import Recipients from '../../common/Recipients';
  import Block from './Block';

  export default {
    name: 'TodayBlock',
    components: {
      Block,
      Recipients,
    },
    mixins: [commonCoach],
    data() {
      return { LessonsPageNames };
    },
    computed: {
      current() {
        const visible = this.lessons.filter(lesson => lesson.is_active);
        if (visible.length === 0) {
          return null;
        }
        const lesson = visible.reduce((newest, l) =>
          l.date_created > newest.date_created ? l : newest
        );
        return {
          id: lesson.id,
          title: lesson.title,
          resourceCount: (lesson.node_ids || []).length,
          groupNames: lesson.groups.map(id => (this.groupMap[id] || {}).name).filter(Boolean),
          hasAssignments: this.getLearnersForLesson(lesson).length > 0,
        };
      },
      activeCount() {
        return (this.activeLearners || []).length;
      },
    },
    $trs: {
      todayLabel: {
        message: 'Today',
        context:
          "Title of the top block on the coach's Class home: the class's current lesson and who is signed in.",
      },
      currentLessonLabel: {
        message: 'Current lesson',
        context: "Label above the name of the newest lesson learners can see, in the 'Today' block.",
      },
      resourcesCount: {
        message: '{count, number} {count, plural, one {resource} other {resources}}',
        context: "Number of resources in the current lesson, in the 'Today' block.",
      },
      noVisibleLesson: {
        message: 'No lesson is visible to learners yet. Create one, or make a lesson visible.',
        context:
          "Shown in the 'Today' block when the class has no lesson that learners can see.",
      },
      ofLearners: {
        message: 'of {total, number}',
        context: "Follows the number of learners signed in now, e.g. '17 of 28', in the 'Today' block.",
      },
      onNowLabel: {
        message: 'learners on now',
        context: "Label under the number of learners signed in now, in the 'Today' block.",
      },
      openLessonAction: {
        message: 'Open lesson',
        context: "Button in the 'Today' block that opens the current lesson.",
      },
      newLessonAction: {
        message: 'New lesson',
        context: "Button in the 'Today' block that starts creating a lesson.",
      },
    },
  };

</script>


<style lang="scss" scoped>

  .annotation {
    font-size: 14px;
  }

  .lesson-title {
    margin: 4px 0;
    font-size: 20px;
  }

  .details {
    font-size: 14px;
  }

  .live-count {
    margin-right: 4px;
    font-size: 32px;
    font-weight: bold;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: flex-end;
  }

</style>
