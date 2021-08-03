import { GetServerSidePropsResult, NextPageContext, Redirect } from 'next';
import dynamic from 'next/dynamic';

import PageLayout from '../../../../../components/layout/Page';
import { ItemType } from '../../../../../misc/enums';
import { ServerPage } from '../../../../../misc/types';
import { urlparse } from '../../../../../misc/utility';
import { ServiceType } from '../../../../../services/constants';
import ServerService from '../../../../../services/server';

const Reader = dynamic(() => import('../../../../../components/Reader'), {
  ssr: false,
});

interface PageProps {
  itemId: number;
  startPage: number;
  data: Unwrap<ServerService['related_items']>;
  urlQuery: ReturnType<typeof urlparse>;
}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = global.app.service.get(ServiceType.Server);

  let redirect: Redirect;

  const itemId = parseInt(context.query.id as string);

  if (isNaN(itemId)) {
    redirect = { permanent: false, destination: '/library', statusCode: 307 };
  }

  const urlQuery = urlparse(context.resolvedUrl);

  let startPage = parseInt(context.query.number as string);

  if (isNaN(startPage)) {
    startPage = 1;
  }

  let data: Unwrap<ServerService['related_items']>;

  if (!redirect) {
    data = await server.related_items<ServerPage>({
      item_id: itemId,
      item_type: ItemType.Gallery,
      related_type: ItemType.Page,
      limit: 0,
      fields: [
        'id',
        'name',
        'number',
        'metatags.favorite',
        'metatags.inbox',
        'metatags.trash',
        'path',
      ],
    });
  }

  return {
    redirect,
    props: { itemId, data, startPage, urlQuery },
  };
}

export default function Page(props: PageProps) {
  return (
    <PageLayout>
      <Reader
        itemId={props.itemId}
        pageCount={props.data.count}
        startPage={props.startPage}
        initialData={props.data.items as ServerPage[]}
      />
    </PageLayout>
  );
}
