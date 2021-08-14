import { GetServerSidePropsResult, NextPageContext } from 'next';
import { useRouter } from 'next/dist/client/router';
import { useCallback, useEffect } from 'react';
import { useRecoilValue, useSetRecoilState } from 'recoil';
import { Divider, Grid, Segment } from 'semantic-ui-react';

import { LoginForm } from '../components/Login';
import { PageTitle } from '../components/Misc';
import t from '../misc/lang';
import { ServiceType } from '../services/constants';
import { AppState } from '../state';

interface PageProps {
  next: string;
}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<{}>> {
  const server = global.app.service.get(ServiceType.Server);
  const next = context.query?.next
    ? decodeURI(context?.query?.next as string)
    : undefined;

  return {
    props: { next },
    redirect: server.logged_in
      ? { permanent: false, destination: next ?? '/library' }
      : undefined,
  };
}

export default function Page({ next }: PageProps) {
  const home = useRecoilValue(AppState.home);
  const setLoggedIn = useSetRecoilState(AppState.loggedIn);

  const router = useRouter();

  useEffect(() => {
    if (next) {
      router.prefetch(next);
    }
  }, [next]);

  return (
    <>
      <PageTitle title={t`Login`} />
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
                <img
                  src="/img/hpx_logo.svg"
                  className="hpxlogo"
                  alt="hpxlogo"
                />
              </div>
              <Divider hidden horizontal />
              <Segment clearing>
                <LoginForm
                  onSuccess={useCallback(() => {
                    setLoggedIn(true);

                    if (next) {
                      router.replace(next, undefined);
                    }
                  }, [home, next])}
                />
              </Segment>
            </div>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </>
  );
}
