import Link from 'next/link';
import { useRouter } from 'next/router';
import { useMemo } from 'react';

import t from '../../client/lang';
import PageLayout from '../../components/layout/Page';
import MainMenu, { MenuItem } from '../../components/Menu';

interface PageProps {
  children?: React.ReactNode;
}

export async function getServerSideProps(context) {
  return {
    redirect: {
      destination: '/add/item',
      permanent: false,
    },
    props: {},
  };
}

export default function AddPage({ children }: PageProps) {
  const router = useRouter();

  const path = router.pathname.split('/')?.[2];

  return (
    <PageLayout
      menu={useMemo(
        () => (
          <MainMenu secondary={false} size="small" tabular stackable>
            <Link href="/add/item" passHref>
              <MenuItem link active={path === 'item'}>{t`New item`}</MenuItem>
            </Link>
            <Link href="/add/scan" passHref>
              <MenuItem
                link
                active={path === 'scan'}
              >{t`Scan directories`}</MenuItem>
            </Link>
          </MainMenu>
        ),
        []
      )}
    >
      {children}
    </PageLayout>
  );
}
