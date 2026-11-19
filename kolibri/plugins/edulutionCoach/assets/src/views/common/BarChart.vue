<template>

  <!-- A plain bar chart in the theme's colours: the Class home's This week
       and the Monthly reports page. No library, so it works offline and
       loads with the page. -->
  <figure class="bar-chart">
    <div
      class="bars"
      role="img"
      :aria-label="ariaLabel"
      :style="{ height: height + 'px', borderBottomColor: $themeTokens.fineLine }"
    >
      <div
        v-for="bar in shaped"
        :key="bar.key"
        class="column"
        :title="bar.title"
      >
        <span v-if="showValues" class="value">{{ bar.text }}</span>
        <div
          class="bar"
          :style="{
            height: bar.px,
            maxWidth: maxBarWidth + 'px',
            backgroundColor: bar.value === null ? $themeTokens.fineLine : barColor,
          }"
        ></div>
      </div>
    </div>
    <div class="labels" aria-hidden="true">
      <span
        v-for="bar in shaped"
        :key="bar.key"
        :style="{ color: $themeTokens.annotation }"
      >{{ bar.label }}</span>
    </div>
  </figure>

</template>


<script>

  export default {
    name: 'BarChart',
    props: {
      // [{ key, label, value (null: not yet), text?, title? }]
      bars: {
        type: Array,
        required: true,
      },
      // The value of a full-height bar; defaults to the largest value.
      max: {
        type: Number,
        default: null,
      },
      ariaLabel: {
        type: String,
        required: true,
      },
      height: {
        type: Number,
        default: 130,
      },
      color: {
        type: String,
        default: null,
      },
      showValues: {
        type: Boolean,
        default: true,
      },
      maxBarWidth: {
        type: Number,
        default: 40,
      },
    },
    computed: {
      barColor() {
        return this.color || this.$themeTokens.primary;
      },
      shaped() {
        const top =
          this.max || Math.max(1, ...this.bars.map(bar => (bar.value === null ? 0 : bar.value)));
        const room = this.height - (this.showValues ? 22 : 4);
        return this.bars.map(bar => ({
          ...bar,
          text: bar.value === null ? '' : bar.text || this.$formatNumber(bar.value),
          px:
            bar.value === null
              ? '2px'
              : Math.max(Math.round((bar.value / top) * room), bar.value ? 3 : 2) + 'px',
        }));
      },
    },
  };

</script>


<style lang="scss" scoped>

  .bar-chart {
    margin: 0;
  }

  .bars {
    display: flex;
    gap: 4px;
    align-items: flex-end;
    padding: 0 2px;
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
    min-width: 0;
    height: 100%;
  }

  .value {
    font-size: 11px;
    white-space: nowrap;
  }

  .bar {
    width: 100%;
    border-radius: 3px 3px 0 0;
  }

  .labels {
    display: flex;
    gap: 4px;
    padding: 6px 2px 0;
    font-size: 11px;

    span {
      flex: 1 1 0;
      min-width: 0;
      overflow: hidden;
      text-align: center;
      white-space: nowrap;
    }
  }

</style>
