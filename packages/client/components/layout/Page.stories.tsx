import MainMenu from '../Menu';
import PageLayout from './Page';

export default {
  title: 'Layout/Page',
};

export const Page = () => <PageLayout menu={<MainMenu />}></PageLayout>;
