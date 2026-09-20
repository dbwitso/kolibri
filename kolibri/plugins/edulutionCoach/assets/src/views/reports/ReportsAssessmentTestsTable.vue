<template>

  <CoreTable :emptyMessage="$tr('emptyMessage')">
    <template #headers>
      <th>{{ $tr('titleLabel') }}</th>
      <th style="width: 120px">
        {{ $tr('scoreLabel') }}
      </th>
      <th>
        {{ $tr('weightageLabel') }}
      </th>
      <th 
        :style="{
          display: 'flex',
          justifyContent: 'center'
        }"
      >
        {{ $tr('actionLabel') }}
      </th>
    </template>
    <template #tbody>
      <transition-group tag="tbody" name="list">
        <tr v-for="tableRow in entries" :key="tableRow.id">
          <td>
            {{ tableRow.title }}
          </td>
          <td>
            <span
              class="score-chip"
              :style="{
                backgroundColor: scoreColor(calcPercentage(tableRow.score, tableRow.question_count), tableRow.attempt_count),
                color: 'white',
              }"
            >
              {{
                $formatNumber(
                  calcPercentage(tableRow.score, tableRow.question_count),
                  { style: 'percent' }
                )
              }}
            </span>
          </td>
          <td :style="{ textAlign: 'center' }">
            {{ tableRow.currentQuestionCount }}
          </td>
          <td
            :style="{
              display: 'flex',
              flexWrap: 'nowrap',
              gap: '4px'
            }"
          >
            <KButton
              :text="$tr('viewDetailsLabel')"
              appearance="flat-button"
              :disabled="tableRow.attempt_count < 1"
              @click="onViewDetailsClick(tableRow)"
            />
            <KButton
              :text="$tr('viewBreakdownLabel')"
              appearance="flat-button"
              @click="onTestTitleClick(tableRow)"
            />
            <KButton
              :text="$tr('viewPastLabel')"
              appearance="flat-button"
              :disabled="!isPastEnabled(tableRow.type, tableRow.attempt_count, tableRow.archive)"
              @click="onviewAttemptsClick(tableRow.id)"
            />
          </td>
        </tr>
      </transition-group>
    </template>
  </CoreTable>
  
</template>
  
  
  <script>
    import commonCoreStrings from 'kolibri.coreVue.mixins.commonCoreStrings';
    import commonCoach from '../common';
  
    export default {
      name: 'ReportsAssessmentTestsTable',
      mixins: [commonCoach, commonCoreStrings],
      props: {
        entries: {
          type: Array,
          default: () => [],
        },
      },
      computed: {
      },
      methods: {
        calcPercentage(score, total) {
          return (score / total);
        },
        scoreColor(value, count) {
          if (value <= 0 && count === 0) {
            return '#D9D9D9';
          }
          if (value <= 0 && count !== 0) {
            return '#FF412A';
          }
          if (value > 0 && value <= 0.25) {
            return '#FF412A';
          }
          if (value > 0.25 && value <= 0.50) {
            return '#EC9090';
          }
          if (value > 0.50 && value <= 0.69) {
            return '#F5C216';
          }
          if (value > 0.69 && value <= 0.74) {
            return '#99CC33';
          }
          if (value <= 1) {
            return '#00B050';
          }
        },
        onTestTitleClick(tableRow) {
          this.$emit('testTitleClick', tableRow.id);
        },
        onviewAttemptsClick(id){
          this.$emit('viewAttemptsClick', id);
        },
        isPastEnabled(type,count,isArchive){
          if ((type === 'SECTION' || type === 'POST') && (count > 1 || isArchive)) {
            return true
          }
          return false
        },
        onViewDetailsClick(tableRow) {
          this.$router.push(tableRow.link)
        }
      },
      $trs: {
        titleLabel: {
          message: 'Test',
          context: '',
        },
        scoreLabel: {
          message: 'Score',
          context: '',
        },
        emptyMessage: {
          message: 'Test list is empty',
          context: '',
        },
        actionLabel :{
          message: 'Action',
          context: '',
        },
        weightageLabel:{
          message: 'Weightage',
          context: '',
        },
        viewDetailsLabel: {
          message: 'View Details',
          context: '',
        },
        viewBreakdownLabel: {
          message: 'View Breakdown',
          context: '',
        },
        viewPastLabel: {
          message: 'View Past',
          context: '',
        },
      },
    };
  
  </script>
  
  
  <style lang="scss" scoped>
  
    @import '../common/print-table';
  
    .small-answered-count {
      display: block;
      margin-left: 1.75rem; /* matches KLabeledIcon */
      font-size: small;
    }

    .score-chip {
      display: inline-flex;
      padding: 4px 8px;
      align-items: center;
      justify-content: center;
      border-radius: 50px;
      min-width: 100px;
    }

  </style>
  