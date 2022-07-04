import AddPage from '../';
import { PageTitle } from '../../../components/misc/index';
import t from '../../../misc/lang';
import { Header } from './';

export default function Page() {
  return (
    <AddPage>
      <PageTitle title={t`Add collection`} />
      <Header active="collection" />
    </AddPage>
  );
}
