<template>

  <!-- The theme's footer logos (theme "footer.logos", e.g. a programme's
       partners), at the foot of every page and of the sign-in page. Nothing
       when the theme lists none. -->
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

  .logos {
    display: flex;
    flex-wrap: wrap;
    gap: 24px 40px;
    align-items: center;
    justify-content: center;
    padding: 0;
    margin: 0;
    list-style: none;
  }

  // One height for all, so a crest is as readable as a wordmark; the width
  // cap keeps wide logos from taking over.
  .logo img {
    display: block;
    width: auto;
    max-width: 230px;
    height: 64px;
    object-fit: contain;
  }

  // Smaller on phones, so the logos fit on one or two rows.
  @media (max-width: 600px) {
    .logos {
      gap: 16px 24px;
    }

    .logo img {
      max-width: 150px;
      height: 44px;
    }
  }

</style>
