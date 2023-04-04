import classNames from 'classnames';
import { Label, List } from 'semantic-ui-react';

import t from '../../client/lang';
import { dateFromTimestamp } from '../../client/utility';
import { ActivityType, CommandState } from '../../shared/enums';
import { Activity, CommandProgress } from '../../shared/types';
import { Progress } from './Progress';

export function ActivityList({
  data,
  detail,
}: {
  detail?: boolean;
  data: (CommandProgress | Activity)[];
}) {
  const title = {
    [ActivityType.Metadata]: t`Fetching metadata...`,
    [ActivityType.ItemMove]: t`Moving item...`,
    [ActivityType.ItemUpdate]: t`Updating item...`,
    [ActivityType.Image]: t`Generating image...`,
    [ActivityType.ItemSimilar]: t`Getting similar items...`,
    [ActivityType.SyncWithSource]: t`Syncing with source...`,
  };

  return (
    <List size="mini">
      {data?.map?.((p) => {
        const done = [
          CommandState.Finished,
          CommandState.Stopped,
          CommandState.Failed,
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
                      {p.state === CommandState.Failed
                        ? t`Failed`
                        : p.state === CommandState.Finished
                        ? t`Finished`
                        : p.state === CommandState.InQueue
                        ? t`In Queue`
                        : p.state === CommandState.InService
                        ? t`In Service`
                        : p.state === CommandState.OutOfService
                        ? t`Out of Service`
                        : p.state === CommandState.Started
                        ? t`Started`
                        : p.state === CommandState.Stopped
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
                  p.state === CommandState.Started
                    ? 'fast'
                    : [CommandState.InService, CommandState.InQueue].includes(
                        p.state
                      )
                    ? 'slow'
                    : undefined
                }
                indicating={
                  !done ||
                  [CommandState.InService, CommandState.OutOfService].includes(
                    p.state
                  )
                }
                size={detail ? 'small' : 'tiny'}
                progress={detail ? 'percent' : false}
                percent={p.max ? undefined : done ? 100 : undefined}
                total={p.max ? p.max : undefined}
                centered
                value={p.max ? p.value : undefined}
                success={p.state === CommandState.Finished}
                error={p.state === CommandState.Failed}
                warning={p.state === CommandState.Stopped}
                autoSuccess={p.max ? true : false}
              >
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
