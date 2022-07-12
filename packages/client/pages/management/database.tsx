import { NextPageContext } from 'next';
import { useRouter } from 'next/router';
import { Container, Segment, Tab } from 'semantic-ui-react';

import { ServiceType } from '../../services/constants';
import ManagementPage from './index';

interface PageProps {}

const limit = 100;

export async function getServerSideProps(context: NextPageContext) {
  const server = global.app.service.get(ServiceType.Server);

  return {
    props: {},
  };
}

const panes = [
  { menuItem: 'Backup', render: () => <Tab.Pane>Backups here</Tab.Pane> },
  {
    menuItem: 'Refresh',
    render: () => <Tab.Pane>Refresh database command</Tab.Pane>,
  },
  {
    menuItem: 'Indexing',
    render: () => <Tab.Pane>indexing stuff here?</Tab.Pane>,
  },
];

export default function Page({}: PageProps) {
  const router = useRouter();

  return (
    <ManagementPage>
      <Container centered clearing as={Segment} basic>
        <Tab
          menu={{ fluid: true, vertical: true, tabular: true }}
          panes={panes}
        />
      </Container>
    </ManagementPage>
  );
}
