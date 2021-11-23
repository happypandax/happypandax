import { NextPageContext } from 'next';
import { useRouter } from 'next/router';
import { useCallback, useMemo } from 'react';
import {
  Button,
  Container,
  Grid,
  Icon,
  Segment,
  Statistic,
} from 'semantic-ui-react';

import FilterCard, { filterCardDataFields } from '../../components/item/Filter';
import { ItemSearch } from '../../components/Search';
import { PaginatedView } from '../../components/view/index';
import { ItemSort, ItemType } from '../../misc/enums';
import t from '../../misc/lang';
import { ServerFilter } from '../../misc/types';
import { urlparse, urlstring } from '../../misc/utility';
import { ServiceType } from '../../services/constants';
import ServerService from '../../services/server';
import DirectoryPage from './';

interface PageProps {
  data: Unwrap<ServerService['items']>;
  page: number;
}

const limit = 100;

export async function getServerSideProps(context: NextPageContext) {
  const server = global.app.service.get(ServiceType.Server);

  const urlQuery = urlparse(context.resolvedUrl);

  let page = 1;
  if (urlQuery.query?.p && !isNaN(parseInt(urlQuery.query?.p as string, 10))) {
    page = parseInt(urlQuery.query?.p as string, 10);
  }

  const data = await server.search_items<ServerFilter>({
    item_type: ItemType.Filter,
    search_query: urlQuery.query?.q?.toString() as string,
    fields: filterCardDataFields,
    limit,
    offset: (page - 1) * limit,
    sort_options: {
      by: ItemSort.FilterName,
    },
  });

  return {
    props: {
      data,
      page,
    },
  };
}

export default function Page({ page, data }: PageProps) {
  const router = useRouter();

  const urlQuery = urlparse(router.asPath);

  const pageHrefTemplate = useMemo(
    () => urlstring(router.asPath, { p: '${page}' }, { encode: false }),
    [router.query]
  );

  return (
    <DirectoryPage>
      <Container centered clearing as={Segment} basic>
        <Button size="small" floated="right" color="green" compact>
          <Icon name="plus" /> {t`New`}
        </Button>
        <Button size="small" floated="right" compact>
          <Icon name="refresh" /> {t`Update`}
        </Button>
        <Statistic horizontal color="grey">
          <Statistic.Value>{data.count}</Statistic.Value>
          <Statistic.Label>{t`Filters`}</Statistic.Label>
        </Statistic>
        <ItemSearch
          stateKey="filters"
          defaultValue={urlQuery.query?.q as string}
          fluid
          debounce={200}
          onSearch={useCallback(
            (q) => {
              router.push(urlstring({ q: q, p: 1 }));
            },
            [router]
          )}
          transparent={false}
          showSuggestion={false}
          dynamic
          size="tiny"
        />
      </Container>
      <PaginatedView
        itemCount={data.items.length}
        itemsPerPage={limit}
        size="tiny"
        activePage={page}
        hrefTemplate={pageHrefTemplate}
        pagination={limit < data.count}
        bottomPagination
        totalItemCount={data.count}>
        <Grid doubling centered stackable columns="3">
          {data.items.map((i: ServerFilter) => (
            <Grid.Column key={i.id}>
              <FilterCard data={i} centered fluid />
            </Grid.Column>
          ))}
        </Grid>
      </PaginatedView>
    </DirectoryPage>
  );
}
