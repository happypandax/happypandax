import { GetServerSidePropsResult, NextPageContext, Redirect } from 'next';
import { Divider } from 'semantic-ui-react';

import {
  CollectionHeaderData,
  collectionHeaderDataFields,
  CollectionItemHeader,
} from '../../../components/layout/CollectionLayout';
import { ImageSize, ItemType } from '../../../misc/enums';
import { ServerCollection } from '../../../misc/types';
import { urlparse } from '../../../misc/utility';
import { ServiceType } from '../../../services/constants';
import LibraryPage, {
  getServerSideProps as libraryServerSideProps,
  libraryArgs,
  PageProps as LibraryPageProps,
} from '../../library';

const stateKey = 'collection_page';

interface PageProps extends LibraryPageProps {
  collection: CollectionHeaderData &
  DeepPick<ServerCollection, 'gallery_count'>;
}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = global.app.service.get(ServiceType.Server);

  let redirect: Redirect;
  let r: Unwrap<ReturnType<typeof libraryServerSideProps>>;

  const item_id = parseInt(context.query.id as string);

  if (isNaN(item_id)) {
    redirect = { permanent: false, destination: '/library' };
  }

  let collection: PageProps['collection'];

  if (!redirect) {
    const urlQuery = urlparse(context.resolvedUrl);

    const group = server.create_group_call();

    server
      .item<ServerCollection>(
        {
          item_id,
          item_type: ItemType.Collection,
          fields: collectionHeaderDataFields.concat(['gallery_count']),
          profile_options: {
            size: ImageSize.Big,
          },
        },
        group
      )
      .then((r) => {
        collection = r;
      });

    await group.call();

    let page = urlQuery.query?.p
      ? parseInt(urlQuery.query?.p as string, 10)
      : 1;

    if (isNaN(page)) {
      page = 1;
    }

    const largs = libraryArgs({
      ctx: context,
      urlQuery,
      itemType: ItemType.Collection,
      relatedType: ItemType.Gallery,
      itemId: collection?.id,
      stateKey,
      page,
    });

    r = await libraryServerSideProps(context, {
      ...largs,
    });
  }

  return {
    redirect,
    ...r,
    props: {
      ...r?.props,
      itemType: ItemType.Gallery,
      collection,
    },
  };
}

export default function Page({ collection, ...props }: PageProps) {
  return (
    <LibraryPage
      {...props}
      hideViewItems
      stateKey={stateKey}
      libraryArgs={{
        itemId: collection?.id,
        itemType: ItemType.Collection,
        relatedType: ItemType.Gallery,
      }}>
      <CollectionItemHeader data={collection} />
      <Divider horizontal hidden />
    </LibraryPage>
  );
}
