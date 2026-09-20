<template>

  <div v-show="!$isPrint" :style="{ backgroundColor: $themeTokens.appBar }">

    <SkipNavigationLink />

    <UiToolbar
      :title="title"
      type="clear"
      textColor="white"
      class="app-bar"
      :style="{ height: topBarHeight + 'px' }"
      :raised="false"
      :removeBrandDivider="true"
    >
      <template #icon>
        <KIconButton
          icon="menu"
          :color="$themeTokens.textInverted"
          :ariaLabel="$tr('openNav')"
          @click="$emit('toggleSideNav')"
        />
      </template>

      <template #brand>
        <img
          v-if="themeConfig.appBar.topLogo"
          :src="themeConfig.appBar.topLogo.src"
          :alt="themeConfig.appBar.topLogo.alt"
          :style="themeConfig.appBar.topLogo.style"
          class="brand-logo"
        >
      </template>

      <template #actions>
        <div>
          <slot name="app-bar-actions"></slot>
          <div class="total-points">
            <slot name="totalPointsMenuItem"></slot>
          </div>

          <span v-if="isUserLoggedIn" class="user-info">
            <KIcon
              icon="person"
              :style="{ fill: $themeTokens.textInverted, height: '24px', width: '24px', top: 0, }"
            />
            <span class="username" tabindex="-1">{{ fullName }}</span>
          </span>

        </div>
      </template>
    </UiToolbar>
    <div class="subpage-nav">
      <slot name="sub-nav"></slot>
    </div>
  </div>

</template>


<script>

  import { mapGetters, mapState } from 'vuex';
  import commonCoreStrings from 'kolibri.coreVue.mixins.commonCoreStrings';
  import UiToolbar from 'kolibri.coreVue.components.UiToolbar';
  import KIconButton from 'kolibri-design-system/lib/buttons-and-links/KIconButton';
  import themeConfig from 'kolibri.themeConfig';
  import navComponentsMixin from '../mixins/nav-components';
  import SkipNavigationLink from './SkipNavigationLink';

  export default {
    name: 'AppBar',
    components: {
      UiToolbar,
      KIconButton,
      SkipNavigationLink,
    },
    mixins: [commonCoreStrings, navComponentsMixin],
    setup() {
      return { themeConfig };
    },
    props: {
      title: {
        type: String,
        required: true,
      }
    },
    computed: {
      ...mapGetters(['isUserLoggedIn']),
      ...mapState({
        fullName: state => state.core.session.full_name,
      }),
    },
    $trs: {
      openNav: {
        message: 'Open site navigation',
        context:
          "This message is providing additional context to the screen-reader users, but is not visible in the Kolibri UI.\n\nIn this case the screen-reader will announce the message when user navigates to the 'hamburger' button with the keyboard, to indicate that it allows them to open the sidebar navigation menu.",
      },
    },
  };

</script>


<style lang="scss" scoped>

  @import '~kolibri-design-system/lib/styles/definitions';

  .user-info {
    display: inline-flex;
    align-items: center;
    vertical-align: middle;
  }

  .username {
    display: inline-block;
    max-width: 200px;
    margin-left: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: middle;
  }

  @media (max-width: 750px) {
    .username {
      max-width: 50px;
    }
  }

  .total-points {
    display: inline-block;
    margin-left: 16px;
  }

  /deep/ .ui-toolbar__brand {
    min-width: inherit;
  }

  /deep/ .ui-toolbar__title {
    margin-right: 10px;
  }

  .brand-logo {
    max-width: 48px;
    max-height: 48px;
    margin-right: 8px;
    vertical-align: middle;
  }

</style>