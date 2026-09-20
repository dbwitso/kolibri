<template>
  <div :class="progressClassName">
    <KLabeledIcon nowrap>
      <template #icon>
        <CoachStatusIcon ref="status" :icon="icon" />
      </template>
      {{ text }}
    </KLabeledIcon>
    <KTooltip
      v-if="false"
      reference="status"
      placement="top"
      :refs="$refs"
    >
      {{ tooltip }}
    </KTooltip>
  </div>

</template>


  <script>
    import CoachStatusIcon from './CoachStatusIcon';
    import { statusStringsMixin, isValidVerb } from './statusStrings';

    export default {
      name: 'ActiveLearnerCount',
      components: {
        CoachStatusIcon,
      },
      mixins: [statusStringsMixin],
      props: {
        verb: {
          type: String,
          required: true,
          validator: isValidVerb,
        },
        icon: {
          type: String,
          required: true,
        },
      },
      computed: {
        strings() {
          return this.activeLearnersTranslators[this.verb];
        },
        // Unlike ActiveLearnersRatio, there's no total to fall back to at the
        // lowest verbosity, so 'count'/'countShort' cover every verbosity level.
        text() {
          return this.strings.$tr(this.shorten('count', this.verbosityNumber), {
            count: this.count,
          });
        },
        tooltip() {
          return this.strings.$tr('count', {
            count: this.count,
          });
        },
        // 'count' holds whichever tally this instance is displaying (active
        // or notActive), but "full attendance" always means active === total,
        // regardless of which one is shown here - so normalize back to the
        // active count before deciding the color.
        activeCount() {
          return this.verb === 'notActive' ? this.total - this.count : this.count;
        },
        progressClassName() {
          if (this.activeCount === this.total) {
            return 'progress-completed'
          }
          if (this.activeCount < this.total) {
            return 'progress-inprogress'
          }
          return 'progress-default'
        }
      },
    };

  </script>


  <style lang="scss" scoped>
  .progress-inprogress svg {
    fill: orange !important;
  }
  .progress-completed svg {
    fill: green !important;
  }
  .progress-default svg {
    fill: #071d49 !important
  }
</style>
