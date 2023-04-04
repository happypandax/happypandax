import { GetServerSidePropsResult, NextPageContext, Redirect } from 'next';
import { useCallback, useMemo, useState } from 'react';
import { Container, Grid, Icon, Label, Segment } from 'semantic-ui-react';

import { useUpdateRecentlyViewedItem } from '../../../../client/hooks/item';
import t from '../../../../client/lang';
import { QueryType, useQueryType } from '../../../../client/queries';
import CollectionCard, {
  CollectionCardData,
  collectionCardDataFields,
} from '../../../../components/item/Collection';
import GalleryCard, {
  GalleryCardData,
  galleryCardDataFields,
} from '../../../../components/item/Gallery';
import PageCard, { pageCardDataFields } from '../../../../components/item/Page';
import {
  GalleryHeaderData,
  galleryHeaderDataFields,
  GalleryItemHeader,
} from '../../../../components/layout/GalleryLayout';
import { ItemMenu } from '../../../../components/layout/ItemLayout';
import PageLayout from '../../../../components/layout/Page';
import { PageTitle } from '../../../../components/misc';
import {
  SimilarItemsSlider,
  Slider,
  SliderElement,
} from '../../../../components/misc/Slider';
import CardView from '../../../../components/view/CardView';
import ListView from '../../../../components/view/ListView';
import { ServiceType } from '../../../../server/constants';
import { ImageSize, ItemType } from '../../../../shared/enums';
import {
  ServerCollection,
  ServerGallery,
  ServerGrouping,
  ServerItem,
} from '../../../../shared/types';
import { urlparse } from '../../../../shared/utility';

interface PageProps {
  item: GalleryHeaderData;
  sameArtist: GalleryCardData[];
  collections: CollectionCardData[];
  series: GalleryCardData[];
  urlQuery: ReturnType<typeof urlparse>;
}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context(context);

  let redirect: Redirect;

  const itemId = parseInt(context.query.id as string);

  const urlQuery = urlparse(context.resolvedUrl);

  if (isNaN(itemId)) {
    redirect = { permanent: false, destination: '/library' };
  }

  let item: PageProps['item'];
  let sameArtist: PageProps['sameArtist'] = [];
  let series: PageProps['series'] = [];
  let collections: PageProps['collections'] = [];

  if (!redirect) {
    const group = server.create_group_call();

    server
      .item<ServerGallery>(
        {
          item_type: ItemType.Gallery,
          item_id: itemId,
          fields: galleryHeaderDataFields,
          profile_options: {
            size: ImageSize.Big,
          },
        },
        group
      )
      .then((r) => {
        item = r;
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
      .related_items<ServerCollection>(
        {
          item_id: itemId,
          item_type: ItemType.Gallery,
          related_type: ItemType.Collection,
          fields: collectionCardDataFields,
        },
        group
      )
      .then((r) => {
        collections = r.items;
      });

    await group.call();

    if (item.artists?.length) {
      const r = await server.related_items<ServerGallery>({
        item_id: item.artists.map((a) => a.id),
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
    props: { item, sameArtist, series, urlQuery, collections },
  };
}

export default function Page(props: PageProps) {
  const display = 'card';
  const pagesLimit = 50;

  useUpdateRecentlyViewedItem(props.item?.id, ItemType.Gallery);

  const [page, setPage] = useState(1);

  const { data: pages, isLoading: pagesIsLoading } = useQueryType(
    QueryType.LIBRARY,
    {
      item_type: ItemType.Gallery,
      item_id: props.item.id,
      related_type: ItemType.Page,
      metatags: { trash: false },
      page: page - 1,
      limit: pagesLimit,
      fields: pageCardDataFields,
    },
    { keepPreviousData: true }
  );

  const onItemKey = useCallback((item: ServerItem) => item.id, []);
  const onPageChange = useCallback((ev, n) => {
    ev.preventDefault();
    setPage(n);
  }, []);

  const View = display === 'card' ? CardView : ListView;

  const collectionCount = props?.collections?.length;

  return (
    <PageLayout
      menu={useMemo(
        () => (
          <ItemMenu data={props.item} type={ItemType.Gallery}></ItemMenu>
        ),
        [props.item]
      )}
    >
      <PageTitle title={props?.item?.preferred_title?.name} />
      <GalleryItemHeader data={props.item} />
      <Container>
        <Segment basic>
          <Grid>
            {!!props.series?.length && (
              <Grid.Row>
                <Slider
                  fluid
                  stateKey="series_page"
                  label={t`Series`}
                  color="teal"
                >
                  {props?.series?.map?.((i) => (
                    <SliderElement key={i.id}>
                      <GalleryCard size="small" data={i} />
                    </SliderElement>
                  ))}
                </Slider>
              </Grid.Row>
            )}
            <Grid.Row>
              <Slider
                fluid
                stateKey="same_artist_page"
                label={t`From same artist`}
                defaultShow={!!props?.sameArtist?.length}
                color="blue"
              >
                {props?.sameArtist?.map?.((i) => (
                  <SliderElement key={i.id}>
                    <GalleryCard size="small" data={i} />
                  </SliderElement>
                ))}
              </Slider>
            </Grid.Row>
            {!!props.collections?.length && (
              <Grid.Row>
                <Slider
                  fluid
                  stateKey="gallery_collection_page"
                  showCount={false}
                  label={t`Appears in ${collectionCount} collections`}
                  color="violet"
                >
                  {props?.collections?.map?.((i) => (
                    <SliderElement key={i.id}>
                      <CollectionCard size="small" data={i} />
                    </SliderElement>
                  ))}
                </Slider>
              </Grid.Row>
            )}
            <Grid.Row>
              <SimilarItemsSlider
                fluid
                stateKey="similar_page"
                item={props.item}
                type={ItemType.Gallery}
              />
            </Grid.Row>
            <Grid.Row as={Segment} basic id="pages">
              <Label attached="top">
                <Icon name="clone outline" />
                {t`Pages`}
                <Label.Detail>{pages?.data.count}</Label.Detail>
              </Label>
              <View
                fluid
                loading={pagesIsLoading}
                activePage={page}
                onPageChange={onPageChange}
                items={pages?.data.items}
                paddedChildren
                itemRender={PageCard}
                itemsPerPage={pagesLimit}
                onItemKey={onItemKey}
                totalItemCount={pages?.data.count}
                pagination={!!pages?.data.count}
                bottomPagination={!!pages?.data.count}
              />
            </Grid.Row>
          </Grid>
        </Segment>
      </Container>
    </PageLayout>
  );
}
