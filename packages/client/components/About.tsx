import classNames from 'classnames';
import { useMemo } from 'react';
import {
  Button,
  Grid,
  Header,
  Icon,
  Label,
  Modal,
  Segment,
  Tab,
  Table,
} from 'semantic-ui-react';

import t from '../client/lang';
import { useQueryType } from '../client/queries';
import { QueryType } from '../shared/query';
import { CommandProgress } from '../shared/types';
import { useGlobalValue } from '../state/global';
import { EmptySegment } from './misc';
import { ActivityList } from './misc/ActivityList';
import { ModalWithBack } from './misc/BackSupport';
import { TrashTabView } from './Trash';

function InfoPane() {
  const packageJson = useGlobalValue('packageJson');
  const { data } = useQueryType(QueryType.PROPERTIES, {
    keys: ['version'],
  });

  return (
    <Grid as={Segment} basic>
      <Grid.Row textAlign="center">
        <Grid.Column>
          {data?.data?.version?.beta && <Label color="violet">{t`Beta`}</Label>}
          {data?.data?.version?.alpha && <Label color="red">{t`Alpha`}</Label>}
          <Label basic color="purple">
            {data?.data?.version?.name}
          </Label>
          <Label basic>
            {t`Webclient`} <Label.Detail>{packageJson?.version}</Label.Detail>
          </Label>
          <Label basic>
            {t`Server`}{' '}
            <Label.Detail>
              {data?.data?.version?.core?.join?.('.')}
            </Label.Detail>
          </Label>
          <Label basic>
            {t`Database`}{' '}
            <Label.Detail>{data?.data?.version?.db?.join?.('.')}</Label.Detail>
          </Label>
          <Label basic>
            {t`Torrent`}{' '}
            <Label.Detail>
              {data?.data?.version?.torrent?.join?.('.')}
            </Label.Detail>
          </Label>
          <Label basic color="grey">
            {t`#`}
            {data?.data?.version?.build}
          </Label>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Button
            as="a"
            href="https://www.patreon.com/twiddly"
            rel="noreferrer"
            target="_blank"
            size="small"
            color="orange">
            <Icon name="heart" />
            {t`Support on Patreon`}
          </Button>
          <Button
            as="a"
            href="https://ko-fi.com/twiddly"
            rel="noreferrer"
            target="_blank"
            size="small"
            color="blue">
            <Icon name="coffee" />
            {t`Buy me a Coffee`}
          </Button>

          <Button
            as="a"
            href="https://github.com/happypandax"
            rel="noreferrer"
            target="_blank"
            size="small"
            floated="right">
            <Icon name="github" />
            {t`View on Github`}
          </Button>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Table basic="very" size="small">
            <Table.Body>
              <Table.Row>
                <Table.Cell collapsing>
                  <Header as="h5">
                    <Icon name="github" />
                    {t`Developer`}
                  </Header>
                </Table.Cell>
                <Table.Cell>
                  <a
                    href="https://github.com/twiddli"
                    target="_blank"
                    rel="noreferrer">
                    Twiddly
                  </a>
                </Table.Cell>
              </Table.Row>
              <Table.Row>
                <Table.Cell collapsing>
                  <Header as="h5">
                    <Icon name="twitter" />
                    Twitter
                  </Header>
                </Table.Cell>
                <Table.Cell>
                  <a
                    href="https://twitter.com/twiddly_"
                    target="_blank"
                    rel="noreferrer">
                    @twiddly_
                  </a>
                </Table.Cell>
              </Table.Row>
            </Table.Body>
          </Table>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Button size="small">
            <Icon name="refresh" />
            {t`Check for updates`}
          </Button>
          <Button size="small" basic floated="right">
            <Icon name="settings" />
            {t`Reset web client settings`}
          </Button>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
}

function ActivityPane() {
  const { data } = useQueryType(QueryType.COMMAND_PROGRESS, undefined, {
    refetchInterval: 1000,
    refetchOnMount: true,
  });

  return (
    <Segment basic className="small-padding-segment max-400-h">
      {!data?.data?.length && <EmptySegment />}
      {!!data?.data?.length && (
        <ActivityList data={data.data as CommandProgress[]} detail />
      )}
    </Segment>
  );
}

function TrashPane() {
  return (
    <Segment basic>
      <TrashTabView />
    </Segment>
  );
}

export function AboutTab() {
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
            menuItem: { key: 'info', icon: 'info circle', content: t`Info` },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <InfoPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'activity',
              icon: 'exchange',
              content: t`Activity`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <ActivityPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'trash',
              icon: 'trash',
              content: t`Trash`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <TrashPane />
              </Tab.Pane>
            ),
          },
        ],
        []
      )}
    />
  );
}

export default function AboutModal({
  className,
  ...props
}: React.ComponentProps<typeof Modal>) {
  const debug = useGlobalValue('debug');

  return (
    <ModalWithBack
      dimmer="inverted"
      closeIcon
      {...props}
      className={classNames('min-300-h', className)}>
      <Modal.Content as={Segment} basic>
        <Header icon textAlign="center">
          <Icon className="hpx-standard" circular />
          {t`About`}
        </Header>
        <AboutTab />
      </Modal.Content>
      {debug && (
        <Segment
          attached="bottom"
          textAlign="center"
          inverted
          color="violet"
          tertiary
          className="no-margins">
          {t`Running in debug mode`}
        </Segment>
      )}

      <Segment
        attached="bottom"
        textAlign="center"
        secondary
        className="no-margins">
        {t`HappyPanda X is a cross platform manga/doujinshi manager made out of pure`}
        <Icon name="heart" color="red" size="large" />
        {t`by`}{' '}
        <a href="https://twitter.com/twiddly_" target="_blank" rel="noreferrer">
          Twiddly
        </a>
      </Segment>
    </ModalWithBack>
  );
}
