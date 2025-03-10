import {getDefaultFormState, ObjectFieldTemplateProps} from '@rjsf/utils';
import React, {useEffect, useState} from 'react';
import ChildCheckboxContainer from '../ui-components/ChildCheckbox';
import {AdvancedMultiSelectHeader} from '../ui-components/AdvancedMultiSelect';
import {MasterCheckboxState} from '../ui-components/MasterCheckbox';
import {InfoPane, WarningType} from '../ui-components/InfoPane';
import {EXPLOITERS_PATH_PROPAGATION} from './PropagationConfig';
import {CONFIGURATION_TABS} from './ConfigurationTabs.js'

export const CREDENTIALS_COLLECTORS_CONFIG_PATH = 'credentials_collectors';
export const PAYLOADS_CONFIG_PATH = 'payloads';
const PLUGIN_SCHEMA_PATH = {
  [CONFIGURATION_TABS.PROPAGATION]: EXPLOITERS_PATH_PROPAGATION,
  [CONFIGURATION_TABS.CREDENTIALS_COLLECTORS]: CREDENTIALS_COLLECTORS_CONFIG_PATH,
  [CONFIGURATION_TABS.PAYLOADS]: PAYLOADS_CONFIG_PATH
};


export default function PluginSelectorTemplate(props: ObjectFieldTemplateProps) {

  let [activePlugin, setActivePlugin] = useState(null);
  const [defaultSchema,] = useState(generateDefaultConfig());

  useEffect(() => updateUISchema(), [props.formContext.selectedPlugins]);

  function getPluginDisplay(plugin, allPlugins) {
    let activePlugins = allPlugins.filter((pluginInArray) => pluginInArray.name == plugin);
    if (activePlugins.length === 1) {
      let activePlugin = activePlugins[0];
      let pluginWarningType = isPluginSafe(activePlugin.name) ?
        WarningType.NONE : WarningType.SINGLE;
      return <InfoPane title={''}
                       body={activePlugin.content}
                       link={activePlugin.content.props.schema.link_to_documentation}
                       warningType={pluginWarningType}/>
    }
    return <InfoPane title={props.schema.title}
                     body={props.schema.description}
                     warningType={WarningType.NONE}/>
  }

  function getOptions() {
    let selectorOptions = [];
    for (let [name, schema] of Object.entries(props.schema.properties || {})) {
      // @ts-expect-error
      selectorOptions.push({label: schema.title, value: name, isActive: (name === activePlugin)});
    }
    return selectorOptions;
  }

  function togglePlugin(pluginName) {
    let plugins = new Set(props.formContext.selectedPlugins);
    if (props.formContext.selectedPlugins.has(pluginName)) {
      plugins.delete(pluginName);
    } else {
      plugins.add(pluginName);
    }
    props.formContext.setSelectedPlugins(plugins, props.formContext.section);
  }

  const updateUISchema = () => {
    let uiSchema = {...props.uiSchema};
    for (let pluginName of Object.keys(defaultSchema)) {
      uiSchema[pluginName] = Object.assign({...uiSchema[pluginName]}, {'ui:readonly': !props.formContext.selectedPlugins.has(pluginName)});
    }

    props.formContext.setUiSchema(uiSchema, PLUGIN_SCHEMA_PATH[props.formContext.section]);
  }

  function getMasterCheckboxState(selectValues) {
    if (Object.keys(selectValues).length === 0) {
      return MasterCheckboxState.NONE;
    }

    if (Object.keys(selectValues).length !== getOptions().length) {
      return MasterCheckboxState.MIXED;
    }

    return MasterCheckboxState.ALL;
  }

  function generateDefaultConfig() {
    // @ts-expect-error
    return getDefaultFormState(props.registry.schemaUtils.validator,
      props.schema, {}, props.registry.rootSchema, true);
  }

  function onMasterPluginCheckboxClick() {
    let checkboxState = getMasterCheckboxState([...props.formContext.selectedPlugins]);
    let selectedSection = props.formContext.section
    if (checkboxState == MasterCheckboxState.ALL) {
      props.formContext.setSelectedPlugins(new Set(), selectedSection);
    } else {
     props.formContext.setSelectedPlugins(new Set(Object.keys(defaultSchema)), selectedSection);
    }
  }

  function isPluginSafe(itemKey) {
    let itemSchema = Object.entries(props.schema.properties).filter(e => e[0] == itemKey)[0][1];
    return itemSchema['safe'];
  }

  function getHideResetState(selectValues) {
    return !(isUnsafePluginSelected(selectValues))
  }

  function isUnsafePluginSelected(selectValues) {
    return !(selectValues.every((value) => isPluginSafe(value)));
  }

  function onResetClick() {
    let safePluginNames = [...props.formContext.selectedPlugins].filter(
      pluginName => isPluginSafe(pluginName));
    props.formContext.setSelectedPlugins(new Set(safePluginNames), props.formContext.section);
  }

  return (
    <div className={'advanced-multi-select'}>
      <AdvancedMultiSelectHeader title={props.schema.title}
                                 onCheckboxClick={onMasterPluginCheckboxClick}
                                 checkboxState={
                                   getMasterCheckboxState(
                                     [...props.formContext.selectedPlugins])}
                                 hideReset={getHideResetState(
                                       [...props.formContext.selectedPlugins])}
                                 onResetClick={onResetClick}
                                 resetButtonTitle={'Disable unsafe'}/>
      <ChildCheckboxContainer multiple={true} required={false}
                              autoFocus={true}
                              selectedValues={[...props.formContext.selectedPlugins]}
                              onCheckboxClick={togglePlugin}
                              isSafe={isPluginSafe}
                              onPaneClick={setActivePlugin}
                              enumOptions={getOptions()}/>
      {getPluginDisplay(activePlugin, props.properties)}
    </div>
  );
}
