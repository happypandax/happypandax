import { JsonMap } from 'happypandax-client';
import { GetServerSidePropsResult, NextPageContext } from 'next';
import { useMemo, useState } from 'react';
import { useRecoilState, useRecoilValue } from 'recoil';

import GalleryCard from '../components/Gallery';
import {
  ClearFilterButton,
  FilterButtonInput,
  OnlyFavoritesButton,
  SortButtonInput,
  ViewButtons,
} from '../components/layout/ItemLayout';
import PageLayout from '../components/layout/Page';
import MainMenu, { MenuItem } from '../components/Menu';
import { PageTitle, Visible } from '../components/Misc';
import CardView from '../components/view/CardView';
import ListView from '../components/view/ListView';
import { ItemType } from '../misc/enums';
import t from '../misc/lang';
import { ServiceType } from '../services/constants';
import { LibraryState } from '../state';

interface PageProps {
  data: JsonMap[];
}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = global.app.service.get(ServiceType.Server);

  const data = await server.library({ item_type: ItemType.Gallery });
  return {
    props: { data },
  };
}

export default function Page({ data }: PageProps) {
  const [item, setItem] = useRecoilState(LibraryState.item);
  const [view, setView] = useRecoilState(LibraryState.view);
  const [favorites, setFavorites] = useRecoilState(LibraryState.favorites);
  const [filter, setFilter] = useRecoilState(LibraryState.filter);
  const [sort, setSort] = useRecoilState(LibraryState.sort);
  const display = useRecoilValue(LibraryState.display);

  // TODO: replace with useQuery with initialData
  const [items, setItems] = useState(data);

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
                <Visible visible={filter !== null}>
                  <ClearFilterButton
                    onClick={() => {
                      setFilter(null);
                    }}
                    className="clear_filter"
                    size="mini"
                  />
                </Visible>
              </div>
            </div>
            <div className="medium-margin-top mb-auto">
              <SortButtonInput active={sort} setActive={setSort} />
            </div>
          </>
        ),
        [favorites, filter, sort]
      )}>
      <PageTitle title={t`Library`} />
      {display === 'card' && (
        <CardView
          items={items}
          itemRender={GalleryCard}
          totalItemCount={items.length}
          pagination={!!items.length}
          bottomPagination={!!items.length}></CardView>
      )}
      {display === 'list' && (
        <ListView
          items={items}
          itemRender={GalleryCard}
          totalItemCount={items.length}
          pagination={!!items.length}
          bottomPagination={!!items.length}></ListView>
      )}
    </PageLayout>
  );
}
