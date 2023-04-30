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
      destination: '/management/metadata',
      permanent: false,
    },
    props: {},
  };
}
export default function ManagementPage({ children }: PageProps) {
  const router = useRouter();

  const path = router.pathname.split('/')?.[2];

  return (
    <PageLayout
      menu={useMemo(
        () => (
          <MainMenu secondary={false} tabular stackable>
            <Link href="/management/metadata" passHref>
              <MenuItem
                link
                icon="cloud"
                active={path === 'metadata'}>{t`Metadata`}</MenuItem>
            </Link>
            <Link href="/management/download" passHref>
              <MenuItem
                link
                icon="download"
                active={path === 'download'}>{t`Download`}</MenuItem>
            </Link>
            <Link href="/management/plugins" passHref>
              <MenuItem
                link
                icon="cubes"
                active={path === 'plugins'}>{t`Plugins`}</MenuItem>
            </Link>
            <Link href="/management/database" passHref>
              <MenuItem
                link
                icon="database"
                active={path === 'database'}>{t`Database`}</MenuItem>
            </Link>
            <Link href="/management/user" passHref>
              <MenuItem
                link
                icon="user"
                active={path === 'user'}>{t`User`}</MenuItem>
            </Link>
          </MainMenu>
        ),
        []
      )}>
      <PageTitle title={t`Management`} />
      {children}
    </PageLayout>
  );
}
