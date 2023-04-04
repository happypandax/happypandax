import MainMenu from '../Menu';
import { Visible } from '../misc';
import {
  ClearFilterButton,
  FilterButtonInput,
  OnlyFavoritesButton,
  SortButtonInput,
  SortOrderButton,
} from './GalleryLayout';
import PageLayout from './Page';

export default {
  title: 'Layout/Page',
};

export const Layout = () => <PageLayout menu={<MainMenu />}></PageLayout>;

export const Buttons = () => (
  <PageLayout
    bottomZone={
      <>
        <OnlyFavoritesButton active={true} setActive={undefined} />
        <div className="medium-margin-top">
          <div className="pos-relative">
            <FilterButtonInput active={undefined} setActive={undefined} />
            <Visible visible={true}>
              <ClearFilterButton
                onClick={() => {}}
                className="accented_button"
                size="mini"
              />
            </Visible>
          </div>
        </div>
        <div className="medium-margin-top mb-auto">
          <div className="pos-relative">
            <SortButtonInput active={undefined} setActive={undefined} />
            <Visible visible={true}>
              <SortOrderButton
                onClick={() => {}}
                className="accented_button"
                size="mini"
              />
            </Visible>
          </div>
        </div>
      </>
    }
  ></PageLayout>
);
