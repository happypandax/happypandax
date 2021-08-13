import { GetServerSidePropsResult, NextPageContext, Redirect } from 'next';
import { useRouter } from 'next/dist/client/router';
import { useMemo } from 'react';
import { Container, Grid, Segment } from 'semantic-ui-react';

import GalleryCard, {
  GalleryCardData,
  galleryCardDataFields,
} from '../../../../components/Gallery';
import {
  GalleryHeaderData,
  galleryHeaderDataFields,
  GalleryItemHeader,
  ItemMenu,
} from '../../../../components/layout/ItemLayout';
import PageLayout from '../../../../components/layout/Page';
import { Slider } from '../../../../components/Misc';
import { ImageSize, ItemType } from '../../../../misc/enums';
import t from '../../../../misc/lang';
import { ServerGallery, ServerGrouping } from '../../../../misc/types';
import { urlparse, urlstring } from '../../../../misc/utility';
import { ServiceType } from '../../../../services/constants';
import ServerService from '../../../../services/server';

interface PageProps {
  item: GalleryHeaderData;
  sameArtist: GalleryCardData[];
  pages: Unwrap<ServerService['library']>;
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
  let pages: PageProps['pages'];

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

    // server
    //   .library<ServerPage>({
    //     item_type: ItemType.Gallery,
    //     item_id: itemId,
    //     related_type: ItemType.Page,
    //     metatags: { trash: false },
    //     page: urlQuery.query?.pp as number,
    //     limit: urlQuery.query?.pplimit as number,
    //     fields: [],
    //   })
    //   .then((r) => {
    //     pages = r;
    //   });

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
    props: { item, sameArtist, series, urlQuery, pages },
  };
}

export default function Page(props: PageProps) {
  const router = useRouter();

  const display = 'card';

  const pageHrefTemplate = useMemo(
    () => urlstring(router.asPath, { pp: '${page}' }, { encode: false }),
    [router.query]
  );

  return (
    <PageLayout
      menu={useMemo(
        () => (
          <ItemMenu data={props.item}></ItemMenu>
        ),
        [props.item]
      )}>
      <GalleryItemHeader data={props.item} />
      <Container>
        <Segment basic>
          <Grid>
            {!!props.series?.length && (
              <Grid.Row>
                <Slider stateKey="series_page" label={t`Series`} color="teal">
                  {props?.series?.map?.((i) => (
                    <GalleryCard key={i.id} size="small" data={i} />
                  ))}
                </Slider>
              </Grid.Row>
            )}
            <Grid.Row>
              <Slider
                stateKey="same_artist_page"
                label={t`From same artist`}
                color="blue">
                {props?.sameArtist?.map?.((i) => (
                  <GalleryCard key={i.id} size="small" data={i} />
                ))}
              </Slider>
            </Grid.Row>
            <Grid.Row>
              <Slider
                autoplay
                stateKey="similar_page"
                label={t`Just like this one`}></Slider>
            </Grid.Row>
            {/* <Grid.Row>
            {display === 'card' && (
              <CardView
                hrefTemplate={pageHrefTemplate}
                activePage={props.urlQuery.query?.p}
                items={props.pages.items}
                paddedChildren
                itemRender={GalleryCard}
                itemsPerPage={30}
                onItemKey={onItemKey}
                totalItemCount={items.count}
                pagination={!!items.count}
                bottomPagination={!!items.count}></CardView>
            )}
            {display === 'list' && (
              <ListView
                hrefTemplate={pageHrefTemplate}
                items={items.items}
                activePage={urlQuery.query?.p}
                onItemKey={onItemKey}
                itemsPerPage={itemCount}
                itemRender={GalleryCard}
                totalItemCount={items.count}
                pagination={!!items.count}
                bottomPagination={!!items.count}></ListView>
            )}
          </Grid.Row> */}
          </Grid>
        </Segment>
      </Container>
    </PageLayout>
  );
}
