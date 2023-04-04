'use client';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect } from 'react';
import { useRecoilValue } from 'recoil';
import { Divider, Grid, Segment } from 'semantic-ui-react';

import { LoginForm } from '../../components/Login';
import { AppState } from '../../state';
import { useSetGlobalState } from '../../state/global';

export default function LoginSegment({ next }: { next: string }) {
  const home = useRecoilValue(AppState.home);
  const setLoggedIn = useSetGlobalState('loggedIn');

  const router = useRouter();

  useEffect(() => {
    if (next) {
      router.prefetch(next);
    }
  }, [next]);

  return (
    <Grid
      className="main-content overflow-hidden"
      centered
      verticalAlign="middle"
    >
      <Grid.Row>
        <Grid.Column
          className="animate__animated vanishIn"
          width="7"
          widescreen="3"
          largescreen="4"
          mobile="15"
          tablet="9"
          computer="7"
        >
          <div className="mt-neg-25">
            <div className="center-text">
              <img src="/img/hpx_logo.svg" className="hpxlogo" alt="hpxlogo" />
            </div>
            <Divider hidden horizontal />
            <Segment clearing>
              <LoginForm
                onSuccess={useCallback(() => {
                  setLoggedIn(true);

                  if (next) {
                    // router.replace doesn't work, idk why
                    router.replace(next);
                  }
                }, [home, next])}
              />
            </Segment>
          </div>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
}
