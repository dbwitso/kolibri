<template>

  <div class="sign-in-text">
    <img
      class="sign-in-logo"
      :src="logo"
      :alt="userString('signingInLabel')"
    >
  </div>

</template>


<script>
  import commonUserStrings from '../commonUserStrings';
  import logo from './kolibri.svg';

  export default {
    name: 'SignInHeading',
    mixins: [commonUserStrings],
    data() {
      return {
        logo,
      };
    },
  };

</script>


<style scoped lang="scss">

  .sign-in-text {
    margin-top: 24px;
    margin-bottom: 16px;
    text-align: center;
  }

  .sign-in-logo {
    max-width: 160px;
    height: auto;
  }

</style>
