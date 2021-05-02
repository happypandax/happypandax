import classNames from 'classnames';
import {
  useContext,
  useState,
  useCallback,
  createContext,
  useMemo,
} from 'react';
import {
  Segment,
  Menu,
  Label,
  Icon,
  Grid,
  Dimmer,
  Table,
  Header,
  Tab,
  Ref,
  Modal,
  Button,
} from 'semantic-ui-react';
import t from '../misc/lang';

function InfoPane() {
  return (
    <Grid as={Segment} basic>
      <Grid.Row textAlign="center">
        <Grid.Column>
          <Label basic>
            {t`Webclient`} <Label.Detail>1.1.1</Label.Detail>
          </Label>
          <Label basic>
            {t`Server`} <Label.Detail>1.1.1</Label.Detail>
          </Label>
          <Label basic>
            {t`Database`} <Label.Detail>1.1.1</Label.Detail>
          </Label>
          <Label basic>
            {t`Torrent`} <Label.Detail>1.1.1</Label.Detail>
          </Label>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Button
            as="a"
            href="https://www.patreon.com/twiddly"
            target="_blank"
            size="small"
            color="orange">
            <Icon name="heart" />
            {t`Support on Patreon`}
          </Button>
          <Button
            as="a"
            href="https://ko-fi.com/twiddly"
            target="_blank"
            size="small"
            color="blue">
            <Icon name="coffee" />
            {t`Buy me a Coffee`}
          </Button>

          <Button
            as="a"
            href="https://github.com/happypandax"
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
                  <a href="https://github.com/twiddli" target="_blank">
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
                  <a href="https://twitter.com/twiddly_" target="_blank">
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
          <Button size="small">
            <Icon name="redo" />
            {t`Reindex library`}
          </Button>
          <Button size="small" floated="right">
            <Icon name="settings" />
            {t`Reset settings`}
          </Button>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
}

function StatsPane() {
  return <Segment basic></Segment>;
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
              key: 'statistics',
              icon: 'bar chart',
              content: t`Statistics`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <StatsPane />
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
  return (
    <Modal
      dimmer="inverted"
      closeIcon
      centered={false}
      {...props}
      className={classNames('min-300-h', className)}>
      <Modal.Content as={Segment} basic>
        <Header icon textAlign="center">
          <Icon name="info" circular />
          {t`About`}
        </Header>
        <AboutTab />
      </Modal.Content>
      <Segment
        attached="bottom"
        textAlign="center"
        secondary
        className="no-margins">
        {t`HappyPanda X is a cross platform manga/doujinshi manager made out of pure`}
        <Icon name="heart" color="red" size="large" />
        {t`by`} Twiddly
      </Segment>
    </Modal>
  );
}
