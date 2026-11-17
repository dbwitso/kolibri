import plugin_data from 'plugin_data';

// False on servers with assessments switched off (LSHE_DISABLE_ASSESSMENTS,
// as on LSHE servers): the assessments API then refuses every request, so
// pages must neither call it nor offer assessment tabs.
export default plugin_data.assessments_enabled !== false;
