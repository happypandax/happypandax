import { NextPageContext } from 'next';
import { useRouter } from 'next/router';
import { useCallback, useMemo } from 'react';
import { Container, Grid, Segment, Statistic } from 'semantic-ui-react';

import t from '../../client/lang';
import CircleCardLabel, {
  circleCardLabelDataFields,
} from '../../components/item/Circle';
import { ItemSearch } from '../../components/Search';
import { PaginatedView } from '../../components/view/index';
import { ServiceType } from '../../server/constants';
import ServerService from '../../services/server';
import { ItemSort, ItemType } from '../../shared/enums';
import { ServerCircle } from '../../shared/types';
import { urlparse, urlstring } from '../../shared/utility';
import DirectoryPage from './';

interface PageProps {
  data: Unwrap<ServerService['items']>;
  page: number;
}

const limit = 100;

export async function getServerSideProps(context: NextPageContext) {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context(context);

  const urlQuery = urlparse(context.resolvedUrl);

  let page = 1;
  if (urlQuery.query?.p && !isNaN(parseInt(urlQuery.query?.p as string, 10))) {
    page = parseInt(urlQuery.query?.p as string, 10);
  }

  const data = await server.search_items<ServerCircle>({
    item_type: ItemType.Circle,
    search_query: urlQuery.query?.q?.toString() as string,
    fields: circleCardLabelDataFields,
    limit,
    offset: (page - 1) * limit,
    sort_options: {
      by: ItemSort.CircleName,
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
      <Container as={Segment} centered clearing basic>
        <Statistic horizontal color="grey">
          <Statistic.Value>{data.count}</Statistic.Value>
          <Statistic.Label>{t`Circles`}</Statistic.Label>
        </Statistic>
        <ItemSearch
          stateKey="circles"
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
        totalItemCount={data.count}
      >
        <Grid doubling centered stackable columns="3">
          {data.items.map((i: ServerCircle) => (
            <Grid.Column key={i.id}>
              <CircleCardLabel data={i} centered fluid />
            </Grid.Column>
          ))}
        </Grid>
      </PaginatedView>
    </DirectoryPage>
  );
}
