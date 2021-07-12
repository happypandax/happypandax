import { GetServerSidePropsResult, NextPageContext } from 'next';
import Router, { useRouter } from 'next/router';
import { useMemo, useState } from 'react';
import { useEffectOnce, useUpdateEffect } from 'react-use';
import { useRecoilState, useRecoilValue } from 'recoil';

import GalleryCard from '../components/Gallery';
import {
  ClearFilterButton,
  FilterButtonInput,
  OnlyFavoritesButton,
  SortButtonInput,
  SortOrderButton,
  ViewButtons,
} from '../components/layout/ItemLayout';
import PageLayout from '../components/layout/Page';
import MainMenu, { MenuItem } from '../components/Menu';
import { PageTitle, Visible } from '../components/Misc';
import CardView from '../components/view/CardView';
import ListView from '../components/view/ListView';
import { ItemType } from '../misc/enums';
import t from '../misc/lang';
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

  const data = await server.library({
    item_type: itemType,
    metatags: { favorite: urlQuery.query?.fav as boolean, trash: false },
    page: urlQuery.query?.p as number,
    sort_by: urlQuery.query?.sort as number,
    filter_id: urlQuery.query?.filter as number,
    sort_desc: urlQuery.query?.desc as boolean,
  });

  return {
    props: { data, urlQuery, itemType },
  };
}

export default function Page({ data, urlQuery, itemType }: PageProps) {
  const [item, setItem] = useRecoilState(LibraryState.item);
  const [view, setView] = useRecoilState(LibraryState.view);
  const [favorites, setFavorites] = useRecoilState(LibraryState.favorites);
  const [filter, setFilter] = useRecoilState(LibraryState.filter);
  const [sort, setSort] = useRecoilState(LibraryState.sort);
  const [sortDesc, setSortDesc] = useRecoilState(LibraryState.sortDesc);
  const display = useRecoilValue(LibraryState.display);

  const router = useRouter();

  // TODO: replace with useQuery with initialData?
  const [items, setItems] = useState(data);

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

  const pageHrefTemplate = useMemo(
    () => urlstring(router.asPath, { p: '${page}' }, { encode: false }),
    [router.query]
  );

  return (
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
      bottomZone={useMemo(
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
      {display === 'card' && (
        <CardView
          hrefTemplate={pageHrefTemplate}
          activePage={urlQuery.query?.p}
          items={items.items}
          itemRender={GalleryCard}
          totalItemCount={items.count}
          pagination={!!items.count}
          bottomPagination={!!items.count}></CardView>
      )}
      {display === 'list' && (
        <ListView
          hrefTemplate={pageHrefTemplate}
          items={items.items}
          activePage={urlQuery.query?.p}
          itemRender={GalleryCard}
          totalItemCount={items.count}
          pagination={!!items.count}
          bottomPagination={!!items.count}></ListView>
      )}
    </PageLayout>
  );
}
