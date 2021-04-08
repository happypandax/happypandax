import { Card, Icon } from 'semantic-ui-react';
import { PageTitle } from '../components/Misc';
import t from '../misc/lang';

export default function Page() {
  return (
    <>
      <PageTitle title={t`Library`} />
      <Card>
        <Card.Content>
          <Card.Header>Test</Card.Header>
          <Card.Meta>
            <span className="date">Joined in 2015</span>
          </Card.Meta>
          <Card.Description>Test Test Test</Card.Description>
        </Card.Content>
        <Card.Content extra>
          <a>
            <Icon name="user" />
            Test
          </a>
        </Card.Content>
      </Card>
    </>
  );
}
