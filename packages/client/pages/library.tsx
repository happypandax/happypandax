import { GetServerSidePropsResult, NextPageContext } from 'next';
import Router, { useRouter } from 'next/router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useEffectOnce, useUpdateEffect } from 'react-use';
import { useRecoilState, useRecoilValue, useSetRecoilState } from 'recoil';
import { Message } from 'semantic-ui-react';

import { LibraryContext } from '../client/context';
import { QueryType, useQueryType } from '../client/queries';
import { GalleryDataTable } from '../components/DataTable';
import GalleryCard, { galleryCardDataFields } from '../components/Gallery';
import {
  ClearFilterButton,
  FilterButtonInput,
  OnlyFavoritesButton,
  SortButtonInput,
  SortOrderButton,
  ViewButtons,
} from '../components/layout/ItemLayout';
import PageLayout, { BottomZoneItem } from '../components/layout/Page';
import MainMenu, { MenuItem } from '../components/Menu';
import {
  EmptySegment,
  PageInfoMessage,
  PageTitle,
  Visible,
} from '../components/Misc';
import { StickySidebar } from '../components/Sidebar';
import CardView from '../components/view/CardView';
import ListView from '../components/view/ListView';
import { ItemType } from '../misc/enums';
import t from '../misc/lang';
import { ServerGallery, ServerItem } from '../misc/types';
import { urlparse, urlstring } from '../misc/utility';
import { ServiceType } from '../services/constants';
import ServerService from '../services/server';
import { LibraryState } from '../state';

interface PageProps {
  data: Unwrap<ServerService['library']>;
  itemType: ItemType;
  urlQuery: ReturnType<typeof urlparse>;
}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = global.app.service.get(ServiceType.Server);

  const urlQuery = urlparse(context.resolvedUrl);

  let itemType = ItemType.Gallery;

  // can't trust user input
  if (urlQuery.query?.t === ItemType.Collection) {
    itemType = ItemType.Collection;
  }

  const group = server.create_group_call();

  const data = await server.library<ServerGallery>({
    item_type: itemType,
    metatags: { favorite: urlQuery.query?.fav as boolean, trash: false },
    page: urlQuery.query?.p as number,
    sort_options: {
      by: urlQuery.query?.sort as number,
      desc: urlQuery.query?.desc as boolean,
    },
    filter_id: urlQuery.query?.filter as number,
    limit: urlQuery.query?.limit as number,
    fields: galleryCardDataFields,
  });

  return {
    props: { data, urlQuery, itemType },
  };
}

function FilterPageMessage({ filterId }: { filterId: number }) {
  const { data, isLoading } = useQueryType(QueryType.ITEM, {
    item_type: ItemType.Filter,
    item_id: filterId,
    fields: ['name', 'info', 'filter'],
  });

  const setFilter = useSetRecoilState(LibraryState.filter);

  return (
    <PageInfoMessage
      hidden={isLoading}
      color="blue"
      size="tiny"
      onDismiss={useCallback(() => setFilter(undefined), [])}>
      <Message.Header className="text-center">
        {t`Filter`}: {data?.data?.name}
      </Message.Header>
      <Message.Content className="sub-text">
        {data?.data?.info || data?.data?.filter}
      </Message.Content>
    </PageInfoMessage>
  );
}

function LibrarySidebar() {
  const [sidebarVisible, setSidebarVisible] = useRecoilState(
    LibraryState.sidebarVisible
  );
  const sidebarData = useRecoilValue(LibraryState.sidebarData);

  return (
    <StickySidebar
      className="sticky-page-sidebar"
      visible={sidebarVisible}
      onHide={useCallback(() => {
        setSidebarVisible(false);
      }, [])}>
      {sidebarData && <GalleryDataTable data={sidebarData} />}
    </StickySidebar>
  );
}

export default function Page({ data, urlQuery, itemType }: PageProps) {
  const [item, setItem] = useRecoilState(LibraryState.item);
  const [view, setView] = useRecoilState(LibraryState.view);
  const [favorites, setFavorites] = useRecoilState(LibraryState.favorites);
  const [filter, setFilter] = useRecoilState(LibraryState.filter);
  const [sort, setSort] = useRecoilState(LibraryState.sort);
  const [sortDesc, setSortDesc] = useRecoilState(LibraryState.sortDesc);
  const display = useRecoilValue(LibraryState.display);
  const itemCount = useRecoilValue(LibraryState.itemCount);

  const router = useRouter();

  // TODO: replace with useQuery with initialData?
  const [items, setItems] = useState(data);

  useEffect(() => {
    setItems(data);
  }, [data]);

  useEffectOnce(() => {
    setFavorites((urlQuery.query?.fav as boolean) ?? false);
    setSortDesc((urlQuery.query?.desc as boolean) ?? false);
    setSort(urlQuery.query?.sort as number);
    setFilter(urlQuery.query?.filter as number);
  });

  useUpdateEffect(() => {
    router.replace(urlstring({ fav: favorites || undefined }));
  }, [favorites]);

  useUpdateEffect(() => {
    router.replace(urlstring({ desc: sortDesc || undefined }));
  }, [sortDesc]);

  useUpdateEffect(() => {
    router.replace(urlstring({ sort }));
  }, [sort]);

  useUpdateEffect(() => {
    router.replace(urlstring({ filter }));
  }, [filter]);

  useEffect(() => {
    router.replace(urlstring({ limit: itemCount }));
  }, [itemCount]);

  const pageHrefTemplate = useMemo(
    () => urlstring(router.asPath, { p: '${page}' }, { encode: false }),
    [router.query]
  );

  const onItemKey = useCallback((item: ServerItem) => item.id, []);

  return (
    <LibraryContext.Provider value={true}>
      <PageLayout
        menu={useMemo(
          () => (
            <MainMenu>
              <MenuItem>
                <ViewButtons
                  view={view}
                  setView={setView}
                  item={item}
                  setItem={setItem}
                />
              </MenuItem>
            </MainMenu>
          ),
          [view, item]
        )}
        bottomZone={useMemo(() => {
          return filter ? (
            <BottomZoneItem x="center" y="bottom">
              <FilterPageMessage filterId={filter} />
            </BottomZoneItem>
          ) : null;
        }, [filter])}
        bottomZoneRight={useMemo(
          () => (
            <>
              <OnlyFavoritesButton
                active={favorites}
                setActive={setFavorites}
              />
              <div className="medium-margin-top">
                <div className="pos-relative">
                  <FilterButtonInput active={filter} setActive={setFilter} />
                  <Visible visible={!!filter}>
                    <ClearFilterButton
                      onClick={() => {
                        setFilter(undefined);
                      }}
                      className="accented_button"
                      size="mini"
                    />
                  </Visible>
                </div>
              </div>
              <div className="medium-margin-top mb-auto">
                <div className="pos-relative">
                  <SortButtonInput
                    itemType={itemType}
                    active={sort}
                    setActive={setSort}
                  />
                  <Visible visible={true}>
                    <SortOrderButton
                      descending={sortDesc}
                      onClick={() => {
                        setSortDesc(!sortDesc);
                      }}
                      className="accented_button"
                      size="mini"
                    />
                  </Visible>
                </div>
              </div>
            </>
          ),
          [favorites, filter, sort, sortDesc]
        )}>
        <PageTitle title={t`Library`} />
        {!items.count && <EmptySegment />}
        <LibrarySidebar />
        {display === 'card' && (
          <CardView
            hrefTemplate={pageHrefTemplate}
            activePage={urlQuery.query?.p}
            items={items.items}
            paddedChildren
            itemRender={GalleryCard}
            itemsPerPage={itemCount}
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
      </PageLayout>
    </LibraryContext.Provider>
  );
}
