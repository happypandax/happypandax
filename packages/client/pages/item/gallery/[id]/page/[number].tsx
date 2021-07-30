import { GetServerSidePropsResult, NextPageContext } from 'next';
import dynamic from 'next/dynamic';

import PageLayout from '../../../../../components/layout/Page';
import { ItemType } from '../../../../../misc/enums';
import { ServerPage } from '../../../../../misc/types';
import { urlparse } from '../../../../../misc/utility';
import { ServiceType } from '../../../../../services/constants';
import ServerService from '../../../../../services/server';

const Reader = dynamic(() => import('../../../../../components/Reader'));

interface PageProps {
  itemId: number;
  data: Unwrap<ServerService['related_items']>;
  urlQuery: ReturnType<typeof urlparse>;
}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = global.app.service.get(ServiceType.Server);

  const itemId = parseInt(context.query.id as string);

  console.log(context.query);

  const urlQuery = urlparse(context.resolvedUrl);

  const data = await server.related_items<ServerPage>({
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

  return {
    props: { itemId, data, urlQuery },
  };
}

export default function Page(props: PageProps) {
  return (
    <PageLayout>
      <Reader
        itemId={props.itemId}
        pageCount={props.data.count}
        initialData={props.data.items as ServerPage[]}
      />
    </PageLayout>
  );
}
