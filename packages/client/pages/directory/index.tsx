import Link from 'next/link';
import { useRouter } from 'next/router';
import { useMemo } from 'react';

import t from '../../client/lang';
import PageLayout from '../../components/layout/Page';
import MainMenu, { MenuItem } from '../../components/Menu';
import { PageTitle } from '../../components/misc';

interface PageProps {
  children?: React.ReactNode;
}

export async function getServerSideProps(context) {
  return {
    redirect: {
      destination: '/directory/filter',
      permanent: false,
    },
    props: {},
  };
}
export default function DirectoryPage({ children }: PageProps) {
  const router = useRouter();

  const path = router.pathname.split('/')?.[2];

  return (
    <PageLayout
      menu={useMemo(
        () => (
          <MainMenu
            secondary={false}
            size="small"
            tabular
            separateNavigation
            stackable
          >
            <Link href="/directory/filter" passHref>
              <MenuItem link active={path === 'filter'}>{t`Filters`}</MenuItem>
            </Link>
            <Link href="/directory/artist" passHref>
              <MenuItem active={path === 'artist'}>{t`Artists`}</MenuItem>
            </Link>
            <Link href="/directory/tag" passHref>
              <MenuItem link active={path === 'tag'}>{t`Tags`}</MenuItem>
            </Link>
            <Link href="/directory/parody" passHref>
              <MenuItem active={path === 'parody'}>{t`Parodies`}</MenuItem>
            </Link>
            <Link href="/directory/circle" passHref>
              <MenuItem active={path === 'circle'}>{t`Circles`}</MenuItem>
            </Link>
            <Link href="/directory/category" passHref>
              <MenuItem active={path === 'category'}>{t`Categories`}</MenuItem>
            </Link>
            <Link href="/directory/language" passHref>
              <MenuItem active={path === 'language'}>{t`Languages`}</MenuItem>
            </Link>
            <Link href="/directory/status" passHref>
              <MenuItem active={path === 'status'}>{t`Status`}</MenuItem>
            </Link>
          </MainMenu>
        ),
        []
      )}
    >
      <PageTitle title={t`Directory`} />
      {children}
    </PageLayout>
  );
}
