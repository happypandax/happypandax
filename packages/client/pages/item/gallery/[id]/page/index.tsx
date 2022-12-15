import { GetServerSidePropsResult, NextPageContext } from 'next';

import { urlstring } from '../../../../../shared/utility';

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<{}>> {
  return {
    redirect: {
      permanent: false,
      destination: urlstring(`/item/gallery/${context.query.id}/page/1`, {
        ...context.query,
        id: undefined,
      } as any),
    },
  };
}

export default function Page() {}
