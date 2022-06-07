import classNames from 'classnames';
import { Label, List } from 'semantic-ui-react';

import { ActivityType, CommandState } from '../../misc/enums';
import t from '../../misc/lang';
import { Activity, CommandProgress } from '../../misc/types';
import { dateFromTimestamp } from '../../misc/utility';
import { Progress } from './Progress';

export function ActivityList({
  data,
  detail,
}: {
  detail?: boolean;
  data: (CommandProgress | Activity)[];
}) {
  const title = {
    [ActivityType.metadata]: t`Fetching metadata...`,
    [ActivityType.item_move]: t`Moving item...`,
    [ActivityType.item_update]: t`Updating item...`,
    [ActivityType.image]: t`Generating image...`,
    [ActivityType.items_similar]: t`Getting similar items...`,
    [ActivityType.sync_with_source]: t`Syncing with source...`,
  };

  return (
    <List size="mini">
      {data?.map?.((p) => {
        const done = [
          CommandState.finished,
          CommandState.stopped,
          CommandState.failed,
        ].includes(p.state);

        console.debug({ p });

        return (
          <List.Item key={p.id}>
            <List.Content>
              <List.Header>
                <span className="right">
                  <Label size="mini">
                    {t`ID`}:<Label.Detail>{p.id}</Label.Detail>
                  </Label>
                  <Label size="mini" basic color="black">
                    {t`Status`}:
                    <Label.Detail>
                      {p.state === CommandState.failed
                        ? t`Failed`
                        : p.state === CommandState.finished
                        ? t`Finished`
                        : p.state === CommandState.in_queue
                        ? t`In Queue`
                        : p.state === CommandState.in_service
                        ? t`In Service`
                        : p.state === CommandState.out_of_service
                        ? t`Out of Service`
                        : p.state === CommandState.started
                        ? t`Started`
                        : p.state === CommandState.stopped
                        ? t`Stopped`
                        : t`Unknown`}
                    </Label.Detail>
                  </Label>
                </span>
                {(p as Activity)?.activity_type
                  ? title[(p as Activity)?.activity_type] || p.title
                  : p.title}
              </List.Header>
              <Progress
                className={classNames('centered', {
                  ['no-margins']: !detail || p.subtitle,
                })}
                precision={2}
                active={!done}
                color={!p.max && !done ? 'blue' : undefined}
                indeterminate={!p.max && !done ? 'filling' : undefined}
                speed={
                  p.state === CommandState.started
                    ? 'fast'
                    : [CommandState.in_service, CommandState.in_queue].includes(
                        p.state
                      )
                    ? 'slow'
                    : undefined
                }
                indicating={
                  !done ||
                  [
                    CommandState.in_service,
                    CommandState.out_of_service,
                  ].includes(p.state)
                }
                size={detail ? 'small' : 'tiny'}
                progress={detail ? 'percent' : false}
                percent={p.max ? undefined : done ? 100 : undefined}
                total={p.max ? p.max : undefined}
                centered
                value={p.max ? p.value : undefined}
                success={p.state === CommandState.finished}
                error={p.state === CommandState.failed}
                warning={p.state === CommandState.stopped}
                autoSuccess={p.max ? true : false}>
                {p.subtitle}
              </Progress>
              <List.Description className="sub-text">
                <List divided horizontal size="mini">
                  <List.Item>
                    {dateFromTimestamp(p.timestamp, { relative: true })}
                  </List.Item>
                  {p.text && (
                    <List.Item>
                      <List.Content>{p.text}</List.Content>
                    </List.Item>
                  )}
                </List>
              </List.Description>
            </List.Content>
          </List.Item>
        );
      })}
    </List>
  );
}
