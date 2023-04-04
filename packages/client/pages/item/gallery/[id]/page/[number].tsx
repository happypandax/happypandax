import { GetServerSidePropsResult, NextPageContext, Redirect } from 'next';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Button, Container, Icon } from 'semantic-ui-react';

import { ReaderContext } from '../../../../../client/context';
import { useHijackHistory } from '../../../../../client/hooks/ui';
import t from '../../../../../client/lang';
import { getCookies, replaceURL } from '../../../../../client/utility';
import {
  CollectionCardData,
  collectionCardDataFields,
} from '../../../../../components/item/Collection';
import {
  GalleryCardData,
  galleryCardDataFields,
} from '../../../../../components/item/Gallery';
import PageLayout, {
  BottomZoneItem,
} from '../../../../../components/layout/Page';
import { PageTitle } from '../../../../../components/misc';
import { ServiceType } from '../../../../../server/constants';
import ServerService, { GroupCall } from '../../../../../services/server';
import { ItemSort, ItemType } from '../../../../../shared/enums';
import {
  ReaderData,
  ServerCollection,
  ServerGallery,
  ServerGrouping,
  ServerPage,
} from '../../../../../shared/types';
import { JSONSafe, urlparse, urlstring } from '../../../../../shared/utility';
import { ReaderState } from '../../../../../state';
import { useInitialRecoilState } from '../../../../../state/index';

const Reader = dynamic(
  () => import('../../../../../components/reader/Reader'),
  {
    ssr: false,
  }
);

const ReaderSettingsButton = dynamic(
  () =>
    import('../../../../../components/reader/ReaderSettings').then(
      (m) => m.ReaderSettingsButton
    ),
  {
    ssr: false,
  }
);

const ReaderAutoNavigateButton = dynamic(
  () =>
    import('../../../../../components/reader/Misc').then(
      (m) => m.ReaderAutoNavigateButton
    ),
  {
    ssr: false,
  }
);

const ReaderAutoScrollButton = dynamic(
  () =>
    import('../../../../../components/reader/Misc').then(
      (m) => m.ReaderAutoScrollButton
    ),
  {
    ssr: false,
  }
);

const EndContent = dynamic(
  () =>
    import('../../../../../components/reader/EndContent').then(
      (m) => m.default
    ),
  {
    ssr: false,
  }
);

const PageInfoPortal = dynamic(
  () =>
    import('../../../../../components/reader/Misc').then(
      (m) => m.PageInfoPortal
    ),
  {
    ssr: false,
  }
);

interface PageProps {
  item: GalleryCardData;
  startPage: number;
  data: Unwrap<ServerService['pages']>;
  title: string;
  urlQuery: ReturnType<typeof urlparse>;
  sameArtist: GalleryCardData[];
  series: GalleryCardData[];
  collections: CollectionCardData[];
  randomItem?: DeepPick<ServerGallery, 'id'>;
  randomItems?: GalleryCardData[];
  nextChapter?: GalleryCardData;
}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context(context);

  let redirect: Redirect;

  const itemId = parseInt(context.query.id as string);

  if (isNaN(itemId)) {
    redirect = { permanent: false, destination: '/library' };
  }

  const urlQuery = urlparse(context.resolvedUrl);

  let startPage = parseInt(context.query.number as string);

  if (isNaN(startPage)) {
    startPage = 1;
    redirect = {
      permanent: false,
      destination: urlstring(
        `/item/gallery/${itemId}/page/${startPage}`,
        urlQuery.query as any
      ),
    };
  }

  let data: PageProps['data'];
  let sameArtist: PageProps['sameArtist'] = [];
  let title = 'Gallery';
  let item: PageProps['item'];
  let randomItem: PageProps['randomItem'];
  let randomItems: PageProps['randomItems'];
  let nextChapter: PageProps['nextChapter'];
  let collections: PageProps['collections'];
  let series: PageProps['series'];

  // TODO: ensure it isn't lower than local window size or the page will error out
  const remoteWindowSize = 40;

  if (!redirect) {
    const collectionCategories = getCookies(
      context,
      'collection_categories'
    ) as string[] | undefined;

    const group = new GroupCall();

    server
      .from_grouping(
        {
          gallery_id: itemId,
          fields: galleryCardDataFields,
        },
        group
      )
      .then((r) => {
        if (r) {
          nextChapter = r;
        }
      });

    server
      .library<ServerCollection>(
        {
          item_type: ItemType.Collection,
          metatags: { trash: false, inbox: false },
          sort_options: { by: ItemSort.CollectionName },
          limit: 50,
          search_query: collectionCategories?.length
            ? collectionCategories.reduce((p, c) => p + `category:"${c}" `, '')
            : undefined,
          search_options: {
            match_exact: true,
            match_all_terms: false,
            case_sensitive: true,
          },
          fields: collectionCardDataFields,
        },
        group
      )
      .then((r) => {
        collections = r.items;
      });

    server
      .related_items<ServerGrouping>(
        {
          item_id: itemId,
          item_type: ItemType.Gallery,
          related_type: ItemType.Grouping,
          fields: galleryCardDataFields.map((f) => 'galleries.' + f),
        },
        group
      )
      .then((r) => {
        series = r.items?.[0]?.galleries?.filter((g) => g.id !== itemId);
      });

    server
      .library<ServerGallery>(
        {
          item_type: ItemType.Gallery,
          metatags: { trash: false },
          sort_options: { by: ItemSort.GalleryRandom },
          limit: 4,
          fields: galleryCardDataFields,
        },
        group
      )
      .then((r) => {
        randomItem = r.items?.[0];
        randomItems = r.items?.slice(1);
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
      .item<GalleryCardData>(
        {
          item_type: ItemType.Gallery,
          item_id: itemId,

          fields: galleryCardDataFields.concat(['artists.id', 'grouping_id']),
        },
        group
      )
      .then((r) => {
        item = r;
      });

    await group.call();

    const it = item as GalleryCardData;

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

  return {
    redirect,
    props: JSONSafe({
      item,
      collections,
      series,
      randomItem,
      randomItems,
      nextChapter,
      sameArtist,
      data,
      startPage,
      urlQuery,
      title,
    }),
  };
}

export default function Page(props: PageProps) {
  const stateKey = 'page';
  const startPage = Math.min(props.startPage, props.data.count);
  const [number, setNumber] = useState(startPage);

  useEffect(() => {
    const u = urlparse();
    replaceURL(
      urlstring(`/item/gallery/${props.item.id}/page/${number}`, u.query as any)
    );
  }, [number]);

  const [infoOpen, setInfoOpen] = useInitialRecoilState(
    ReaderState.pageInfoOpen(stateKey),
    false
  );

  useHijackHistory(
    infoOpen,
    useCallback(() => setInfoOpen(false), [])
  );

  return (
    <ReaderContext.Provider
      value={useMemo(
        () => ({ item: props.item, stateKey }),
        [props.item, stateKey]
      )}
    >
      <PageLayout
        basicDrawerButton
        bottomZoneLeftBottom={useMemo(
          () => (
            <Link href={`/item/gallery/${props.item.id}`} passHref>
              <Button
                as="a"
                icon={{ name: 'level up alternate', flipped: 'horizontally' }}
                circular
                color="blue"
                basic
              />
            </Link>
          ),
          [props.item]
        )}
        bottomZone={useMemo(() => {
          return (
            <>
              <BottomZoneItem x="right" y="bottom">
                <ReaderAutoScrollButton />
                <ReaderAutoNavigateButton />
                <ReaderSettingsButton />
              </BottomZoneItem>
              <BottomZoneItem x="center" y="bottom">
                <Button basic onClick={() => setInfoOpen(true)}>
                  <Icon name="info circle" /> {t`Info`}
                </Button>
              </BottomZoneItem>
            </>
          );
        }, [])}
      >
        <PageTitle title={t`Page ${number}` + ' | ' + props.title} />
        <Reader
          pageCount={props.data.count}
          startPage={startPage}
          initialData={props.data.items as ServerPage[]}
          onPage={useCallback((page: ReaderData) => {
            setNumber(page.number);
          }, [])}
        >
          <Container textAlign="center">
            <EndContent
              series={props.series}
              collections={props.collections}
              nextChapter={props.nextChapter}
              random={props.randomItem}
              randomItems={props.randomItems}
              sameArtist={props.sameArtist}
            />
          </Container>
        </Reader>
        <PageInfoPortal
          container
          item={props.item}
          open={infoOpen}
          onClose={useCallback(() => setInfoOpen(false), [])}
        />
      </PageLayout>
    </ReaderContext.Provider>
  );
}
