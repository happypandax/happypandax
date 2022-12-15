'use client';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect } from 'react';
import { useRecoilValue } from 'recoil';
import { Segment } from 'semantic-ui-react';

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
  );
}
