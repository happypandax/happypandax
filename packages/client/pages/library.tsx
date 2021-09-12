import classNames from 'classnames';
import _ from 'lodash';
import { GetServerSidePropsResult, NextPageContext } from 'next';
import Router, { useRouter } from 'next/router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useEffectOnce, useUpdateEffect } from 'react-use';
import { useRecoilState, useRecoilValue, useSetRecoilState } from 'recoil';
import {
  Checkbox,
  Form,
  Menu,
  Message,
  Modal,
  Select,
} from 'semantic-ui-react';

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
import PageLayout, {
  BottomZoneItem,
  PageSettingsButton,
} from '../components/layout/Page';
import MainMenu, { MenuItem } from '../components/Menu';
import {
  EmptySegment,
  PageInfoMessage,
  PageTitle,
  Visible,
} from '../components/Misc';
import { ItemSearch } from '../components/Search';
import { StickySidebar } from '../components/Sidebar';
import CardView from '../components/view/CardView';
import ListView from '../components/view/ListView';
import { ItemSort, ItemType, ViewType } from '../misc/enums';
import t from '../misc/lang';
import { ServerGallery, ServerItem } from '../misc/types';
import { getCookies, urlparse, urlstring } from '../misc/utility';
import { ServiceType } from '../services/constants';
import ServerService from '../services/server';
import { AppState, LibraryState, MiscState } from '../state';

interface PageProps {
  data: Unwrap<ServerService['library']>;
  itemType: ItemType;
  urlQuery: ReturnType<typeof urlparse>;
}

function libraryArgs(
  ctx: NextPageContext | undefined,
  itemType: ItemType,
  urlQuery: ReturnType<typeof urlparse>,
  page?: number
) {
  const view = urlQuery.query?.view ?? getCookies(ctx, 'library_view');

  const metatags = {
    trash: false,
    favorite:
      ((urlQuery.query?.fav ?? getCookies(ctx, 'library_fav')) as boolean) ||
      undefined,
    inbox:
      ViewType.All === view
        ? undefined
        : ViewType.Inbox === view
        ? true
        : false,
  };

  let p =
    page ?? ((urlQuery.query?.p ?? getCookies(ctx, 'library_page')) as number);

  if (p) {
    p--;
  }

  return {
    item_type: itemType,
    metatags,
    search_query: (urlQuery.query?.q ??
      getCookies(ctx, 'library_query')) as string,
    page: p,
    sort_options: {
      by:
        ((urlQuery.query?.sort ?? getCookies(ctx, 'library_sort')) as number) ??
        ItemSort.GalleryDate,
      desc:
        ((urlQuery.query?.desc ??
          getCookies(ctx, 'library_desc')) as boolean) ?? true,
    },
    filter_id: (urlQuery.query?.filter ??
      getCookies(ctx, 'library_filter')) as number,
    limit: (urlQuery.query?.limit ??
      getCookies(ctx, 'library_limit')) as number,
    fields: galleryCardDataFields,
  };
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

  // const group = server.create_group_call();

  const data = await server.library<ServerGallery>(
    libraryArgs(context, itemType, urlQuery)
  );

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

const itemsPerPage = [
  { key: '10', text: '10', value: 10 },
  { key: '20', text: '20', value: 20 },
  { key: '30', text: '30', value: 30 },
  { key: '40', text: '40', value: 40 },
  { key: '50', text: '50', value: 50 },
  { key: '75', text: '75', value: 75 },
  { key: '100', text: '100', value: 100 },
  { key: '125', text: '125', value: 125 },
  { key: '200', text: '200', value: 200 },
  { key: '250', text: '250', value: 250 },
];

function LibrarySettings({ trigger }: { trigger: React.ReactNode }) {
  const sameMachine = useRecoilState(AppState.sameMachine);
  const [item, setItem] = useRecoilState(LibraryState.item);
  const [view, setView] = useRecoilState(LibraryState.view);
  const [infinite, setInfinite] = useRecoilState(LibraryState.infinite);
  const [limit, setLimit] = useRecoilState(LibraryState.limit);
  const [display, setDisplay] = useRecoilState(LibraryState.display);
  const [externalViewer, setExternalViewer] = useRecoilState(
    AppState.externalViewer
  );

  const displayChange = useCallback((e, { value }) => {
    e.preventDefault();
    setDisplay(value);
  }, []);

  return (
    <Modal trigger={trigger} dimmer={false}>
      <Modal.Header>{t`Library Settings`}</Modal.Header>
      <Modal.Content>
        <Form>
          <Form.Group inline>
            <label>{t`Display`}</label>
            <Form.Radio
              label={t`Card`}
              value="card"
              checked={display === 'card'}
              onChange={displayChange}
            />
            <Form.Radio
              label={t`List`}
              value="list"
              checked={display === 'list'}
              onChange={displayChange}
            />
          </Form.Group>

          <Form.Group inline>
            <label>{t`Default view`}</label>
            <Form.Radio label={t`All`} />
            <Form.Radio label={t`Library`} />
            <Form.Radio label={t`Inbox`} />
          </Form.Group>

          <Form.Field
            control={Select}
            label={t`Items per page`}
            placeholder={t`Items per page`}
            onChange={useCallback((ev, { value }) => {
              ev.preventDefault();
              setLimit(parseInt(value, 10));
            }, [])}
            value={limit}
            options={itemsPerPage}
            // width={4}
          />

          <Form.Field
            control={Select}
            label={t`Default item`}
            placeholder={t`Default item`}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
            }, [])}
            value={30}
            defaultValue={30}
            options={itemsPerPage}
            // width={4}
          />

          <Form.Field
            control={Select}
            label={t`Default sort`}
            placeholder={t`Default sort`}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
            }, [])}
            value={30}
            defaultValue={30}
            options={itemsPerPage}
            // width={4}
          />

          <Form.Field
            control={Select}
            label={t`Default sort order`}
            placeholder={t`Default sort order`}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
            }, [])}
            value={30}
            defaultValue={30}
            options={itemsPerPage}
            // width={4}
          />

          <Form.Field
            control={Select}
            label={t`Default filter`}
            placeholder={t`Default filter`}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
            }, [])}
            value={30}
            defaultValue={30}
            options={itemsPerPage}
            // width={4}
          />

          <Form.Field>
            <label>{t`Infinite scroll`}</label>
            <Checkbox
              toggle
              checked={infinite}
              onChange={useCallback((ev, { checked }) => {
                ev.preventDefault();
                setInfinite(checked);
              }, [])}
            />
          </Form.Field>

          {sameMachine && (
            <Form.Field>
              <label>{t`Open in external viewer`}</label>
              <Checkbox
                toggle
                checked={externalViewer}
                onChange={useCallback((ev, { checked }) => {
                  ev.preventDefault();
                  setExternalViewer(checked);
                }, [])}
              />
            </Form.Field>
          )}
        </Form>
      </Modal.Content>
    </Modal>
  );
}

const stateKey = 'library_page';

export default function Page({
  data: initialData,
  urlQuery,
  itemType,
}: PageProps) {
  const [item, setItem] = useRecoilState(LibraryState.item);
  const [view, setView] = useRecoilState(LibraryState.view);
  const [query, setQuery] = useRecoilState(LibraryState.query);
  const [favorites, setFavorites] = useRecoilState(LibraryState.favorites);
  const [filter, setFilter] = useRecoilState(LibraryState.filter);
  const [sort, setSort] = useRecoilState(LibraryState.sort);
  const [sortDesc, setSortDesc] = useRecoilState(LibraryState.sortDesc);
  const [limit, setLimit] = useRecoilState(LibraryState.limit);
  const [display, setDisplay] = useRecoilState(LibraryState.display);
  const infinite = useRecoilValue(LibraryState.infinite);

  const [infiniteKey, setInfiniteKey] = useState('');

  const setRecentQuery = useSetRecoilState(MiscState.recentSearch(stateKey));

  const libraryargs = libraryArgs(undefined, itemType, urlQuery);

  const { data, fetchNextPage, isFetching } = useQueryType(
    QueryType.LIBRARY,
    libraryargs,
    {
      initialData,
      infinite: true,
      infinitePageParam: (variables, ctx) => ({
        ...variables,
        page: (ctx.pageParam ?? 1) - 1,
      }),
      onQueryKey: () => QueryType.LIBRARY.toString() + infiniteKey,
    }
  );

  const items = data?.pages?.flat?.().flatMap?.((i) => i.data.items);
  const count = data?.pages?.[0]?.data?.count;

  const router = useRouter();
  const routerQuery = urlparse(router.asPath);

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
    router.replace(urlstring({ view, p: 1 }));
  }, [view]);

  useUpdateEffect(() => {
    router.replace(urlstring({ display }), undefined, { shallow: true });
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
    router.replace(urlstring({ q: query, p: 1 }));
  }, [query]);

  const pageHrefTemplate = useMemo(
    () => urlstring(router.asPath, { p: '${page}' }, { encode: false }),
    [router.query]
  );

  const onItemKey = useCallback((item: ServerItem) => item.id, []);
  const saveRecentQuery = useCallback(
    _.debounce((query: string) => {
      setRecentQuery([query]);
    }, 5000),
    []
  );

  const fetchNext = useCallback(() => {
    if (!infiniteKey) {
      setInfiniteKey(new Date().getTime().toString(36));
    } else if (!isFetching && fetchNextPage) {
      let p = libraryargs.page ? libraryargs.page : 1;
      p = p + data.pages.length;
      fetchNextPage({
        pageParam: p,
      });
      router.replace(urlstring({ p }), undefined, { shallow: true });
    }
  }, [libraryargs, router, fetchNextPage, infiniteKey, isFetching, data]);

  const onPageChange = useCallback(() => {
    setInfiniteKey('');
  }, [infinite]);

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
                  stateKey={stateKey}
                  onSearch={(query) => {
                    setQuery(query);
                    if (query) {
                      saveRecentQuery(query);
                    }
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
      bottomZoneRightBottom={useMemo(() => {
        return <LibrarySettings trigger={<PageSettingsButton />} />;
      }, [])}
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
      {!count && <EmptySegment />}
      <LibraryContext.Provider value={true}>
        <LibrarySidebar />
        {display === 'card' && (
          <CardView
            hrefTemplate={pageHrefTemplate}
            activePage={routerQuery?.query?.p ?? urlQuery.query?.p}
            items={items}
            infinite={infinite}
            onPageChange={onPageChange}
            onLoadMore={fetchNext}
            paddedChildren
            itemRender={GalleryCard}
            itemsPerPage={limit}
            onItemKey={onItemKey}
            totalItemCount={count}
            pagination={!!count}
            bottomPagination={!!count}></CardView>
        )}
        {display === 'list' && (
          <ListView
            hrefTemplate={pageHrefTemplate}
            items={items}
            infinite={infinite}
            onPageChange={onPageChange}
            onLoadMore={fetchNext}
            activePage={routerQuery?.query?.p ?? urlQuery.query?.p}
            onItemKey={onItemKey}
            itemsPerPage={limit}
            itemRender={GalleryCard}
            totalItemCount={count}
            pagination={!!count}
            bottomPagination={!!count}></ListView>
        )}
      </LibraryContext.Provider>
    </PageLayout>
  );
}
