import classNames from 'classnames';
import { useRecoilValue } from 'recoil';
import { Divider, Header, Icon, Image, Segment } from 'semantic-ui-react';

import { DataContext } from '../../client/context';
import { useImage, useSetupDataState } from '../../client/hooks/item';
import { useBreakpoints } from '../../client/hooks/ui';
import t from '../../client/lang';
import { ItemType } from '../../shared/enums';
import { FieldPath, ServerCollection } from '../../shared/types';
import { AppState } from '../../state';
import {
  CategoryLabel,
  DateAddedLabel,
  DatePublishedLabel,
  FavoriteLabel,
  LastUpdatedLabel,
  NameTable,
  UrlList,
} from '../dataview/Common';
import { CollectionMenu } from '../item/Collection';
import {
  BlurryBackgroundContainer,
  LabelField,
  LabelFields,
} from './ItemLayout';
import styles from './ItemLayout.module.css';

export type CollectionHeaderData = DeepPick<
  ServerCollection,
  | 'id'
  | 'name'
  | 'profile'
  | 'info'
  | 'pub_date'
  | 'category.name'
  | 'metatags.favorite'
  | 'metatags.read'
  | 'metatags.inbox'
  | 'last_updated'
  | 'timestamp'
>;

export const collectionHeaderDataFields: FieldPath<ServerCollection>[] = [
  'name',
  'info',
  'category.name',
  'urls.name',
  'profile',
  'metatags.*',
  'last_updated',
  'timestamp',
  'pub_date',
];

export function CollectionItemHeader({
  data: initialData,
}: {
  data: CollectionHeaderData;
}) {
  const { isMobileMax } = useBreakpoints();

  const blur = useRecoilValue(AppState.blur);

  const { data, dataContext } = useSetupDataState({
    initialData,
    itemType: ItemType.Collection,
    key: 'header',
  });

  const { src } = useImage(data?.profile);

  return (
    <DataContext.Provider value={dataContext}>
      <BlurryBackgroundContainer data={data}>
        <Segment
          className={classNames('no-margins no-top-padding', {
            'no-right-padding': !isMobileMax,
          })}
        >
          <div
            className={classNames(styles.header_content, {
              [styles.column]: isMobileMax,
            })}
          >
            <div className={classNames(styles.cover_collection)}>
              <Image
                centered
                rounded
                className={classNames({ blur })}
                alt="cover image"
                id={styles.cover}
                src={src}
                width={data?.profile?.size?.[0]}
                height={data?.profile?.size?.[1]}
              />
            </div>
            <Segment className="no-margins no-right-padding" basic>
              <NameTable>
                <FavoriteLabel
                  defaultRating={data?.metatags?.favorite ? 1 : 0}
                  size="gigantic"
                  className="float-left"
                />
                <CollectionMenu
                  trigger={
                    <Icon
                      link
                      size="large"
                      className="float-right"
                      name="ellipsis vertical"
                    />
                  }
                />
              </NameTable>
              <Header textAlign="center">
                <LastUpdatedLabel timestamp={data?.last_updated} />
                <DateAddedLabel timestamp={data?.timestamp} />
              </Header>
              <Divider hidden className="small" />
              <LabelFields>
                <LabelField label={t`Category`}>
                  <CategoryLabel />
                </LabelField>

                <LabelField label={t`Published`}>
                  <DatePublishedLabel />
                </LabelField>
                <LabelField label={t`External links`} padded={false}>
                  <UrlList />
                </LabelField>
              </LabelFields>
            </Segment>
          </div>
        </Segment>
      </BlurryBackgroundContainer>
    </DataContext.Provider>
  );
}
