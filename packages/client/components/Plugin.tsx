import React, { useCallback, useState } from 'react';
import {
  Button,
  Divider,
  Header,
  Label,
  Message,
  Segment,
  SemanticCOLORS,
} from 'semantic-ui-react';

import { useQueryClient } from '@tanstack/react-query';

import t from '../client/lang';
import {
  getQueryTypeKey,
  MutatationType,
  QueryType,
  useMutationType,
  useQueryType,
} from '../client/queries';
import { PluginState } from '../shared/enums';
import { PluginData } from '../shared/types';
import { LabelAccordion } from './misc';

function getPluginState(state) {
  return state === PluginState.Installed || state === PluginState.Unloaded
    ? 'Not active'
    : state === PluginState.Disabled
    ? 'Disabled'
    : state === PluginState.Failed
    ? 'Failed'
    : state === PluginState.Registered
    ? 'Registered'
    : state === PluginState.Enabled
    ? 'Active'
    : 'Unknown';
}

function CheckUpdateButton({ plugin }: { plugin: PluginData }) {
  return <Label as={Button}>{t`Check for update`}</Label>;
}

export function Plugin({ plugin }: { plugin: PluginData }) {
  const client = useQueryClient();

  const [siteOpen, setSiteOpen] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  const { mutate: disablePlugin, isLoading: isDisabling } = useMutationType(
    MutatationType.DISABLE_PLUGIN,
    {
      onSuccess: () => {
        client.invalidateQueries(getQueryTypeKey(QueryType.PLUGINS));
      },
    }
  );

  const { mutate: installPlugin } = useMutationType(
    MutatationType.INSTALL_PLUGIN,
    {
      onMutate: () => {
        setIsInstalling(true);
      },
      onSettled: () => {
        setIsInstalling(false);
      },
      onSuccess: () => {
        setTimeout(() => {
          client.invalidateQueries(getQueryTypeKey(QueryType.PLUGINS));
        }, 2500);
      },
    }
  );

  const { mutate: removePlugin, isLoading: isRemoving } = useMutationType(
    MutatationType.REMOVE_PLUGIN,
    {
      onSuccess: () => {
        client.invalidateQueries(getQueryTypeKey(QueryType.PLUGINS));
      },
    }
  );

  console.debug(plugin.shortname, plugin.state);

  return (
    <Segment basic className="medium-padding-segment">
      <Header>
        <Label.Group className="right">
          <CheckUpdateButton plugin={plugin} />
        </Label.Group>
        <Label.Group>
          <Label color="black">
            {t`Shortname`}
            <Label.Detail>{plugin.shortname}</Label.Detail>
          </Label>
          <Label color="black">
            {t`ID`}
            <Label.Detail>{plugin.id}</Label.Detail>
          </Label>
          <Label color="black" basic>
            {t`Version`}
            <Label.Detail>{plugin.version}</Label.Detail>
          </Label>
        </Label.Group>
        {plugin.site && (
          <Label.Group className="right">
            <Label
              as={Button}
              color={siteOpen ? 'red' : 'blue'}
              onClick={() => setSiteOpen(!siteOpen)}>
              {siteOpen ? t`Close` : t`Open Plugin Site`}
            </Label>
          </Label.Group>
        )}
        <Label.Group size="small">
          <Label basic color="purple">
            {t`Author`}
            <Label.Detail>{plugin.author}</Label.Detail>
          </Label>
          <Label basic as="a" href={plugin.website} target="_blank">
            {t`Website`}
            <Label.Detail>{plugin.website}</Label.Detail>
          </Label>
        </Label.Group>
      </Header>
      {plugin.status && <Message warning>{plugin.status}</Message>}
      <div>{plugin.description}</div>
      {plugin.site && siteOpen && (
        <iframe width="100%" height="400px" src={plugin.site} />
      )}
      <Divider />
      <Button.Group fluid>
        <Button
          disabled={plugin.state === PluginState.Enabled}
          basic={plugin.state !== PluginState.Enabled}
          color="green"
          onClick={useCallback(() => {
            installPlugin({ plugin_id: plugin.id });
          }, [plugin])}>
          {isInstalling
            ? t`Installing...`
            : plugin.state === PluginState.Registered ||
              plugin.state === PluginState.Disabled
            ? t`Install`
            : plugin.state === PluginState.Unloaded ||
              plugin.state === PluginState.Installed
            ? t`Enable`
            : getPluginState(plugin.state)}
        </Button>
        <Button
          basic
          color={plugin.state === PluginState.Disabled ? 'orange' : 'black'}
          disabled={
            plugin.state === PluginState.Disabled ||
            plugin.state !== PluginState.Enabled
          }
          onClick={useCallback(() => {
            disablePlugin({ plugin_id: plugin.id });
          }, [plugin])}>
          {isDisabling
            ? t`Disabling...`
            : plugin.state === PluginState.Disabled
            ? t`Disabled`
            : t`Disable`}
        </Button>
        <Button
          basic
          color="red"
          onClick={useCallback(() => {
            removePlugin({ plugin_id: plugin.id });
          }, [plugin])}>
          {isRemoving ? t`Removing...` : t`Remove`}
        </Button>
      </Button.Group>
    </Segment>
  );
}

export function PluginAccordion({
  defaultVisible,
  ...props
}: React.ComponentProps<typeof Plugin> & { defaultVisible?: boolean }) {
  let color: SemanticCOLORS = 'grey';

  switch (props.plugin?.state) {
    case PluginState.Enabled:
      color = 'green';
      break;
    case PluginState.Disabled:
      color = 'orange';
      break;
    case PluginState.Failed:
      color = 'red';
      break;
    case PluginState.Unloaded:
      color = 'yellow';
      break;
  }

  return (
    <LabelAccordion
      clearing
      defaultVisible={defaultVisible}
      secondary
      basic={false}
      label={props.plugin?.name}
      color={color}
      detail={getPluginState(props.plugin?.state)}>
      <Plugin {...props} />
    </LabelAccordion>
  );
}

export function Plugins({
  defaultVisibleInactive,
  ...props
}: React.ComponentProps<typeof Segment> & {
  defaultVisibleInactive?: boolean;
}) {
  const { data, isLoading } = useQueryType(
    QueryType.PLUGINS,
    {},
    {
      refetchInterval: 5000,
      keepPreviousData: true,
      refetchOnMount: 'always',
    }
  );
  return (
    <Segment loading={isLoading} {...props} clearing>
      {data?.data
        ?.sort?.((a, b) => a.name.localeCompare(b.name))
        .map?.((plugin) => (
          <PluginAccordion
            defaultVisible={
              defaultVisibleInactive
                ? plugin.state !== PluginState.Enabled
                : undefined
            }
            key={plugin.id}
            plugin={plugin}
          />
        ))}
    </Segment>
  );
}
