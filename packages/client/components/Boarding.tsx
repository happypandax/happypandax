import {
  Segment,
  Grid,
  Divider,
  Header,
  Label,
  Button,
} from 'semantic-ui-react';
import Image from 'next/image';
import t from '../misc/lang';

function Step({
  children,
  number,
  title,
}: {
  children?: React.ReactNode;
  number: React.ReactNode;
  title: React.ReactNode;
}) {
  return (
    <Grid.Row>
      <Grid.Column width="1">
        <Label color="blue">{number}</Label>
      </Grid.Column>
      <Grid.Column width="15">
        <Header as="h2" className="center-text">
          {title}
        </Header>
        {children}
      </Grid.Column>
    </Grid.Row>
  );
}

export default function Setup() {
  return (
    <Grid
      className="min-fullheight animate__animated animate__fadeInUp"
      centered
      verticalAlign="middle"
      as={Segment}>
      <Grid.Row>
        <Grid.Column
          width="7"
          widescreen="3"
          largescreen="4"
          mobile="15"
          tablet="9"
          computer="7">
          <div className="center-text">
            <img src="/img/hpx_logo.svg" className="hpxlogo" alt="hpxlogo" />
          </div>
          <Divider hidden horizontal />
          <Header as="h1" className="center-text">
            Setup Guide
          </Header>
        </Grid.Column>
      </Grid.Row>
      <Step number="1" title={t`Choose a backend`}></Step>
      <Step number="1" title={t`Manage users`}></Step>
      <Step number="2" title={t`Install plugins`}></Step>
      <Step number="3" title={t`Import galleries`}></Step>
      <Step number="4" title={t`Fetch metadata`}></Step>
      <Step number="5" title={t`and a word from Momo-chan...`}>
        <div className="center-text">
          <img src="/img/masturbated.png" height={500} />
        </div>
        <div className="center-text">
          <Button size="large" color="green">{t`Thanks!`}</Button>
        </div>
      </Step>
    </Grid>
  );
}
