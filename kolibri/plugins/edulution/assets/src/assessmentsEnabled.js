import plugin_data from 'plugin_data';

// False on servers with assessments switched off (LSHE_DISABLE_ASSESSMENTS,
// as on LSHE servers): the assessments API then refuses every request, so
// pages must not call it.
export default plugin_data.assessmentsEnabled !== false;
