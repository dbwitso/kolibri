<template>

  <div class="fh">
    <div class="wrapper-table">
      <div class="main-row table-row" :style="backgroundImageStyle">
        <div class="main-cell table-cell">
          <!-- remote access disabled -->
          <div
            v-if="!$store.getters.allowAccess"
            class="box"
            :style="{ backgroundColor: $themePalette.grey.v_100 }"
          >
            <CoreLogo
              v-if="themeConfig.signIn.topLogo"
              class="logo"
              :src="themeConfig.signIn.topLogo.src"
              :alt="themeConfig.signIn.topLogo.alt"
              :style="themeConfig.signIn.topLogo.style"
            />
            <h1
              v-if="themeConfig.signIn.showTitle"
              class="kolibri-title"
              :style="[ { color: $themeBrand.primary.v_300 }, themeConfig.signIn.titleStyle]"
            >
              {{ logoText }}
            </h1>
            <p data-test="restrictedAccess">
              {{ $tr('restrictedAccess') }}
            </p>
            <p>{{ $tr('restrictedAccessDescription') }}</p>
          </div>
          <!-- remote access enabled -->
          <div v-else class="box" :style="{ backgroundColor: $themePalette.grey.v_100 }">
            <CoreLogo
              v-if="themeConfig.signIn.topLogo"
              class="logo"
              :src="themeConfig.signIn.topLogo.src"
              :alt="themeConfig.signIn.topLogo.alt"
              :style="themeConfig.signIn.topLogo.style"
            />
            <p
              v-if="themeConfig.signIn.showPoweredBy"
              :style="themeConfig.signIn.poweredByStyle"
              class="small-text"
            >
              <KButton
                v-if="oidcProviderFlow"
                :text="$tr('poweredByKolibri')"
                appearance="basic-link"
                @click="whatsThisModalVisible = true"
              />
              <KExternalLink
                v-else
                :text="$tr('poweredByKolibri')"
                :primary="true"
                href="https://learningequality.org/r/powered_by_kolibri"
                :openInNewTab="true"
                appearance="basic-link"
              />
            </p>

            <slot></slot>

            <p v-if="!hideCreateAccount && canSignUp" class="create">
              <KRouterLink
                :text="userString('createAccountAction')"
                :to="signUpPage"
                :primary="false"
                appearance="raised-button"
                :disabled="busy"
                style="width: 100%;"
                data-test="createUser"
              />
            </p>

            <div>
              <component :is="component" v-for="component in loginOptions" :key="component.name" />
            </div>
          </div>
        </div>
      </div>
      <div class="table-row">
        <div class="footer-cell table-cell" :style="{ backgroundColor: $themeTokens.surface }">
          <div class="small-text">
            <span class="version-string">
              {{ versionMsg }}
            </span>
            <CoreLogo
              v-if="themeConfig.signIn.showKolibriFooterLogo"
              class="footer-logo"
              :src="themeConfig.signIn.footerLogo && themeConfig.signIn.footerLogo.src"
              :alt="themeConfig.signIn.footerLogo && themeConfig.signIn.footerLogo.alt"
            />
            <span v-else> • </span>
            <KButton
              :text="coreString('usageAndPrivacyLabel')"
              appearance="basic-link"
              @click="privacyModalVisible = true"
            />
            <template v-if="themeConfig.signIn.backgroundImgCredit">
              <span> • </span>
              {{ $tr('photoCreditLabel', {
                photoCredit: themeConfig.signIn.backgroundImgCredit
              }) }}
            </template>
          </div>
        </div>
      </div>
    </div>

    <PrivacyInfoModal
      v-if="privacyModalVisible"
      @submit="privacyModalVisible = false"
      @cancel="privacyModalVisible = false"
    />

    <KModal
      v-if="whatsThisModalVisible"
      :title="$tr('whatsThis')"
      :submitText="coreString('closeAction')"
      @submit="whatsThisModalVisible = false"
      @cancel="whatsThisModalVisible = false"
    >
      <p>{{ $tr('oidcGenericExplanation') }}</p>
      <p>
        <KExternalLink
          text="https://learningequality.org/kolibri"
          :primary="true"
          href="https://learningequality.org/r/powered_by_kolibri"
          :openInNewTab="true"
          appearance="basic-link"
        />
      </p>
    </KModal>
  </div>

</template>


<script>

  import { mapGetters } from 'vuex';
  import CoreLogo from 'kolibri.coreVue.components.CoreLogo';
  import PrivacyInfoModal from 'kolibri.coreVue.components.PrivacyInfoModal';
  import commonCoreStrings from 'kolibri.coreVue.mixins.commonCoreStrings';
  import useUser from 'kolibri.coreVue.composables.useUser';
  import themeConfig from 'kolibri.themeConfig';
  import loginComponents from 'kolibri.utils.loginComponents';
  import { ComponentMap } from '../constants';
  import commonUserStrings from './commonUserStrings';
  import getUrlParameter from './getUrlParameter';
  import plugin_data from 'plugin_data';

  export default {
    name: 'AuthBase',
    components: { CoreLogo, PrivacyInfoModal },
    mixins: [commonCoreStrings, commonUserStrings],
    setup() {
      const { isLearnerOnlyImport } = useUser();
      return { isLearnerOnlyImport, themeConfig };
    },
    props: {
      hideCreateAccount: {
        type: Boolean,
        required: false,
        default: false,
      },
      busy: {
        type: Boolean,
        required: false,
        default: false,
      },
    },
    data() {
      return {
        privacyModalVisible: false,
        whatsThisModalVisible: false,
      };
    },
    computed: {
      ...mapGetters(['facilityConfig']),
      backgroundImageStyle() {
        if (this.themeConfig.signIn.background) {
          const scrimOpacity =
            this.themeConfig.signIn.scrimOpacity !== undefined
              ? this.themeConfig.signIn.scrimOpacity
              : 0.7;
          return {
            backgroundColor: this.$themeTokens.primary,
            backgroundImage: `linear-gradient(rgba(0, 0, 0, ${scrimOpacity}), rgba(0, 0, 0, ${scrimOpacity})), url(${this.themeConfig.signIn.background})`,
          };
        }
        return { backgroundColor: this.$themeBrand.primary.v_900 };
      },
      canSignUp() {
        return !this.isLearnerOnlyImport && this.facilityConfig.learner_can_sign_up;
      },
      nextParam() {
        // query is after hash
        if (this.$route.query.next) {
          return this.$route.query.next;
        }
        // query is before hash
        return getUrlParameter('next');
      },
      signUpPage() {
        const signUpRoute = this.$router.getRoute(ComponentMap.SIGN_UP);
        if (this.nextParam) {
          return { ...signUpRoute, query: { next: this.nextParam } };
        }
        return signUpRoute;
      },
      loginOptions() {
        // POC, in the future sorting of different login options can be implemented
        return [...loginComponents];
      },
      logoText() {
        return this.themeConfig.signIn.title
          ? this.themeConfig.signIn.title
          : this.coreString('kolibriLabel');
      },
      oidcProviderFlow() {
        return plugin_data.oidcProviderEnabled && this.nextParam;
      },
      versionMsg() {
        // Split the version string at the first occurrence of '.' after the third number
        const version = __version.split('.').slice(0, 3).join('.');
        return this.$tr('poweredBy', { version });
      },
    },
    $trs: {
      oidcGenericExplanation: {
        message:
          'Kolibri is an e-learning platform. You can also use your Kolibri account to log in to some third-party applications.',
        context: 'Generic explanation about Kolibri.',
      },
      // eslint-disable-next-line kolibri/vue-no-unused-translations
      oidcSpecificExplanation: {
        message:
          "You were sent here from the application '{app_name}'. Kolibri is an e-learning platform, and you can also use your Kolibri account to access '{app_name}'.",
        context:
          'Explanation of Kolibri that a user sees if they are sent to Kolibri from a different application.',
      },
      poweredBy: {
        message: 'Kolibri {version}',
        context:
          'Indicates the current version of Kolibri.\n\nFor languages with non-latin scripts, Kolibri should be transcribed phonetically into the target language, similar to a person\'s name. It should not be translated as "hummingbird".',
      },
      poweredByKolibri: {
        message: 'Powered by Kolibri',
        context: 'Indicates that Kolibri is the technology behind this application.',
      },
      whatsThis: {
        message: "What's this?",
        context: 'Link with explanation of the authentication process.',
      },
      restrictedAccess: {
        message: 'Access to Kolibri has been restricted for external devices',
        context: 'Error message description.',
      },
      restrictedAccessDescription: {
        message:
          'To change this, sign in as a super admin and update the Device network access settings',

        context: 'Error message description',
      },
      photoCreditLabel: {
        message: ' ',
        context: 'Gives credit to the photographer of the background image.',
      },
    },
  };

</script>


<style lang="scss" scoped>

  @import '~kolibri-design-system/lib/styles/definitions';

  .fh {
    height: 100%;
  }

  .wrapper-table {
    display: table;
    width: 100%;
    height: 100%;
    text-align: center;
  }

  .table-row {
    display: table-row;
  }

  .main-row {
    text-align: center;
    background-repeat: no-repeat;
    background-position: center;
    background-size: cover;
  }

  .table-cell {
    display: table-cell;
  }

  .main-cell {
    height: 100%;
    vertical-align: middle;
  }

  .box {
    @extend %dropshadow-16dp;

    width: 360px;
    padding: 32px;
    margin: 16px auto;
    border-radius: $radius;
  }

  .login-btn {
    width: calc(100% - 16px);
  }

  .create {
    margin-top: 24px;
    margin-bottom: 0;
  }

  .small-text {
    font-size: 0.8em;
  }

  .version-string {
    white-space: nowrap;
  }

  .footer-cell {
    @extend %dropshadow-8dp;

    padding: 16px;
  }

  .footer-cell .small-text {
    margin-top: 8px;
  }

  .suggestions-wrapper {
    position: relative;
    width: 100%;
  }

  .suggestions {
    @extend %dropshadow-1dp;

    position: absolute;
    z-index: 8;
    width: 100%;
    padding: 0;
    margin: 0;
    // Move up snug against the textbox
    margin-top: -2em;
    list-style-type: none;
  }

  .textbox-enter-active {
    transition: opacity 0.5s;
  }

  .textbox-enter {
    opacity: 0;
  }

  .list-leave-active {
    transition: opacity 0.1s;
  }

  .textbox-leave {
    transition: opacity 0s;
  }

  .logo {
    width: 100%;
    max-width: 65vh; // not compatible with older browsers
    height: auto;
  }

  .kolibri-title {
    margin-top: 0;
    margin-bottom: 0;
    font-size: 24px;
    font-weight: 100;
  }

  .footer-logo {
    position: relative;
    top: -1px;
    display: inline-block;
    height: 24px;
    margin-right: 10px;
    margin-left: 8px;
    vertical-align: middle;
  }

  /deep/ .ui-textbox-input {
    &:hover {
      outline: none;
    }
  }

</style>
