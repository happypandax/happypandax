import classNames from 'classnames';
import _ from 'lodash';
import { GetServerSidePropsResult, NextPageContext } from 'next';
import Router, { useRouter } from 'next/router';
import { useCallback, useMemo, useState } from 'react';
import { useQueryClient } from 'react-query';
import { useEffectOnce, useUpdateEffect } from 'react-use';
import {
  useRecoilState,
  useRecoilTransaction_UNSTABLE,
  useRecoilValue,
  useSetRecoilState,
} from 'recoil';
import {
  Button,
  Checkbox,
  Form,
  Header,
  Menu,
  Message,
  Modal,
  Segment,
  Select,
} from 'semantic-ui-react';

import { LibraryContext } from '../client/context';
import { QueryType, useQueryType } from '../client/queries';
import GalleryDataTable from '../components/dataview/GalleryData';
import CollectionCard, {
  collectionCardDataFields,
} from '../components/item/Collection';
import GalleryCard, { galleryCardDataFields } from '../components/item/Gallery';
import GroupingCard, {
  groupingCardDataFields,
} from '../components/item/Grouping';
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
import { AppState, getStateKey, LibraryState, SearchState } from '../state';

const StateKey = 'library_page';

export function cookieKey(k: string) {
  return k;
}

export function libraryArgs({
  ctx,
  stateKey: defaultStateKey,
  cookieKey: defaultCookieKey,
  urlQuery,
  page,
  itemType: defaultItemType,
  relatedType,
  itemId,
}: {
  ctx?: NextPageContext;
  urlQuery: ReturnType<typeof urlparse>;
  page?: number;
  itemType?: ItemType;
  relatedType?: ItemType;
  itemId?: number;
  stateKey?: string;
  cookieKey?(k: string): string;
}) {
  let itemType = relatedType ?? defaultItemType;

  const stateKey = defaultStateKey ?? StateKey;

  if (!itemType) {
    // can't trust user input
    if (urlQuery.query?.item === ItemType.Collection) {
      itemType = ItemType.Collection;
    } else if (
      getCookies(ctx, getStateKey(LibraryState.item, stateKey)) ===
      ItemType.Collection
    ) {
      itemType = ItemType.Collection;
    } else if (
      getCookies(ctx, getStateKey(LibraryState.series, stateKey)) === true
    ) {
      itemType = ItemType.Grouping;
    } else {
      itemType = ItemType.Gallery;
    }
  }

  const view =
    urlQuery.query?.view ??
    getCookies(ctx, getStateKey(LibraryState.view, stateKey));

  const metatags = {
    trash: false,
    favorite:
      ((urlQuery.query?.fav ??
        getCookies(
          ctx,
          getStateKey(LibraryState.favorites, stateKey)
        )) as boolean) || undefined,
    inbox:
      ViewType.All === view
        ? undefined
        : ViewType.Inbox === view
        ? true
        : false,
  };

  let search_options = getCookies(
    ctx,
    getStateKey(SearchState.options, stateKey)
  );
  const searchKeys = Object.keys(urlQuery.query).filter((x) =>
    x.startsWith('s.')
  );
  if (searchKeys.length) {
    searchKeys.forEach((s) => {
      const k = s.split('.')?.[1];
      if (
        k &&
        [
          'regex',
          'case_sensitive',
          'match_exact',
          'match_all_terms',
          'children',
        ].includes(k)
      ) {
        search_options = search_options ?? {};
        search_options[k] = !!urlQuery.query[s];
      }
    });
  }

  let p = page ?? 1;
  if (!page) {
    if (
      urlQuery.query?.p &&
      !isNaN(parseInt(urlQuery.query?.p as string, 10))
    ) {
      p = parseInt(urlQuery.query?.p as string, 10);
    } else {
      const c_p = getCookies(ctx, getStateKey(LibraryState.page, stateKey));
      if (c_p) {
        p = c_p;
      }
    }
  }

  if (p) {
    p--;
  }

  let filter_id = (urlQuery.query?.filter ??
    getCookies(ctx, getStateKey(LibraryState.filter, stateKey))) as number;

  // filters dont support collections
  if (itemType === ItemType.Collection) {
    filter_id = undefined;
  }

  const limit =
    ((urlQuery.query?.limit ??
      getCookies(ctx, getStateKey(LibraryState.limit, stateKey))) as number) ??
    30;

  return {
    errorLimit: p * limit > 10000, // there is a limit of 10000 or the request will fail
    args: {
      related_type: relatedType,
      item_id: itemId,
      item_type: defaultItemType ?? itemType,
      metatags,
      search_query: (urlQuery.query?.q?.toString() ??
        getCookies(ctx, getStateKey(LibraryState.query, stateKey))) as string,
      page: p,
      sort_options: {
        by:
          ((urlQuery.query?.sort ??
            getCookies(
              ctx,
              getStateKey(LibraryState.sort, stateKey)
            )) as number) ?? ItemSort.GalleryDate,
        desc:
          ((urlQuery.query?.desc ??
            getCookies(
              ctx,
              getStateKey(LibraryState.sortDesc, stateKey)
            )) as boolean) ?? true,
      },
      search_options,
      filter_id,
      limit,
      fields:
        itemType === ItemType.Gallery
          ? galleryCardDataFields
          : itemType === ItemType.Collection
          ? collectionCardDataFields
          : groupingCardDataFields,
    } as Parameters<ServerService['library']>[0],
  };
}

function FilterPageMessage({
  filterId,
  stateKey,
}: {
  filterId: number;
  stateKey: string;
}) {
  const { data, isLoading } = useQueryType(QueryType.ITEM, {
    item_type: ItemType.Filter,
    item_id: filterId,
    fields: ['name', 'info', 'filter'],
  });

  const setFilter = useSetRecoilState(LibraryState.filter(stateKey));

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

function LibrarySettings({
  trigger,
  stateKey,
}: {
  trigger: React.ReactNode;
  stateKey: string;
}) {
  const sameMachine = useRecoilState(AppState.sameMachine);
  const [item, setItem] = useRecoilState(LibraryState.item(stateKey));
  const [view, setView] = useRecoilState(LibraryState.view(stateKey));
  const [series, setSeries] = useRecoilState(LibraryState.series);
  const [infinite, setInfinite] = useRecoilState(LibraryState.infinite);
  const [limit, setLimit] = useRecoilState(LibraryState.limit);
  const [display, setDisplay] = useRecoilState(LibraryState.display);
  const [externalViewer, setExternalViewer] = useRecoilState(
    AppState.externalViewer
  );

  const router = useRouter();

  const [reload, setReload] = useState(false);

  const displayChange = useCallback((e, { value }) => {
    e.preventDefault();
    setDisplay(value);
  }, []);

  const externalViewerChange = useCallback((ev, { checked }) => {
    ev.preventDefault();
    setExternalViewer(checked);
  }, []);

  return (
    <Modal
      trigger={trigger}
      dimmer={false}
      onClose={useCallback(() => {
        if (reload) {
          router.reload();
        }
      }, [reload, router])}>
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
            <label>{t`Collapse galleries in series`}</label>
            <Checkbox
              toggle
              checked={series}
              onChange={useCallback((ev, { checked }) => {
                ev.preventDefault();
                setSeries(checked);
                setReload(true);
              }, [])}
            />
          </Form.Field>

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
                onChange={externalViewerChange}
              />
            </Form.Field>
          )}
        </Form>
      </Modal.Content>
    </Modal>
  );
}

export interface PageProps {
  data: Unwrap<ServerService['library']>;
  page: number;
  itemType: ItemType;
  urlQuery: ReturnType<typeof urlparse>;
  requestTime: number;
  errorLimit: boolean;
}

export async function getServerSideProps(
  context: NextPageContext,
  args?: ReturnType<typeof libraryArgs>
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = global.app.service.get(ServiceType.Server);

  const urlQuery = urlparse(context.resolvedUrl);

  const { errorLimit, args: largs } =
    args ?? libraryArgs({ ctx: context, urlQuery });

  const data = errorLimit
    ? { count: 0, items: [] }
    : await server.library<ServerGallery>(largs);

  return {
    props: {
      data,
      urlQuery,
      itemType: largs.item_type,
      page: largs.page ? largs.page + 1 : 1,
      requestTime: Date.now(),
      errorLimit,
    },
  };
}

export default function Page({
  data: initialData,
  page: initialPage,
  errorLimit: initialErrorLimit,
  urlQuery,
  itemType,
  requestTime,
  libraryArgs: defaultLibraryArgs,
  hideViewItems,
  stateKey: defaultStateKey,
  children,
}: PageProps & {
  hideViewItems?: boolean;
  stateKey?: string;
  children?: React.ReactNode;
  libraryArgs?: Partial<Parameters<typeof libraryArgs>[0]>;
}) {
  const stateKey = defaultStateKey ?? StateKey;

  const [item, setItem] = useRecoilState(LibraryState.item(stateKey));
  const [view, setView] = useRecoilState(LibraryState.view(stateKey));
  const [query, setQuery] = useRecoilState(LibraryState.query(stateKey));
  const [favorites, setFavorites] = useRecoilState(
    LibraryState.favorites(stateKey)
  );
  const [filter, setFilter] = useRecoilState(LibraryState.filter(stateKey));
  const [sort, setSort] = useRecoilState(LibraryState.sort(stateKey));
  const [sortDesc, setSortDesc] = useRecoilState(
    LibraryState.sortDesc(stateKey)
  );
  const [page, setPage] = useRecoilState(LibraryState.page(stateKey));
  const limit = useRecoilValue(LibraryState.limit);
  const display = useRecoilValue(LibraryState.display);
  const infinite = useRecoilValue(LibraryState.infinite);

  const [searchOptions, setSearchOptions] = useRecoilState(
    SearchState.options(stateKey)
  );
  const setRecentQuery = useSetRecoilState(SearchState.recent(stateKey));

  const router = useRouter();
  const routerQuery = urlparse(router.asPath);

  const { errorLimit, args: libraryargs } = libraryArgs({
    urlQuery: routerQuery,
    ...defaultLibraryArgs,
  });

  const [infiniteKey, setInfiniteKey] = useState('');

  const activePage = infiniteKey
    ? page
    : libraryargs.page !== undefined
    ? libraryargs.page + 1
    : page;


  const errorLimited = errorLimit || initialErrorLimit;

  const { data, fetchNextPage, isFetching, queryKey, remove } = useQueryType(
    QueryType.LIBRARY,
    {
      ...libraryargs,
      item: itemType,
      page: infiniteKey ? initialPage - 1 : activePage - 1,
    },
    {
      enabled: !errorLimited,
      initialData: global.app.IS_SERVER ? undefined : initialData,
      initialDataUpdatedAt: requestTime,
      infinite: true,
      infinitePageParam: (variables, ctx) => ({
        ...variables,
        page: (ctx.pageParam ?? 1) - 1,
      }),
      onQueryKey: () => QueryType.LIBRARY.toString() + infiniteKey,
    }
  );

  const items = infiniteKey
    ? data?.pages?.flat?.().flatMap?.((i) => i.data.items)
    : initialData.items;

  const count = infiniteKey
    ? data?.pages?.[0]?.data?.count
    : initialData?.count;

  const initialQueryState = useRecoilTransaction_UNSTABLE(({ set }) => () => {
    if (urlQuery.query?.fav !== undefined) {
      set(LibraryState.favorites(stateKey), urlQuery.query.fav as boolean);
    }
    if (urlQuery.query?.desc !== undefined) {
      set(LibraryState.sortDesc(stateKey), urlQuery.query.desc as boolean);
    }
    if (urlQuery.query?.sort !== undefined) {
      set(LibraryState.sort(stateKey), urlQuery.query.sort as number);
    }
    if (urlQuery.query?.filter !== undefined) {
      set(LibraryState.filter(stateKey), urlQuery.query.filter as number);
    }
    if (urlQuery.query?.view !== undefined) {
      set(LibraryState.view(stateKey), urlQuery.query.view as number);
    }
    if (urlQuery.query?.item !== undefined) {
      set(LibraryState.item(stateKey), urlQuery.query.item as number);
    }
    if (urlQuery.query?.limit !== undefined) {
      set(LibraryState.limit, urlQuery.query.limit as number);
    }
    if (urlQuery.query?.display !== undefined) {
      set(LibraryState.display, urlQuery.query.display as 'card' | 'list');
    }
    if (routerQuery?.query?.p ?? urlQuery.query?.p) {
      const p = parseInt(
        ((routerQuery?.query?.p ?? urlQuery.query?.p) as string) ?? '1',
        10
      );
      set(LibraryState.page(stateKey), isNaN(p) ? 1 : p);
    }

    if (
      urlQuery.query?.option !== undefined &&
      typeof urlQuery.query.option === 'object'
    ) {
      set(SearchState.options(stateKey), urlQuery.query.option);
    }
  });

  useEffectOnce(() => {
    initialQueryState();
  });

  const client = useQueryClient();

  useUpdateEffect(() => {
    const q = {
      p: 1,
      view,
      item,
      fav: favorites || undefined,
      desc: sortDesc,
      sort,
      filter,
      limit,
      ..._.mapKeys(searchOptions, (v, k) => 's.' + k),
    };
    router.replace(urlstring(q)).then(() => {
      setPage(1);
      setInfiniteKey('');
    });
    // .then(() => client.resetQueries(queryKey));
  }, [view, item, favorites, sortDesc, sort, filter, limit, searchOptions]);

  useUpdateEffect(() => {
    const q = {
      ...routerQuery?.query,
      p: 1,
      q: query,
    };
    setPage(1);
    setInfiniteKey('');
    router.push(urlstring(q)).then(() => {
      setPage(1);
      setInfiniteKey('');
    });

    // .then(() => client.resetQueries(queryKey));
  }, [query]);

  useUpdateEffect(() => {
    router.replace(urlstring({ display }), undefined, { shallow: true });
  }, [display]);

  useUpdateEffect(() => {
    if (routerQuery?.query?.p ?? urlQuery.query?.p) {
      const p = parseInt(
        ((routerQuery?.query?.p ?? urlQuery.query?.p) as string) ?? '1',
        10
      );
      if (!isNaN(p)) {
        setPage(p);
      }
    }
  }, [routerQuery]);

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
    let key = infiniteKey;
    if (!infiniteKey) {
      key = new Date().getTime().toString(36);
      setInfiniteKey(key);
    }

    if (!isFetching && fetchNextPage) {
      let p = initialPage + data.pages.length;
      console.log(p);
      fetchNextPage({
        pageParam: p,
      });
      setPage(p);
      router.replace(urlstring({ p }), undefined, {
        shallow: true,
        scroll: false,
      });
    }
  }, [router, initialPage, fetchNextPage, infiniteKey, isFetching, data]);

  const onPageChange = useCallback((ev, n) => {
    setInfiniteKey('');
    setPage(n);
  }, []);

  const onItemChange = useRecoilTransaction_UNSTABLE(({ set }) => (i) => {
    set(LibraryState.item(stateKey), i);
    set(LibraryState.page(stateKey), 1);
  });

  const onViewChange = useRecoilTransaction_UNSTABLE(({ set }) => (i) => {
    set(LibraryState.view(stateKey), i);
    set(LibraryState.page(stateKey), 1);
  });

  const goBack = useCallback(() => {
    router.back();
  }, [router]);

  const View = display === 'card' ? CardView : ListView;

  return (
    <PageLayout
      menu={useMemo(
        () => (
          <MainMenu fixed>
            <MenuItem className={classNames('no-right-padding')}>
              <ViewButtons
                view={view}
                onView={onViewChange}
                hideItems={hideViewItems}
                item={item}
                onItem={onItemChange}
              />
            </MenuItem>
            <Menu.Menu position="left" className="fullwidth">
              <MenuItem className={classNames('fullwidth')}>
                <ItemSearch
                  stateKey={stateKey}
                  itemTypes={
                    [ItemType.Gallery, ItemType.Grouping].includes(itemType)
                      ? [
                          ItemType.Artist,
                          ItemType.Category,
                          ItemType.Circle,
                          ItemType.Grouping,
                          ItemType.Language,
                          ItemType.Parody,
                          ItemType.NamespaceTag,
                        ]
                      : [ItemType.Collection, ItemType.Category]
                  }
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
        [view, item, itemType, query, urlQuery.query?.q, hideViewItems]
      )}
      bottomZone={useMemo(() => {
        return filter ? (
          <BottomZoneItem x="center" y="bottom">
            <FilterPageMessage stateKey={stateKey} filterId={filter} />
          </BottomZoneItem>
        ) : null;
      }, [filter, stateKey])}
      bottomZoneRightBottom={useMemo(() => {
        return (
          <LibrarySettings
            stateKey={stateKey}
            trigger={<PageSettingsButton />}
          />
        );
      }, [stateKey])}
      bottomZoneRight={useMemo(
        () => (
          <>
            <OnlyFavoritesButton active={favorites} setActive={setFavorites} />
            {itemType !== ItemType.Collection && (
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
            )}
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
        [favorites, filter, sort, sortDesc, itemType]
      )}>
      <PageTitle title={t`Library`} />
      {children}
      {!count && !errorLimited && <EmptySegment />}
      {errorLimited && (
        <EmptySegment
          title={
            <div>
              <p>
                {t`Momo wasn't able to fetch page ${activePage} fast enough!`}
                <br />
                {t`Please refine your search query to retrieve results.`}
              </p>
            </div>
          }>
          <Segment basic textAlign="center">
            <Button color="red" onClick={goBack}>{t`Go back`}</Button>
          </Segment>
        </EmptySegment>
      )}
      <LibraryContext.Provider value={true}>
        <LibrarySidebar />
        {!errorLimited && (
          <View
            hrefTemplate={pageHrefTemplate}
            activePage={activePage}
            items={items}
            infinite={infinite}
            loading={isFetching}
            onPageChange={onPageChange}
            onLoadMore={fetchNext}
            paddedChildren
            itemRender={
              itemType === ItemType.Gallery
                ? GalleryCard
                : itemType === ItemType.Collection
                ? CollectionCard
                : GroupingCard
            }
            itemsPerPage={limit}
            onItemKey={onItemKey}
            totalItemCount={count}
            pagination={!!count || errorLimited}
            bottomPagination={!!count}
          />
        )}
      </LibraryContext.Provider>
    </PageLayout>
  );
}
