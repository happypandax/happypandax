import { NextPageContext } from 'next';
import { useRouter } from 'next/router';
import { useCallback } from 'react';
import { Button, Card, Icon, Segment, Statistic } from 'semantic-ui-react';

import FilterCard, { filterCardDataFields } from '../../components/item/Filter';
import { ItemSearch } from '../../components/Search';
import { ItemSort, ItemType } from '../../misc/enums';
import t from '../../misc/lang';
import { ServerFilter } from '../../misc/types';
import { urlparse, urlstring } from '../../misc/utility';
import { ServiceType } from '../../services/constants';
import ServerService from '../../services/server';
import DirectoryPage from './';

interface PageProps {
  data: Unwrap<ServerService['items']>;
}

export async function getServerSideProps(context: NextPageContext) {
  const server = global.app.service.get(ServiceType.Server);

  const urlQuery = urlparse(context.resolvedUrl);

  const data = await server.search_items<ServerFilter>({
    item_type: ItemType.Filter,
    search_query: urlQuery.query?.q as string,
    fields: filterCardDataFields,
    sort_options: {
      by: ItemSort.FilterName,
    },
  });

  console.log(data);

  return {
    props: {
      data,
    },
  };
}
export default function Page({ data }: PageProps) {
  const router = useRouter();

  const urlQuery = urlparse(router.asPath);

  return (
    <DirectoryPage>
      <Segment clearing basic>
        <Button size="small" floated="right" color="green" compact>
          <Icon name="plus" /> {t`New`}
        </Button>
        <Button size="small" floated="right" compact>
          <Icon name="refresh" /> {t`Update`}
        </Button>
        <Statistic horizontal color="blue">
          <Statistic.Value>{data.count}</Statistic.Value>
          <Statistic.Label>{t`Filters`}</Statistic.Label>
        </Statistic>
        <ItemSearch
          stateKey="filters"
          defaultValue={urlQuery.query?.q as string}
          fluid
          onSearch={useCallback(
            (q) => {
              router.push(urlstring({ q: q }));
            },
            [router]
          )}
          transparent={false}
          showSuggestion={false}
          dynamic
          size="tiny"
        />
      </Segment>
      <Card.Group doubling centered stackable>
        {data.items.map((i: ServerFilter) => (
          <FilterCard key={i.id} data={i} />
        ))}
      </Card.Group>
    </DirectoryPage>
  );
}
