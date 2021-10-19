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
  Checkbox,
  Form,
  Menu,
  Message,
  Modal,
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
import { AppState, LibraryState, SearchState } from '../state';
import _SearchState from '../state/_search';

interface PageProps {
  data: Unwrap<ServerService['library']>;
  page: number;
  itemType: ItemType;
  urlQuery: ReturnType<typeof urlparse>;
  requestTime: number;
}

const stateKey = 'library_page';

function libraryArgs(
  ctx: NextPageContext | undefined,
  urlQuery: ReturnType<typeof urlparse>,
  page?: number
) {
  let itemType = ItemType.Grouping;

  // can't trust user input
  if (urlQuery.query?.item === ItemType.Collection) {
    itemType = ItemType.Collection;
  } else if (getCookies(ctx, 'library_item') === ItemType.Collection) {
    itemType = ItemType.Collection;
  } else if (getCookies(ctx, 'library_series') === false) {
    itemType = ItemType.Gallery;
  }

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

  let search_options = getCookies(
    ctx,
    `${_SearchState.name}_options__"${stateKey}"`
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

  let p =
    page ?? ((urlQuery.query?.p ?? getCookies(ctx, 'library_page')) as number);

  if (p) {
    p--;
  }

  let filter_id = (urlQuery.query?.filter ??
    getCookies(ctx, 'library_filter')) as number;

  // filters dont support collections
  if (itemType === ItemType.Collection) {
    filter_id = undefined;
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
    search_options,
    filter_id,
    limit:
      ((urlQuery.query?.limit ?? getCookies(ctx, 'library_limit')) as number) ??
      30,
    fields:
      itemType === ItemType.Gallery
        ? galleryCardDataFields
        : itemType === ItemType.Collection
        ? collectionCardDataFields
        : groupingCardDataFields,
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
  const [series, setSeries] = useRecoilState(LibraryState.series);
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
            <label>{t`Collapse gallery in series`}</label>
            <Checkbox
              toggle
              checked={series}
              onChange={useCallback((ev, { checked }) => {
                ev.preventDefault();
                setSeries(checked);
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

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = global.app.service.get(ServiceType.Server);

  const urlQuery = urlparse(context.resolvedUrl);

  // const group = server.create_group_call();

  const args = libraryArgs(context, urlQuery);

  const data = await server.library<ServerGallery>(args);

  return {
    props: {
      data,
      urlQuery,
      itemType: args.item_type,
      page: args.page ? args.page + 1 : 1,
      requestTime: Date.now(),
    },
  };
}

export default function Page({
  data: initialData,
  page: initialPage,
  urlQuery,
  itemType,
  requestTime,
}: PageProps) {
  const [item, setItem] = useRecoilState(LibraryState.item);
  const [view, setView] = useRecoilState(LibraryState.view);
  const [query, setQuery] = useRecoilState(LibraryState.query);
  const [favorites, setFavorites] = useRecoilState(LibraryState.favorites);
  const [filter, setFilter] = useRecoilState(LibraryState.filter);
  const [sort, setSort] = useRecoilState(LibraryState.sort);
  const [sortDesc, setSortDesc] = useRecoilState(LibraryState.sortDesc);
  const [page, setPage] = useRecoilState(LibraryState.page);
  const limit = useRecoilValue(LibraryState.limit);
  const display = useRecoilValue(LibraryState.display);
  const infinite = useRecoilValue(LibraryState.infinite);

  const [infiniteKey, setInfiniteKey] = useState('');

  const [searchOptions, setSearchOptions] = useRecoilState(
    SearchState.options(stateKey)
  );
  const setRecentQuery = useSetRecoilState(SearchState.recent(stateKey));

  const router = useRouter();
  const routerQuery = urlparse(router.asPath);

  const libraryargs = libraryArgs(undefined, routerQuery);

  const { data, fetchNextPage, isFetching, queryKey } = useQueryType(
    QueryType.LIBRARY,
    {
      ...libraryargs,
      item: itemType,
      page: infiniteKey ? initialPage - 1 : libraryargs.page,
    },
    {
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

  const items = data?.pages?.flat?.().flatMap?.((i) => i.data.items);
  const count = data?.pages?.[0]?.data?.count;

  const initialQueryState = useRecoilTransaction_UNSTABLE(({ set }) => () => {
    if (urlQuery.query?.fav !== undefined) {
      set(LibraryState.favorites, urlQuery.query.fav as boolean);
    }
    if (urlQuery.query?.desc !== undefined) {
      set(LibraryState.sortDesc, urlQuery.query.desc as boolean);
    }
    if (urlQuery.query?.sort !== undefined) {
      set(LibraryState.sort, urlQuery.query.sort as number);
    }
    if (urlQuery.query?.filter !== undefined) {
      set(LibraryState.filter, urlQuery.query.filter as number);
    }
    if (urlQuery.query?.view !== undefined) {
      set(LibraryState.view, urlQuery.query.view as number);
    }
    if (urlQuery.query?.item !== undefined) {
      set(LibraryState.item, urlQuery.query.item as number);
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
      set(LibraryState.page, isNaN(p) ? 1 : p);
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
    };
    setPage(1);
    router.replace(urlstring(q)).then(() => client.resetQueries(queryKey));
  }, [view, item, favorites, sortDesc, sort, filter, limit]);

  useUpdateEffect(() => {
    const q = {
      ...routerQuery?.query,
      p: 1,
      query,
    };
    setPage(1);
    router.push(urlstring(q)).then(() => client.resetQueries(queryKey));
  }, [query]);

  useUpdateEffect(() => {
    const q = _.mapKeys(searchOptions, (v, k) => 's.' + k);
    router.replace(urlstring(q)).then(() => client.resetQueries(queryKey));
  }, [searchOptions]);

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
      let p = libraryargs.page ? libraryargs.page : 1;
      p = p + data.pages.length;
      fetchNextPage({
        pageParam: p,
      });
      setPage(p);
      router.replace(urlstring({ p }), undefined, {
        shallow: true,
        scroll: false,
      });
    }
  }, [libraryargs, router, fetchNextPage, infiniteKey, isFetching, data]);

  const onPageChange = useCallback(() => {
    setInfiniteKey('');
  }, [infinite]);

  const View = display === 'card' ? CardView : ListView;

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
      {!count && <EmptySegment />}
      <LibraryContext.Provider value={true}>
        <LibrarySidebar />
        <View
          hrefTemplate={pageHrefTemplate}
          activePage={page}
          items={items}
          infinite={infinite}
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
          pagination={!!count}
          bottomPagination={!!count}
        />
      </LibraryContext.Provider>
    </PageLayout>
  );
}
