import classNames from 'classnames';
import { GetServerSidePropsResult, NextPageContext } from 'next';
import Router, { useRouter } from 'next/router';
import { useCallback, useEffect, useMemo } from 'react';
import { useEffectOnce, useUpdateEffect } from 'react-use';
import { useRecoilState, useRecoilValue, useSetRecoilState } from 'recoil';
import { Menu, Message } from 'semantic-ui-react';

import { LibraryContext } from '../client/context';
import { QueryType, useQueryType } from '../client/queries';
import { GalleryDataTable } from '../components/DataTable';
import GalleryCard, { galleryCardDataFields } from '../components/item/Gallery';
import {
  ClearFilterButton,
  FilterButtonInput,
  OnlyFavoritesButton,
  SortButtonInput,
  SortOrderButton,
  ViewButtons,
} from '../components/layout/GalleryLayout';
import PageLayout, { BottomZoneItem } from '../components/layout/Page';
import MainMenu, { MenuItem } from '../components/Menu';
import {
  EmptySegment,
  ItemSearch,
  PageInfoMessage,
  PageTitle,
  Visible,
} from '../components/Misc';
import { StickySidebar } from '../components/Sidebar';
import CardView from '../components/view/CardView';
import ListView from '../components/view/ListView';
import { ItemSort, ItemType, ViewType } from '../misc/enums';
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

  const view = urlQuery.query?.view;

  const metatags = {
    trash: false,
    favorite: urlQuery.query?.fav as boolean,
    inbox:
      ViewType.All === view
        ? undefined
        : ViewType.Inbox === view
        ? true
        : false,
  };

  const data = await server.library<ServerGallery>({
    item_type: itemType,
    metatags,
    search_query: urlQuery.query?.q as string,
    page: urlQuery.query?.p as number,
    sort_options: {
      by: (urlQuery.query?.sort as number) ?? ItemSort.GalleryDate,
      desc: (urlQuery.query?.desc as boolean) ?? true,
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
  const [query, setQuery] = useRecoilState(LibraryState.query);
  const [favorites, setFavorites] = useRecoilState(LibraryState.favorites);
  const [filter, setFilter] = useRecoilState(LibraryState.filter);
  const [sort, setSort] = useRecoilState(LibraryState.sort);
  const [sortDesc, setSortDesc] = useRecoilState(LibraryState.sortDesc);
  const [limit, setLimit] = useRecoilState(LibraryState.limit);
  const [display, setDisplay] = useRecoilState(LibraryState.display);

  const router = useRouter();

  useEffectOnce(() => {
    if (urlQuery.query?.fav !== undefined) {
      setFavorites(urlQuery.query.fav as boolean);
    }
    if (urlQuery.query?.desc !== undefined) {
      setSortDesc(urlQuery.query.desc as boolean);
    }
    if (urlQuery.query?.sort !== undefined) {
      setSort(urlQuery.query.sort as number);
    }
    if (urlQuery.query?.filter !== undefined) {
      setFilter(urlQuery.query.filter as number);
    }
    if (urlQuery.query?.view !== undefined) {
      setView(urlQuery.query.view as number);
    }
    if (urlQuery.query?.limit !== undefined) {
      setLimit(urlQuery.query.limit as number);
    }
    if (urlQuery.query?.display !== undefined) {
      setDisplay(urlQuery.query.display as 'card' | 'list');
    }
  });

  useUpdateEffect(() => {
    router.replace(urlstring({ view }));
  }, [view]);

  useUpdateEffect(() => {
    router.replace(urlstring({ display }));
  }, [display]);

  useUpdateEffect(() => {
    router.replace(urlstring({ fav: favorites || undefined }));
  }, [favorites]);

  useUpdateEffect(() => {
    router.replace(urlstring({ desc: sortDesc }));
  }, [sortDesc]);

  useUpdateEffect(() => {
    router.replace(urlstring({ sort }));
  }, [sort]);

  useUpdateEffect(() => {
    router.replace(urlstring({ filter }));
  }, [filter]);

  useEffect(() => {
    router.replace(urlstring({ limit }));
  }, [limit]);

  useEffect(() => {
    router.replace(urlstring({ q: query }));
  }, [query]);

  const pageHrefTemplate = useMemo(
    () => urlstring(router.asPath, { p: '${page}' }, { encode: false }),
    [router.query]
  );

  const onItemKey = useCallback((item: ServerItem) => item.id, []);

  return (
    <PageLayout
      menu={useMemo(
        () => (
          <MainMenu fixed>
            <MenuItem className={classNames('no-right-padding')}>
              <ViewButtons
                view={view}
                onView={setView}
                item={item}
                onItem={setItem}
              />
            </MenuItem>
            <Menu.Menu position="left" className="fullwidth">
              <MenuItem className={classNames('fullwidth')}>
                <ItemSearch
                  onSearch={(query) => {
                    setQuery(query);
                  }}
                  onClear={() => {
                    setQuery('');
                  }}
                  defaultValue={(urlQuery.query?.q as string) ?? query}
                  placeholder={t`Search using tags, titles, names, artists... Press "/" to search`}
                  showOptions
                  size="small"
                  fluid
                />
              </MenuItem>
            </Menu.Menu>
          </MainMenu>
        ),
        [view, item, itemType, query, urlQuery.query?.q]
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
            <OnlyFavoritesButton active={favorites} setActive={setFavorites} />
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
      {!data.count && <EmptySegment />}
      <LibraryContext.Provider value={true}>
        <LibrarySidebar />
        {display === 'card' && (
          <CardView
            hrefTemplate={pageHrefTemplate}
            activePage={urlQuery.query?.p}
            items={data.items}
            paddedChildren
            itemRender={GalleryCard}
            itemsPerPage={limit}
            onItemKey={onItemKey}
            totalItemCount={data.count}
            pagination={!!data.count}
            bottomPagination={!!data.count}></CardView>
        )}
        {display === 'list' && (
          <ListView
            hrefTemplate={pageHrefTemplate}
            items={data.items}
            activePage={urlQuery.query?.p}
            onItemKey={onItemKey}
            itemsPerPage={limit}
            itemRender={GalleryCard}
            totalItemCount={data.count}
            pagination={!!data.count}
            bottomPagination={!!data.count}></ListView>
        )}
      </LibraryContext.Provider>
    </PageLayout>
  );
}
