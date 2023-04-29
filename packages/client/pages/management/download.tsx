import { Container, Segment } from 'semantic-ui-react';

import t from '../../client/lang';
import { PageTitle } from '../../components/misc';
import { DownloadQueue } from '../../components/queue/Download';
import ManagementPage from './';

interface PageProps {}

export default function Page({}: PageProps) {
  return (
    <ManagementPage>
      <PageTitle title={t`Download`} />
      <Container centered clearing as={Segment} basic>
        <DownloadQueue logDefaultVisible logExpanded />
      </Container>
    </ManagementPage>
  );
}
