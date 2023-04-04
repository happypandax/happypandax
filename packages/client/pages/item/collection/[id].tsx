import { GetServerSidePropsResult, NextPageContext } from 'next';
import { Divider } from 'semantic-ui-react';

import {
  CollectionHeaderData,
  collectionHeaderDataFields,
  CollectionItemHeader,
} from '../../../components/layout/CollectionLayout';
import { ServiceType } from '../../../server/constants';
import { ImageSize, ItemType } from '../../../shared/enums';
import { ServerErrorCode } from '../../../shared/error';
import { ServerCollection } from '../../../shared/types';
import { urlparse } from '../../../shared/utility';
import LibraryPage, {
  getLibraryArgs,
  getServerSideProps as libraryServerSideProps,
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
  const server = await global.app.service
    .get(ServiceType.Server)
    .context(context);

  let redirectUrl = '/library';
  let redirect = false;
  let r: Unwrap<ReturnType<typeof libraryServerSideProps>>;

  const item_id = parseInt(context.query.id as string);

  if (isNaN(item_id)) {
    redirect = true;
  }

  let collection: PageProps['collection'] = null;

  const urlQuery = urlparse(context.resolvedUrl);

  if (!redirect) {
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

    await group.call({ throw_error: false });

    try {
      await group.throw_errors();
    } catch (e) {
      if (e?.code === ServerErrorCode.DatabaseItemNotFoundError) {
        redirect = true;
        redirectUrl = '/404';
      } else {
        throw e;
      }
    }

    if (!redirect) {
      let page = urlQuery.query?.p
        ? parseInt(urlQuery.query?.p as string, 10)
        : 1;

      if (isNaN(page)) {
        page = 1;
      }

      const largs = getLibraryArgs({
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
  }

  return {
    redirect: redirect
      ? { permanent: false, destination: redirectUrl }
      : undefined,
    ...r,
    props: {
      ...r?.props,
      urlQuery,
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
      }}
    >
      <CollectionItemHeader data={collection} />
      <Divider horizontal hidden />
    </LibraryPage>
  );
}
