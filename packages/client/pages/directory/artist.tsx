import { NextPageContext } from 'next';
import { useRouter } from 'next/router';
import { useCallback, useMemo } from 'react';
import { Grid, Segment, Statistic } from 'semantic-ui-react';

import ArtistCardLabel, {
  artistCardLabelDataFields,
} from '../../components/item/Artist';
import { ItemSearch } from '../../components/Search';
import { PaginatedView } from '../../components/view/index';
import { ItemSort, ItemType } from '../../misc/enums';
import t from '../../misc/lang';
import { ServerArtist } from '../../misc/types';
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

  const data = await server.search_items<ServerArtist>({
    item_type: ItemType.Artist,
    search_query: urlQuery.query?.q?.toString() as string,
    fields: artistCardLabelDataFields,
    limit,
    offset: (page - 1) * limit,
    sort_options: {
      by: ItemSort.ArtistName,
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
      <Segment clearing basic>
        <Statistic horizontal color="grey">
          <Statistic.Value>{data.count}</Statistic.Value>
          <Statistic.Label>{t`Artists`}</Statistic.Label>
        </Statistic>
        <ItemSearch
          stateKey="artists"
          defaultValue={urlQuery.query?.q as string}
          fluid
          debounce={200}
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
          {data.items.map((i: ServerArtist) => (
            <Grid.Column key={i.id}>
              <ArtistCardLabel data={i} centered fluid />
            </Grid.Column>
          ))}
        </Grid>
      </PaginatedView>
    </DirectoryPage>
  );
}
