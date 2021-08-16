import classNames from 'classnames';
import { useMemo } from 'react';
import { Header, Icon, Modal, Segment, Tab } from 'semantic-ui-react';

import t from '../misc/lang';

function GeneralPane() {
  return <Segment basic></Segment>;
}

function NetworkPane() {
  return <Segment basic></Segment>;
}

function ServerPane() {
  return <Segment basic></Segment>;
}

function AdvancedPane() {
  return <Segment basic></Segment>;
}

export function SettingsTab() {
  return (
    <Tab
      menu={useMemo(
        () => ({
          pointing: true,
          secondary: true,
          stackable: true,
        }),
        []
      )}
      panes={useMemo(
        () => [
          {
            menuItem: {
              key: 'general',
              icon: 'cog',
              content: t`General`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <GeneralPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'plugins',
              icon: 'cubes',
              content: t`Plugins`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <NetworkPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'network',
              icon: 'project diagram',
              content: t`Network`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <NetworkPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'server',
              icon: <Icon className="hpx-standard" />,
              content: t`Server`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <ServerPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'advanced',
              icon: 'exclamation triangle',
              content: t`Advanced`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <AdvancedPane />
              </Tab.Pane>
            ),
          },
        ],
        []
      )}
    />
  );
}

export default function SettingsModal({
  className,
  ...props
}: React.ComponentProps<typeof Modal>) {
  return (
    <Modal
      dimmer="inverted"
      closeIcon
      {...props}
      className={classNames('min-400-h', className)}>
      <Modal.Header>
        <Icon name="settings" />
        {t`Preferences`}
      </Modal.Header>
      <Modal.Content as={Segment} className="no-margins" basic>
        <SettingsTab />
      </Modal.Content>
    </Modal>
  );
}
