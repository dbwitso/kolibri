<template>

  <!-- The theme's footer logos (theme "footer.logos", e.g. a programme's
       partners), at the foot of the sign-in page: shown before signing in,
       not on the pages after. Nothing when the theme lists none. -->
  <!-- A white strip, so the logos (often on white) never sit in boxes on
       the grey page. -->
  <footer
    v-if="logos.length"
    class="partner-footer"
    :style="{ backgroundColor: $themeTokens.surface, borderColor: $themeTokens.fineLine }"
  >
    <ul class="logos" :aria-label="$tr('partnersLabel')">
      <li v-for="logo in logos" :key="logo.src" class="logo">
        <img :src="logo.src" :alt="logo.alt" :style="logo.style">
      </li>
    </ul>
  </footer>

</template>


<script>

  import themeConfig from '../styles/themeConfig';

  export default {
    name: 'PartnerFooter',
    computed: {
      logos() {
        return ((themeConfig.footer && themeConfig.footer.logos) || []).filter(
          logo => logo && logo.src
        );
      },
    },
    $trs: {
      partnersLabel: {
        message: 'Partners',
        context: 'Accessible name for the row of partner logos in the page footer.',
      },
    },
  };

</script>


<style lang="scss" scoped>

  .partner-footer {
    padding: 20px 16px;
    margin-top: 32px;
    border: 1px solid;
    border-radius: 8px;
  }

  // The logos scale with the screen width: full size on a laptop, smaller
  // on a 10-11 inch tablet in landscape (850-1340px wide, by model) so all
  // of them stay on one line, and on two rows on a phone.
  .logos {
    display: flex;
    flex-wrap: wrap;
    gap: 16px clamp(14px, 2.6vw, 40px);
    align-items: center;
    justify-content: center;
    padding: 0;
    margin: 0;
    list-style: none;
  }

  // One line from tablet width up.
  @media (min-width: 700px) {
    .logos {
      flex-wrap: nowrap;
    }
  }

  // One height for all, so a crest is as readable as a wordmark; the width
  // cap keeps wide logos from taking over.
  .logo img {
    display: block;
    width: auto;
    max-width: clamp(110px, 17vw, 230px);
    height: clamp(34px, 4.8vw, 64px);
    object-fit: contain;
  }

</style>
