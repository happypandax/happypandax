import { Container, Segment } from 'semantic-ui-react';

import t from '../../client/lang';
import { PageTitle } from '../../components/misc';
import { MetadataQueue } from '../../components/queue/Metadata';
import ManagementPage from './';

interface PageProps {}

export default function Page({}: PageProps) {
  return (
    <ManagementPage>
      <PageTitle title={t`Metadata`} />
      <Container centered clearing as={Segment} basic>
        <MetadataQueue logDefaultVisible logExpanded />
      </Container>
    </ManagementPage>
  );
}
