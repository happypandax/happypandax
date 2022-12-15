import { redirect } from 'next/navigation';
import { Divider, Grid } from 'semantic-ui-react';

import { ServiceType } from '../../services/constants';
import LoginSegment from './segment';

export default function Page({
  searchParams,
}: {
  params: { slug: string };
  searchParams?: { [key: string]: string | string[] | undefined };
}) {
  const server = global.app.service.get(ServiceType.Server);
  const next = searchParams?.next
    ? decodeURIComponent(searchParams?.next as string)
    : undefined;

  if (server.logged_in) {
    redirect(next ?? '/library');
  }

  return (
    <Grid
      className="main-content overflow-hidden"
      centered
      verticalAlign="middle">
      <Grid.Row>
        <Grid.Column
          className="animate__animated vanishIn"
          width="7"
          widescreen="3"
          largescreen="4"
          mobile="15"
          tablet="9"
          computer="7">
          <div className="mt-neg-25">
            <div className="center-text">
              <img src="/img/hpx_logo.svg" className="hpxlogo" alt="hpxlogo" />
            </div>
            <Divider hidden horizontal />
            <LoginSegment next={next} />
          </div>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
}
