import { GetServerSidePropsResult, NextPageContext } from 'next';
import { useMemo } from 'react';
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
import t from '../misc/lang';
import { LibraryState } from '../state';

interface PageProps {
  data;
}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  return {
    props: {},
  };
}

export default function Page() {
  const [item, setItem] = useRecoilState(LibraryState.item);
  const [view, setView] = useRecoilState(LibraryState.view);
  const [favorites, setFavorites] = useRecoilState(LibraryState.favorites);
  const [filter, setFilter] = useRecoilState(LibraryState.filter);
  const [sort, setSort] = useRecoilState(LibraryState.sort);
  const display = useRecoilValue(LibraryState.display);

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
          items={[]}
          itemRender={GalleryCard}
          totalItemCount={0}
          pagination
          bottomPagination></CardView>
      )}
      {display === 'list' && (
        <ListView
          items={[]}
          itemRender={GalleryCard}
          totalItemCount={0}
          pagination
          bottomPagination></ListView>
      )}
    </PageLayout>
  );
}
