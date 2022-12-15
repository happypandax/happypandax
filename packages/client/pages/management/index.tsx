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
      destination: '/management/database',
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
          <MainMenu secondary={false} size="small" tabular>
            <Link href="/management/database" passHref>
              <MenuItem
                link
                active={path === 'database'}>{t`Database`}</MenuItem>
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
