import { GetServerSidePropsResult, NextPageContext, Redirect } from 'next';
import { useRouter } from 'next/dist/client/router';
import dynamic from 'next/dynamic';
import { useCallback, useState } from 'react';

import PageLayout from '../../../../../components/layout/Page';
import { PageTitle } from '../../../../../components/Misc';
import { ItemType } from '../../../../../misc/enums';
import t from '../../../../../misc/lang';
import { ServerGallery, ServerPage } from '../../../../../misc/types';
import { replaceURL, urlparse, urlstring } from '../../../../../misc/utility';
import { ServiceType } from '../../../../../services/constants';
import ServerService from '../../../../../services/server';

import type { ReaderData } from '../../../../../components/Reader';
const Reader = dynamic(() => import('../../../../../components/Reader'), {
  ssr: false,
});

interface PageProps {
  itemId: number;
  startPage: number;
  data: Unwrap<ServerService['pages']>;
  title: string;
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

  console.log(context.query);

  if (isNaN(startPage)) {
    startPage = 1;
  }

  let data: Unwrap<ServerService['pages']>;
  let title = 'Gallery';

  // TODO: ensure it isn't lower than local window size or the page will error out
  const remoteWindowSize = 40;

  if (!redirect) {
    const gallery = await server.item<ServerGallery>({
      item_type: ItemType.Gallery,
      item_id: itemId,
      fields: ['preferred_title.name'],
    });
    if (gallery.preferred_title) {
      title = gallery.preferred_title.name;
    }

    data = await server.pages({
      gallery_id: itemId,
      window_size: remoteWindowSize,
      number: startPage,
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
    props: { itemId, data, startPage, urlQuery, title },
  };
}

export default function Page(props: PageProps) {
  const router = useRouter();
  const [number, setNumber] = useState(props.startPage);

  const onPage = useCallback((page: ReaderData) => {
    const u = urlparse();
    replaceURL(
      urlstring(
        `/item/gallery/${props.itemId}/page/${page.number}`,
        u.query as any
      )
    );
    setNumber(page.number);
  }, []);

  return (
    <PageLayout>
      <PageTitle title={t`Page ${number}` + ' | ' + props.title} />
      <Reader
        itemId={props.itemId}
        pageCount={props.data.count}
        startPage={props.startPage}
        initialData={props.data.items as ServerPage[]}
        onPage={onPage}
      />
    </PageLayout>
  );
}
