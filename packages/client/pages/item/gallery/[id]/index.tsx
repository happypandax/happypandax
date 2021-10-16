import { GetServerSidePropsResult, NextPageContext, Redirect } from 'next';
import { useCallback, useMemo, useState } from 'react';
import { Container, Grid, Icon, Label, Segment } from 'semantic-ui-react';

import { QueryType, useQueryType } from '../../../../client/queries';
import GalleryCard, {
  GalleryCardData,
  galleryCardDataFields,
} from '../../../../components/item/Gallery';
import PageCard, { pageCardDataFields } from '../../../../components/item/Page';
import {
  GalleryHeaderData,
  galleryHeaderDataFields,
  GalleryItemHeader,
  ItemMenu,
} from '../../../../components/layout/ItemLayout';
import PageLayout from '../../../../components/layout/Page';
import {
  PageTitle,
  SimilarItemsSlider,
  Slider,
  SliderElement,
} from '../../../../components/Misc';
import CardView from '../../../../components/view/CardView';
import ListView from '../../../../components/view/ListView';
import { ImageSize, ItemType } from '../../../../misc/enums';
import t from '../../../../misc/lang';
import {
  ServerGallery,
  ServerGrouping,
  ServerItem,
} from '../../../../misc/types';
import { urlparse } from '../../../../misc/utility';
import { ServiceType } from '../../../../services/constants';

interface PageProps {
  item: GalleryHeaderData;
  sameArtist: GalleryCardData[];
  series: GalleryCardData[];
  urlQuery: ReturnType<typeof urlparse>;
}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = global.app.service.get(ServiceType.Server);

  let redirect: Redirect;

  const itemId = parseInt(context.query.id as string);

  const urlQuery = urlparse(context.resolvedUrl);

  if (isNaN(itemId)) {
    redirect = { permanent: false, destination: '/library' };
  }

  let item: PageProps['item'];
  let sameArtist: PageProps['sameArtist'] = [];
  let series: PageProps['series'] = [];

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
    props: { item, sameArtist, series, urlQuery },
  };
}

export default function Page(props: PageProps) {
  const [page, setPage] = useState(1);

  const { data: pages, isLoading: pagesIsLoading } = useQueryType(
    QueryType.LIBRARY,
    {
      item_type: ItemType.Gallery,
      item_id: props.item.id,
      related_type: ItemType.Page,
      metatags: { trash: false },
      page: page - 1,
      limit: 50,
      fields: pageCardDataFields,
    }
  );

  const display = 'card';

  const onItemKey = useCallback((item: ServerItem) => item.id, []);
  const onPageChange = useCallback((ev, n) => {
    ev.preventDefault();
    setPage(n);
  }, []);

  return (
    <PageLayout
      menu={useMemo(
        () => (
          <ItemMenu data={props.item}></ItemMenu>
        ),
        [props.item]
      )}>
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
                  color="teal">
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
                color="blue">
                {props?.sameArtist?.map?.((i) => (
                  <SliderElement key={i.id}>
                    <GalleryCard size="small" data={i} />
                  </SliderElement>
                ))}
              </Slider>
            </Grid.Row>
            {!!props.sameArtist?.length && (
              <Grid.Row>
                <Slider
                  fluid
                  stateKey="gallery_collection_page"
                  label={t`Appears in ${0} collections`}
                  color="violet">
                  {props?.sameArtist?.map?.((i) => (
                    <SliderElement key={i.id}>
                      <GalleryCard size="small" data={i} />
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
              {display === 'card' && (
                <CardView
                  fluid
                  loading={pagesIsLoading}
                  activePage={page}
                  onPageChange={onPageChange}
                  items={pages?.data.items}
                  paddedChildren
                  itemRender={PageCard}
                  itemsPerPage={30}
                  onItemKey={onItemKey}
                  totalItemCount={pages?.data.count}
                  pagination={!!pages?.data.count}
                  bottomPagination={!!pages?.data.count}></CardView>
              )}
              {display === 'list' && (
                <ListView
                  fluid
                  loading={pagesIsLoading}
                  items={pages?.data.items}
                  onPageChange={onPageChange}
                  activePage={page}
                  onItemKey={onItemKey}
                  itemsPerPage={30}
                  itemRender={PageCard}
                  totalItemCount={pages?.data.count}
                  pagination={!!pages?.data.count}
                  bottomPagination={!!pages?.data.count}></ListView>
              )}
            </Grid.Row>
          </Grid>
        </Segment>
      </Container>
    </PageLayout>
  );
}
