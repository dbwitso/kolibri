<template>

  <KModal
    :title="$tr('newLearnerGroup')"
    size="small"
    :submitText="coreString('saveAction')"
    :cancelText="coreString('cancelAction')"
    :submitDisabled="submitting"
    @cancel="$emit('cancel')"
    @submit="callCreateGroup"
  >
    <KTextbox
      ref="name"
      v-model.trim="name"
      type="text"
      :label="coachString('groupNameLabel')"
      :autofocus="true"
      :invalid="nameIsInvalid"
      :invalidText="nameIsInvalidText"
      :maxlength="50"
      @blur="nameBlurred = true"
    />
  </KModal>

</template>


<script>

  import { mapActions } from 'vuex';
  import commonCoreStrings from 'kolibri.coreVue.mixins.commonCoreStrings';
  import { coachStringsMixin } from '../../common/commonCoachStrings';

  export default {
    name: 'CreateGroupModal',
    mixins: [coachStringsMixin, commonCoreStrings],
    props: {
      groups: {
        type: Array,
        required: true,
      },
    },
    data() {
      return {
        name: '',
        nameBlurred: false,
        formSubmitted: false,
        submitting: false,
      };
    },
    computed: {
      classId() {
        // classSummary.id is populated by an independent async fetch (initClassInfo)
        // and is not guaranteed to be set yet when this page mounts/renders, unlike
        // the classId route param which this page's own route always provides.
        return this.$route.params.classId;
      },
      duplicateName() {
        const index = this.groups.findIndex(
          group => group.name.toUpperCase() === this.name.toUpperCase()
        );
        if (index === -1) {
          return false;
        }
        return true;
      },
      nameIsInvalidText() {
        if (this.submitting) return '';
        if (this.nameBlurred || this.formSubmitted) {
          if (this.name === '') {
            return this.coreString('requiredFieldError');
          }
          if (this.duplicateName) {
            return this.$tr('duplicateName');
          }
        }
        return '';
      },
      nameIsInvalid() {
        return Boolean(this.nameIsInvalidText);
      },
      formIsValid() {
        return !this.nameIsInvalid;
      },
    },
    methods: {
      ...mapActions('groups', ['createGroup']),
      callCreateGroup() {
        this.formSubmitted = true;
        if (this.formIsValid) {
          this.submitting = true;
          this.createGroup({ groupName: this.name, classId: this.classId }).then(() => {
            this.$emit('submit');
          });
        } else {
          this.$refs.name.focus();
        }
      },
    },
    $trs: {
      newLearnerGroup: {
        message: 'Create new group',
        context: 'Name of window used to create a new group of learners.',
      },
      duplicateName: {
        message: 'A group with that name already exists',
        context:
          'Error message that displays if user creates a group with a name that already exisits.',
      },
    },
  };

</script>


<style lang="scss" scoped></style>
