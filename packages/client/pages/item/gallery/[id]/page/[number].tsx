import { GetServerSidePropsResult, NextPageContext, Redirect } from 'next';
import dynamic from 'next/dynamic';
import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  GalleryCardData,
  galleryCardDataFields,
} from '../../../../../components/Gallery';
import PageLayout, {
  BottomZoneItem,
} from '../../../../../components/layout/Page';
import { PageTitle } from '../../../../../components/Misc';
import { ItemSort, ItemType } from '../../../../../misc/enums';
import t from '../../../../../misc/lang';
import { ServerGallery, ServerPage } from '../../../../../misc/types';
import { replaceURL, urlparse, urlstring } from '../../../../../misc/utility';
import { ServiceType } from '../../../../../services/constants';
import ServerService, { GroupCall } from '../../../../../services/server';

import type { ReaderData } from '../../../../../components/Reader';
const Reader = dynamic(() => import('../../../../../components/Reader'), {
  ssr: false,
});

const ReaderSettingsButton = dynamic(
  () =>
    import('../../../../../components/Reader').then(
      (m) => m.ReaderSettingsButton
    ),
  {
    ssr: false,
  }
);

const ReaderAutoNavigateButton = dynamic(
  () =>
    import('../../../../../components/Reader').then(
      (m) => m.ReaderAutoNavigateButton
    ),
  {
    ssr: false,
  }
);

const EndContent = dynamic(
  () => import('../../../../../components/Reader').then((m) => m.EndContent),
  {
    ssr: false,
  }
);

interface PageProps {
  item: DeepPick<ServerGallery, 'id'>;
  startPage: number;
  data: Unwrap<ServerService['pages']>;
  title: string;
  urlQuery: ReturnType<typeof urlparse>;
  sameArtist: GalleryCardData[];
  readingList: GalleryCardData[];
  randomItem?: GalleryCardData;
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
    redirect = {
      permanent: false,
      destination: urlstring(
        `/item/gallery/${itemId}/${startPage}`,
        urlQuery as any
      ),
      statusCode: 307,
    };
  }

  let data: PageProps['data'];
  let sameArtist: PageProps['sameArtist'] = [];
  let title = 'Gallery';
  let item: PageProps['item'];
  let randomItem: PageProps['randomItem'];

  // TODO: ensure it isn't lower than local window size or the page will error out
  const remoteWindowSize = 40;

  if (!redirect) {
    const group = new GroupCall();

    server
      .library<ServerGallery>(
        {
          item_type: ItemType.Gallery,
          metatags: { trash: false },
          sort_by: ItemSort.GalleryRandom,
          limit: 1,
        },
        group
      )
      .then((r) => {
        randomItem = r.items?.[0];
      });

    server
      .pages(
        {
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
        },
        group
      )
      .then((d) => {
        data = d;
      });

    server
      .item<ServerGallery>(
        {
          item_type: ItemType.Gallery,
          item_id: itemId,
          fields: ['preferred_title.name', 'artists.id'],
        },
        group
      )
      .then((r) => {
        console.log(r)
        item = r;
      });

    await group.call();

    const it = item as ServerGallery;

    if (it.preferred_title) {
      title = it.preferred_title.name;
    }

    if (it.artists.length) {
      const r = await server.related_items<ServerGallery>({
        item_id: it.artists.map((a) => a.id),
        item_type: ItemType.Artist,
        related_type: ItemType.Gallery,
        fields: galleryCardDataFields,
        limit: 50,
      });
      sameArtist = r.items.filter((g) => g.id !== itemId);
    }
  }

  console.log(sameArtist);

  return {
    redirect,
    props: { item, randomItem, sameArtist, data, startPage, urlQuery, title },
  };
}

export default function Page(props: PageProps) {
  const startPage = Math.min(props.startPage, props.data.count);
  const [number, setNumber] = useState(startPage);

  useEffect(() => {
    const u = urlparse();
    replaceURL(
      urlstring(`/item/gallery/${props.item.id}/page/${number}`, u.query as any)
    );
  }, [number]);

  const stateKey = 'page';

  return (
    <PageLayout
      basicDrawerButton
      bottomZone={useMemo(() => {
        return (
          <BottomZoneItem x="right" y="bottom">
            <ReaderAutoNavigateButton stateKey={stateKey} />
            <ReaderSettingsButton stateKey={stateKey} />
          </BottomZoneItem>
        );
      }, [stateKey])}>
      <PageTitle title={t`Page ${number}` + ' | ' + props.title} />
      <Reader
        item={props.item}
        pageCount={props.data.count}
        startPage={startPage}
        initialData={props.data.items as ServerPage[]}
        onPage={useCallback((page: ReaderData) => {
          setNumber(page.number);
        }, [])}
        stateKey={stateKey}>
        <EndContent random={props.randomItem} sameArtist={props.sameArtist} />
      </Reader>
    </PageLayout>
  );
}
