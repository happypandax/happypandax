import classNames from 'classnames';
import { forwardRef, useCallback, useEffect, useState } from 'react';
import { useRecoilValue, useSetRecoilState } from 'recoil';
import {
  Divider,
  Icon,
  Label,
  List,
  Loader,
  Menu,
  Ref,
} from 'semantic-ui-react';

import { useQueryClient } from '@tanstack/react-query';

import { useSetting } from '../../client/hooks/settings';
import t from '../../client/lang';
import {
  getQueryTypeKey,
  MutatationType,
  QueryType,
  useMutationType,
  useQueryType,
} from '../../client/queries';
import { LogType, QueueType } from '../../shared/enums';
import { DownloadHandler, MetadataHandler } from '../../shared/types';
import { AppState } from '../../state';
import { ServerLog } from '../misc';
import { Progress } from '../misc/Progress';
import { SortableItemItem, SortableList } from '../misc/SortableList';

export function ItemQueueBase({
  Settings,
  refetch,
  onActive,
  running,
  log_type,
  queue_size,
  logDefaultVisible = false,
  logExpanded,
  finish_size,
  percent,
  active_size,
  queue_type,
  menuItems,
}: {
  Settings: React.ElementType;
  running: boolean;
  log_type: LogType;
  logDefaultVisible?: boolean;
  logExpanded?: boolean;
  queue_size: number;
  finish_size: number;
  percent: number;
  active_size: number;
  queue_type: QueueType;
  onActive: (boolean) => void;
  refetch: () => Promise<any>;
  menuItems?: React.ReactNode;
}) {
  const [runningLoading, setRunningLoading] = useState(false);
  const [clearLoading, setClearLoading] = useState(false);
  const [active, setActive] = useState(true);
  const [logVisible, setLogVisible] = useState(logDefaultVisible);
  const [settingsVisible, setSettingsVisible] = useState(false);

  const setDrawerSticky = useSetRecoilState(AppState.drawerSticky);
  const drawerExpanded = useRecoilValue(AppState.drawerExpanded);

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

  const _logExpanded = logExpanded ?? drawerExpanded;

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
        <Menu.Item>
          <Label color="black">
            {t`Session`}:
            <Label.Detail>
              {queue_size} ⟹ {active_size} ⟹ {finish_size}
            </Label.Detail>
          </Label>
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
          className={classNames('no-margins', {
            'max-300-h': _logExpanded,
            'max-100-h': !_logExpanded,
          })}
          attached="top"
        />
      )}
      <Progress
        size="tiny"
        className="no-margins"
        autoSuccess
        value={percent}
        total={100}
      />
      <Divider hidden horizontal />
    </>
  );
}

export const HandlerLabel = forwardRef(function HandlerLabel(
  {
    item,
    ...props
  }: {
    item: {
      id: string;
      handler: MetadataHandler | DownloadHandler;
      index: number;
      type: 'metadata' | 'download';
    };
  },
  ref
) {
  const [disabled, setDisabled] = useSetting<string[]>(
    item?.type === 'metadata' ? 'metadata.disabled' : 'download.disabled',
    []
  );

  return (
    <Ref innerRef={ref}>
      <Label
        basic
        color={disabled.includes(item.id) ? 'red' : 'green'}
        {...props}
        size="small">
        <DragItem />
        {item.index}
        <Label.Detail>
          {item.id}
          <span className="small-margin-left">
            <Icon
              onClick={useCallback(() => {
                const v = disabled.includes(item.id)
                  ? disabled.filter((i) => i !== item.id)
                  : [...disabled, item.id];
                setDisabled(v);
              }, [disabled])}
              color={disabled.includes(item.id) ? 'red' : 'green'}
              link
              name="circle"
            />
          </span>
        </Label.Detail>
      </Label>
    </Ref>
  );
});

export function HandlerLabelSortItem(props) {
  return <SortableItemItem as={HandlerLabel} {...props} />;
}

export function HandlerLabelGroup({ type }: { type: 'metadata' | 'download' }) {
  const { data, remove } = useQueryType(
    type === 'metadata' ? QueryType.METADATA_INFO : QueryType.DOWNLOAD_INFO
  );

  const [priority, setPriority] = useSetting<string[]>(
    type === 'metadata' ? 'metadata.priority' : 'download.priority',
    []
  );

  const handlers = data?.data ?? [];

  const onChange = useCallback((items) => {
    setPriority(items.map((i) => i.id));
    setTimeout(() => {
      remove();
    }, 500);
  }, []);

  return handlers.length ? (
    <SortableList
      onItemsChange={onChange}
      onlyOnDragItem
      direction="horizontal"
      element={HandlerLabelSortItem}
      items={handlers
        .map((h, i) => ({ id: h.identifier, handler: h, index: i + 1, type }))
        .sort((a, b) => priority.indexOf(a.id) - priority.indexOf(b.id))}
    />
  ) : (
    <>{t`No handlers activated`}</>
  );
}

function DragItem() {
  return (
    <Icon
      link
      name="border none"
      style={{ cursor: 'move' }}
      className="sub-text"
      data-drag-item="true"
    />
  );
}

export const HandlerItem = forwardRef(function HandlerItem(
  {
    item,
    ...props
  }: {
    item: {
      id: string;
      handler: MetadataHandler | DownloadHandler;
      type: 'metadata' | 'download';
    };
  },
  ref
) {
  const [value, setValue] = useSetting<string[]>(
    item?.type === 'metadata' ? 'metadata.disabled' : 'download.disabled',
    []
  );
  const qclient = useQueryClient();

  const disabled = value.includes(item.id);
  return (
    <Ref innerRef={ref}>
      <List.Item
        {...props}
        style={{ ...props?.style, display: 'flex', alignItems: 'center' }}>
        <DragItem />

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
                  setTimeout(() => {
                    qclient.invalidateQueries(
                      getQueryTypeKey(QueryType.METADATA_INFO)
                    );
                    qclient.invalidateQueries(
                      getQueryTypeKey(QueryType.DOWNLOAD_INFO)
                    );
                  }, 500);
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
