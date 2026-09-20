<template>

  <CoachAppBarPage
    :authorized="userIsAuthorized"
    authorizedRole="adminOrCoach"
    :showSubNav="true"
  >

    <KPageContainer>
      <ReportsHeader
        :activeTabId="ReportsTabs.OVERVIEW"
        :title="$isPrint ? $tr('printLabel', { className }) : null"
      />
      <KTabsPanel
        :tabsId="REPORTS_TABS_ID"
        :activeTabId="ReportsTabs.OVERVIEW"
      >
        <p v-show="!$isPrint" class="description">
          {{ $tr('description') }}
        </p>
        <ReportsControls @export="exportCSV" />
        <CoreTable :emptyMessage="coachString('learnerListEmptyState')">
          <template #headers>
            <th>{{ coachString('nameLabel') }}</th>
            <th>{{ coachString('helpNeededLabel') }}</th>
            <th>{{ $tr('lockedResourcesLabel') }}</th>
            <th>{{ $tr('activeNowLabel') }}</th>
            <th>{{ coachString('lastActivityLabel') }}</th>
          </template>
          <template #tbody>
            <transition-group
              tag="tbody"
              name="list"
            >
              <tr
                v-for="tableRow in table"
                :key="tableRow.learner_id"
                :class="{ 'needs-attention': tableRow.needsAttention }"
              >
                <td>
                  <KRouterLink
                    :text="tableRow.name"
                    :to="classRoute('ReportsLearnerReportPage', { learnerId: tableRow.learner_id })"
                    icon="person"
                  />
                </td>
                <td>
                  <KLabeledIcon v-if="tableRow.help_needed_count">
                    <template #icon>
                      <KIcon :color="$themeTokens.incorrect" icon="help" />
                    </template>
                    {{ $formatNumber(tableRow.help_needed_count) }}
                  </KLabeledIcon>
                  <KEmptyPlaceholder v-else />
                </td>
                <td>
                  <KLabeledIcon v-if="tableRow.locked_resources_count">
                    <template #icon>
                      <KIcon :color="$themePalette.orange.v_600" icon="warning" />
                    </template>
                    {{ $formatNumber(tableRow.locked_resources_count) }}
                  </KLabeledIcon>
                  <KEmptyPlaceholder v-else />
                </td>
                <td>
                  <KIcon
                    v-if="tableRow.currently_active"
                    :color="$themeTokens.mastered"
                    icon="inProgress"
                  />
                  <KEmptyPlaceholder v-else />
                </td>
                <td>
                  <ElapsedTime :date="tableRow.last_activity" />
                </td>
              </tr>
            </transition-group>
          </template>
        </CoreTable>
      </KTabsPanel>
    </KPageContainer>
  </CoachAppBarPage>

</template>


<script>

  import ElapsedTime from 'kolibri.coreVue.components.ElapsedTime';
  import commonCoach from '../common';
  import { REPORTS_TABS_ID, ReportsTabs } from '../../constants/tabsConstants';
  import CoachAppBarPage from '../CoachAppBarPage';
  import CSVExporter from '../../csv/exporter';
  import * as csvFields from '../../csv/fields';
  import ReportsControls from './ReportsControls';
  import ReportsHeader from './ReportsHeader';

  export default {
    name: 'ReportsClassOverviewPage',
    components: {
      CoachAppBarPage,
      ReportsControls,
      ReportsHeader,
      ElapsedTime,
    },
    mixins: [commonCoach],
    data() {
      return {
        REPORTS_TABS_ID,
        ReportsTabs,
      };
    },
    computed: {
      // learnerOverview is already sorted by the API/getter with the
      // learners most likely to need attention first - see
      // class_summary_api.get_learner_overview.
      table() {
        return this.learnerOverview.map(row => ({
          ...row,
          needsAttention: Boolean(row.help_needed_count || row.locked_resources_count),
        }));
      },
    },
    methods: {
      exportCSV() {
        const columns = [
          ...csvFields.name(),
          {
            name: this.coachString('helpNeededLabel'),
            key: 'help_needed_count',
          },
          {
            name: this.$tr('lockedResourcesLabel'),
            key: 'locked_resources_count',
          },
          {
            name: this.$tr('activeNowLabel'),
            key: 'currently_active',
          },
          {
            name: this.coachString('lastActivityLabel'),
            key: 'last_activity',
            format: row => (row.last_activity ? row.last_activity.toISOString() : ''),
          },
        ];

        const fileName = this.$tr('printLabel', { className: this.className });
        new CSVExporter(columns, fileName).export(this.table);
      },
    },
    $trs: {
      printLabel: {
        message: '{className} Overview',
        context:
          "Title that displays on a printed copy of the 'Reports' > 'Overview' page. This shows if the user uses the 'Print' option by clicking on the printer icon.",
      },
      description: {
        message: "Learners most likely to need your attention are listed first",
        context: "Description for the 'Reports' > 'Overview' tab.",
      },
      lockedResourcesLabel: {
        message: 'Locked resources',
        context:
          "Column header showing how many resources are currently locked for a learner because they completed them (see the lesson resource lock feature) and a coach has not yet unlocked them again.",
      },
      activeNowLabel: {
        message: 'Active now',
        context: "Column header indicating whether a learner is currently online in Kolibri.",
      },
    },
  };

</script>


<style lang="scss" scoped>

  @import '../common/print-table';

  .description {
    margin-top: 0;
  }

  .needs-attention td:first-child {
    box-shadow: inset 3px 0 0 currentColor;
  }

</style>
