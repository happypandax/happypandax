import { forwardRef, useCallback, useEffect, useState } from 'react';
import { useQueryClient } from 'react-query';
import { useSetRecoilState } from 'recoil';
import { Icon, Label, List, Loader, Menu, Ref } from 'semantic-ui-react';

import { useSetting } from '../../client/hooks/settings';
import {
  getQueryTypeKey,
  MutatationType,
  QueryType,
  useMutationType,
} from '../../client/queries';
import { LogType, QueueType } from '../../misc/enums';
import t from '../../misc/lang';
import { DownloadHandler, MetadataHandler } from '../../misc/types';
import { AppState } from '../../state';
import { ServerLog, SortableItemItem } from '../Misc';

export function ItemQueueBase({
  Settings,
  refetch,
  onActive,
  running,
  log_type,
  queue_type,
  menuItems,
}: {
  Settings: React.ElementType;
  running: boolean;
  log_type: LogType;
  queue_type: QueueType;
  onActive: (boolean) => void;
  refetch: () => Promise<any>;
  menuItems?: React.ReactNode;
}) {
  const [runningLoading, setRunningLoading] = useState(false);
  const [clearLoading, setClearLoading] = useState(false);
  const [active, setActive] = useState(true);
  const [logVisible, setLogVisible] = useState(false);
  const [settingsVisible, setSettingsVisible] = useState(false);

  const setDrawerSticky = useSetRecoilState(AppState.drawerSticky);

  const clearQueue = useMutationType(MutatationType.CLEAR_QUEUE, {
    onMutate: () => setClearLoading(true),
    onSettled: () => refetch().finally(() => setClearLoading(false)),
  });

  const stopQueue = useMutationType(MutatationType.STOP_QUEUE, {
    onMutate: () => {
      setActive(false), setRunningLoading(true);
    },
    onSettled: () => setRunningLoading(false),
  });
  const startQueue = useMutationType(MutatationType.START_QUEUE, {
    onMutate: () => {
      setActive(true), setRunningLoading(true);
    },
    onSettled: () => setRunningLoading(false),
  });

  useEffect(() => {
    setActive(running);
  }, [running]);

  useEffect(() => {
    const sticky = settingsVisible;
    if (!sticky) {
      setTimeout(() => {
        setDrawerSticky(settingsVisible);
      }, 500);
    } else {
      setDrawerSticky(settingsVisible);
    }
  }, [settingsVisible]);

  useEffect(() => {
    onActive?.(active);
  }, [active]);

  return (
    <>
      {!!Settings && (
        <Settings
          open={settingsVisible}
          closeIcon
          onClose={() => setSettingsVisible(false)}
        />
      )}
      <Menu labeled compact text fluid>
        <Menu.Item
          disabled={runningLoading}
          onClick={useCallback(() => {
            if (active) {
              stopQueue.mutate({ queue_type });
            } else {
              startQueue.mutate({ queue_type });
            }
          }, [active])}>
          <Loader active={runningLoading} size="small" />
          <Icon
            name={active ? 'play' : 'pause'}
            color={active ? 'green' : 'red'}
          />{' '}
          {active ? t`Running` : t`Paused`}
        </Menu.Item>
        <Menu.Item
          disabled={clearLoading}
          onClick={useCallback(() => {
            clearQueue.mutate({ queue_type });
          }, [])}>
          <Loader active={clearLoading} size="small" />
          <Icon name="remove" /> {t`Clear`}
        </Menu.Item>
        <Menu.Menu position="right">
          <Menu.Item
            onClick={useCallback(() => setLogVisible(!logVisible), [
              logVisible,
            ])}>
            <Icon name={logVisible ? 'angle down' : 'angle right'} /> {t`Log`}
          </Menu.Item>
          <Menu.Item
            onClick={useCallback(() => setSettingsVisible(!settingsVisible), [
              settingsVisible,
            ])}>
            <Icon name="setting" /> {t`Options`}
          </Menu.Item>
          {menuItems}
        </Menu.Menu>
      </Menu>
      {logVisible && (
        <ServerLog
          type={log_type}
          className="max-100-h no-margins"
          attached="top"
        />
      )}
    </>
  );
}

export const HandlerItem = forwardRef(function HandlerItem(
  {
    item,
    type,
    ...props
  }: {
    item: { id: string; handler: MetadataHandler | DownloadHandler };
    type: 'metadata' | 'download';
  },
  ref
) {
  const [value, setValue] = useSetting<string[]>(
    type === 'metadata' ? 'metadata.disabled' : 'download.disabled',
    []
  );
  const qclient = useQueryClient();

  const disabled = value.includes(item.id);
  return (
    <Ref innerRef={ref}>
      <List.Item
        {...props}
        style={{ ...props?.style, display: 'flex', alignItems: 'center' }}>
        <Icon link name="border none" data-drag-item="true" />

        <List.Content>
          <List.Header>
            {disabled && <Icon fitted name="ban" color="red" />}
            <Label basic>
              {t`Identifier`}
              <Label.Detail>{item?.id}</Label.Detail>
            </Label>
            {item?.handler?.name}
            {item?.handler?.sites && (
              <span className="right sub-text">
                {t`Sites`}: {item?.handler?.sites.join(', ')}
              </span>
            )}
          </List.Header>
          <List.Description>
            {item?.handler?.description}
            <Label.Group className="right">
              <Label
                as="a"
                basic
                color={disabled ? 'green' : 'red'}
                onClick={useCallback(() => {
                  let v = value.filter((v) => v !== item.id);
                  if (!disabled) {
                    v = [...v, item.id];
                  }
                  setValue(v);
                  qclient.invalidateQueries(
                    getQueryTypeKey(QueryType.METADATA_INFO)
                  );
                  qclient.invalidateQueries(
                    getQueryTypeKey(QueryType.DOWNLOAD_INFO)
                  );
                }, [value, disabled])}>
                {disabled ? t`Enable` : t`Disable`}
              </Label>
            </Label.Group>
          </List.Description>
        </List.Content>
      </List.Item>
    </Ref>
  );
});

export function HandlerSortableItem(
  props: React.ComponentProps<typeof HandlerItem>
) {
  return <SortableItemItem as={HandlerItem} {...props} />;
}
