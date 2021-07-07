import { useRouter } from 'next/dist/client/router';
import { useCallback } from 'react';
import { useRecoilValue, useSetRecoilState } from 'recoil';
import { Divider, Grid, Segment } from 'semantic-ui-react';

import { LoginForm } from '../components/Login';
import { PageTitle } from '../components/Misc';
import t from '../misc/lang';
import { AppState } from '../state';

export default function Page() {
  const home = useRecoilValue(AppState.home);
  const setLoggedIn = useSetRecoilState(AppState.loggedIn);

  const router = useRouter();

  return (
    <>
      <PageTitle title={t`Login`} />
      <Grid
        className="fullheight overflow-hidden"
        centered
        verticalAlign="middle">
        <Grid.Row>
          <Grid.Column
            className="animate__animated animate__fadeInDown"
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
              <LoginForm
                onSuccess={useCallback(() => {
                  setLoggedIn(true);

                  const next_path = router?.query?.next
                    ? decodeURI(router?.query?.next as string)
                    : home;

                  if (next_path) {
                    router.replace(next_path, undefined, { shallow: true });
                  }
                }, [home])}
              />
            </Segment>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </>
  );
}
