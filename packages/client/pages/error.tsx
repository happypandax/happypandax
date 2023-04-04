import { Grid, Header, Icon } from 'semantic-ui-react';

import t from '../client/lang';
import PageLayout from '../components/layout/Page';

export default function Page() {
  return (
    <PageLayout>
      <Grid
        className="main-content overflow-hidden"
        centered
        verticalAlign="middle"
      >
        <Grid.Row>
          <Grid.Column
            width="7"
            widescreen="3"
            largescreen="4"
            mobile="15"
            tablet="9"
            computer="7"
          >
            <div className="mt-neg-25">
              <div className="center-text">
                <Header size="huge" icon>
                  <Icon className="hpx-standard sub-text" size="huge" />
                  {t`ERROR`}
                  <Header.Subheader>{t`Momo found an error!`}</Header.Subheader>
                </Header>
              </div>
            </div>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </PageLayout>
  );
}
