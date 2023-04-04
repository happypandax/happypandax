import classNames from 'classnames';
import Link from 'next/link';
import { Card, Icon, Image, Label, Segment } from 'semantic-ui-react';

import { DataContext } from '../../client/context';
import { useSetupDataState } from '../../client/hooks/item';
import t from '../../client/lang';
import { getLibraryQuery } from '../../client/utility';
import { ItemType, ViewType } from '../../shared/enums';
import { FieldPath, ServerArtist } from '../../shared/types';
import { urlstring } from '../../shared/utility';
import { FavoriteLabel, FolllowLabel } from '../dataview/Common';

export type ArtistCardLabelData = DeepPick<
  ServerArtist,
  | 'id'
  | 'info'
  | 'preferred_name.name'
  | 'metatags.favorite'
  | 'metatags.follow'
  | 'circles.[].id'
  | 'circles.[].name'
>;

export const artistCardLabelDataFields: FieldPath<ServerArtist>[] = [
  'info',
  'preferred_name.name',
  'metatags.favorite',
  'metatags.follow',
  'circles.id',
  'circles.name',
];

export default function ArtistCardLabel({
  data: initialData,
  ...props
}: {
  data: ArtistCardLabelData;
} & React.ComponentProps<typeof Card>) {
  const { data, dataContext } = useSetupDataState({
    initialData,
    itemType: ItemType.Artist,
  });

  return (
    <DataContext.Provider value={dataContext}>
      <Card
        {...props}
        as={Segment}
        size="tiny"
        color="blue"
        className={classNames('default-card', props.className)}
      >
        <Card.Content>
          <Image
            floated="left"
            size="mini"
            circular
            src="/img/default.png"
            alt="default"
          />
          <Card.Header>
            {data?.preferred_name?.name}
            <Label size="mini" className="right">
              {t`ID`}
              <Label.Detail>{data.id}</Label.Detail>
            </Label>
            <FolllowLabel
              size="big"
              title={t`Follow status`}
              className="right"
              defaultRating={data?.metatags?.follow ? 1 : 0}
            />
            <FavoriteLabel
              icon="heart"
              size="big"
              className="right"
              defaultRating={data?.metatags?.favorite ? 1 : 0}
            />
          </Card.Header>
          <Card.Meta>
            <Label.Group size="small">
              {data?.circles?.map?.((c) => (
                <Label color="teal" key={c?.id}>
                  <Icon name="group" /> {c.name}
                </Label>
              ))}
            </Label.Group>
          </Card.Meta>
          <Card.Meta>{data.info || t`No description`}</Card.Meta>
          <Card.Meta className="clearfix">
            <Link
              href={urlstring('/library', {
                ...getLibraryQuery({
                  query: `artist:"${data.preferred_name.name}"`,
                  view: ViewType.All,
                  favorites: false,
                  filter: 0,
                }),
              })}
              passHref
              legacyBehavior
            >
              <Label
                size="small"
                empty
                className="right"
                icon="grid layout"
                title={t`Show galleries`}
                as="a"
              />
            </Link>
          </Card.Meta>
        </Card.Content>
      </Card>
    </DataContext.Provider>
  );
}
