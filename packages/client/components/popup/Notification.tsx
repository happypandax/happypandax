import classNames from 'classnames';
import { formatDistanceToNowStrict } from 'date-fns';
import { useCallback } from 'react';
import { useRecoilState, useRecoilValue, useSetRecoilState } from 'recoil';
import { Header, Icon, Popup, Segment } from 'semantic-ui-react';

import { AppState } from '../../state';
import { EmptySegment } from '../misc';
import styles from './Notification.module.css';

export function Notification({
  type = 'info',
  title,
  description,
  date,
  onClose,
}: {
  type?: 'info' | 'warning' | 'error';
  title: React.ReactNode;
  description?: React.ReactNode;
  onClose?: (e: any) => void;
  date?: Date;
}) {
  return (
    <Segment attached className={styles.notification}>
      <Header
        size="tiny"
        className="w-full"
        color={
          type === 'info' ? 'blue' : type === 'warning' ? 'orange' : 'red'
        }>
        <Icon
          name={
            type === 'info'
              ? 'info'
              : type === 'warning'
              ? 'exclamation'
              : 'exclamation circle'
          }
          color={
            type === 'info' ? 'blue' : type === 'warning' ? 'orange' : 'red'
          }
          className={classNames()}
        />
        <Header.Content className={styles.notification_content}>
          <div className="w-full">
            {!!onClose && (
              <Icon
                link
                onClick={onClose}
                name="close"
                className={classNames('sub-text', styles.notification_close)}
              />
            )}
            <span className="float-right sub-text small-text">
              {date ? formatDistanceToNowStrict(date, { addSuffix: true }) : ''}
            </span>
            {title}
          </div>
          <Header.Subheader>{description}</Header.Subheader>
        </Header.Content>
      </Header>
    </Segment>
  );
}

export const NotificationGroup = Segment.Group;

export function Notifications() {
  const notifications = useRecoilValue(AppState.notifications);

  return (
    <>
      {!notifications.length && <EmptySegment />}
      {notifications.map((d) => (
        <Notification
          key={d.date?.getTime?.()}
          type={d.type}
          title={d.title}
          description={d.body}
          date={d.date}
        />
      ))}
    </>
  );
}

export function NotificationsPopup({
  trigger,
}: {
  trigger: React.ComponentProps<typeof Popup>['trigger'];
}) {
  const setNotificationAlert = useSetRecoilState(AppState.notificationAlert);

  return (
    <Popup
      on="click"
      position="bottom right"
      onOpen={useCallback(() => {
        setNotificationAlert([]);
      }, [])}
      className={classNames('no-padding-segment', styles.notification_group)}
      trigger={trigger}>
      <Notifications />
    </Popup>
  );
}

export function NotificationAlert({
  context,
}: {
  context: React.ComponentProps<typeof Popup>['context'];
}) {
  const [notificationAlert, setNotificationAlert] = useRecoilState(
    AppState.notificationAlert
  );

  return (
    <Popup
      open={!!notificationAlert.length}
      context={context}
      position="bottom right"
      positionFixed
      className="no-padding-segment">
      {notificationAlert.map((d) => (
        <Notification
          key={d?.date?.getTime()}
          onClose={() => {
            setNotificationAlert(
              notificationAlert.filter(
                (n) => d.date.getTime() !== n.date.getTime()
              )
            );
          }}
          type={d.type}
          title={d.title}
          description={d.body}
          date={d.date}
        />
      ))}
    </Popup>
  );
}
