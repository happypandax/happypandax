import { Segment, Grid, Divider } from 'semantic-ui-react';
import { PageTitle } from '../components/Misc';
import t from '../misc/lang';
import { LoginForm } from '../components/Login';

export default function Page() {
  return (
    <>
      <PageTitle title={t`Login`} />
      <Grid className="fullheight" centered verticalAlign="middle">
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
            <Segment clearing>
              <LoginForm />
            </Segment>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </>
  );
}
