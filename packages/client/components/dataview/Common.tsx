import classNames from 'classnames';
import React, { useCallback, useState } from 'react';
import { useRecoilValue } from 'recoil';
import { Header, Icon, Label, List, Segment, Table } from 'semantic-ui-react';

import { ItemActions } from '../../client/actions/item';
import { useUpdateDataState } from '../../client/hooks/item';
import t from '../../client/lang';
import { dateFromTimestamp } from '../../client/utility';
import {
  FieldPath,
  ServerCollection,
  ServerGallery,
  ServerItemTaggable,
  ServerItemWithName,
  ServerItemWithUrls,
  ServerMetaTags,
  ServerNamespaceTag,
} from '../../shared/types';
import { AppState } from '../../state';
import Rating from '../misc/Rating';
import styles from './Common.module.css';

export function LanguageLabel({
  children,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label color="blue" basic {...props}>
      <Icon className="globe africa" />
      {children}
    </Label>
  );
}

export function ReadCountLabel({
  children,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Timed read`} color="blue" basic {...props}>
      <Icon className="book open" />
      {children}
    </Label>
  );
}

export function PageCountLabel({
  children,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Page count`} color="blue" basic {...props}>
      <Icon name="clone outline" />
      {children}
    </Label>
  );
}

export function GalleryCountLabel({
  ...props
}: React.ComponentProps<typeof Label>) {
  return <PageCountLabel title={t`Gallery count`} {...props} />;
}

export function CategoryLabel({
  data: initialData,
  ...props
}: React.ComponentProps<typeof Label> & {
  data?: DeepPick<ServerGallery, 'id' | 'category.name'>;
}) {
  const { data } = useUpdateDataState(initialData);

  return (
    <Label {...props} title={t`Category`} color="black" basic>
      <Icon name="folder" />
      {data?.category?.name}
    </Label>
  );
}

export function StatusLabel({
  children,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Status`} color="blue" basic {...props}>
      <Icon name="calendar check" />
      {children}
    </Label>
  );
}

export function PageNumberLabel({
  children,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Page number`} color="black" {...props}>
      {children}
    </Label>
  );
}

export function GroupingNumberLabel({
  children,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Group number`} color="teal" basic {...props}>
      {children}
    </Label>
  );
}

export function DateLabel({
  timestamp,
  text,
  ...props
}: React.ComponentProps<typeof Label> & { text?: string; timestamp?: number }) {
  const [showRelative, setShowRelative] = useState(true);

  const date = dateFromTimestamp(timestamp, { relative: showRelative });

  return (
    <Label
      as="a"
      {...props}
      onClick={useCallback(() => setShowRelative(!showRelative), [
        showRelative,
      ])}>
      {text}
      <Label.Detail>{date ? date : t`Unknown`}</Label.Detail>
    </Label>
  );
}

export function DateAddedLabel({
  children,
  ...props
}: React.ComponentProps<typeof DateLabel>) {
  return <DateLabel {...props} text={t`Added`} title={t`Date added`} />;
}

export function LastReadLabel({
  children,
  ...props
}: React.ComponentProps<typeof DateLabel>) {
  return <DateLabel {...props} text={t`Last read`} title={t`Last read`} />;
}

export function LastUpdatedLabel({
  children,
  ...props
}: React.ComponentProps<typeof DateLabel>) {
  return <DateLabel {...props} text={t`Updated`} title={t`Last updated`} />;
}

export function DatePublishedLabel({
  children,
  data: initialData,
  ...props
}: React.ComponentProps<typeof Label> & {
  data?: DeepPick<ServerGallery, 'id' | 'pub_date'>;
}) {
  const { data } = useUpdateDataState(initialData);

  const date = dateFromTimestamp(data?.pub_date, {
    relative: false,
    format: 'PPP',
  });

  return <Header size="tiny">{date ? date : t`Unknown`}</Header>;
}

export function ArtistLabels({
  data: initialData,
}: {
  data?: DeepPick<
    ServerGallery,
    'id' | 'artists.[].preferred_name.name' | 'artists.[].id'
  >;
}) {
  const { data } = useUpdateDataState(initialData);

  return (
    <Label.Group color="blue">
      {data?.artists?.map?.((a) => (
        <Label key={a?.id}>
          <Icon name="user outline" /> {a?.preferred_name?.name}
        </Label>
      ))}
    </Label.Group>
  );
}

export function ParodyLabels({
  data: initialData,
}: {
  data?: DeepPick<
    ServerGallery,
    'id' | 'parodies.[].preferred_name.name' | 'parodies.[].id'
  >;
}) {
  const { data } = useUpdateDataState(initialData);

  return (
    <Label.Group color="violet">
      {data?.parodies?.map?.((a) => (
        <Label key={a?.id}>{a?.preferred_name?.name}</Label>
      ))}
    </Label.Group>
  );
}

export function CircleLabels({
  data: initialData,
}: {
  data?: DeepPick<ServerGallery, 'id' | 'artists' | 'circles'>;
}) {
  const { data } = useUpdateDataState(initialData);

  const artistCircles = data?.artists
    ?.flatMap?.((a) => a?.circles?.map?.((c) => c))
    ?.filter?.((c) => !data?.circles?.find?.((c2) => c2.id === c.id));

  return (
    <Label.Group>
      {data?.circles?.map?.((c) => (
        <Label color="teal" key={c?.id}>
          <Icon name="group" /> {c.name}
        </Label>
      ))}
      {artistCircles?.map?.((c) => (
        <Label key={c?.id} basic color="teal" className="border-dashed">
          <Icon name="group" /> {c?.name}
        </Label>
      ))}
    </Label.Group>
  );
}

export function GroupingLabel({
  data: initialData,
}: {
  data?: DeepPick<ServerGallery, 'id' | 'grouping.name'>;
}) {
  const { data } = useUpdateDataState(initialData);

  return (
    <Label basic>
      <Icon className="stream" /> {data?.grouping?.name}
    </Label>
  );
}

export function FavoriteLabel({
  onRate,
  onRating,
  className,
  size = 'massive',
  ...props
}: Omit<MakeOptional<React.ComponentProps<typeof Rating>, 'icon'>, 'size'> & {
  size?: React.ComponentProps<typeof Rating>['size'] | 'gigantic';
  onRating?: (rating: number) => void;
}) {
  const { data, setData, context } = useUpdateDataState<{
    id: number;
    metatags: PartialExcept<ServerMetaTags, 'favorite'>;
  }>();

  const onFav = useCallback(
    (e, d) => {
      e.preventDefault();

      if (context.editing) {
        throw Error('not implemented');
      } else {
        ItemActions.updateMetatags(
          [data],
          {
            item_type: context.type,
            item_id: data.id,
            metatags: { favorite: !!d.rating },
          },
          (d, mutated) => {
            if (mutated) {
              setData(d[0]);
            }
          }
        ).catch((err) => console.error(err));
      }

      onRating?.(d.rating);
    },
    [context.type, data, onRating]
  );

  return (
    <Rating
      className={classNames(
        { [styles.favorite_label]: size === 'gigantic' },
        className
      )}
      icon="heart"
      color="red"
      onRate={onRate ?? onFav}
      size={size === 'gigantic' ? 'massive' : size}
      rating={data?.metatags?.favorite ? 1 : undefined}
      {...props}
    />
  );
}

export function FolllowLabel({
  onRate,
  className,
  size = 'big',
  ...props
}: Omit<MakeOptional<React.ComponentProps<typeof Rating>, 'icon'>, 'size'> & {
  size?: React.ComponentProps<typeof Rating>['size'] | 'gigantic';
}) {
  const { data, setData, context } = useUpdateDataState<{
    id: number;
    metatags: PartialExcept<ServerMetaTags, 'follow'>;
  }>();

  // console.log(context.key, data);

  const onFav = useCallback(
    (e, d) => {
      if (context.editing) {
        throw Error('not implemented');
      } else {
        ItemActions.updateMetatags(
          [data],
          {
            item_type: context.type,
            item_id: data.id,
            metatags: { follow: d.rating!! },
          },
          (d, mutated) => {
            if (mutated) {
              setData(d[0]);
            }
          }
        ).catch((err) => console.error(err));
      }
    },
    [context.type, data]
  );

  return (
    <Rating
      className={classNames(
        { [styles.favorite_label]: size === 'gigantic' },
        className
      )}
      icon="thumbtack"
      title={t`Follow status`}
      color="blue"
      onRate={onRate ?? onFav}
      size={size === 'gigantic' ? 'massive' : size}
      rating={data?.metatags?.follow ? 1 : undefined}
      {...props}
    />
  );
}

export function RatingLabel({
  size = 'huge',
  onRating,
  defaultRating,
}: {
  defaultRating?: number;
  size?: React.ComponentProps<typeof Rating>['size'] | 'gigantic';
  onRating?: (rating: number) => void;
}) {
  const { data, setData, context } = useUpdateDataState<{
    id: number;
    rating: number;
  }>();

  return (
    <Rating
      icon="star"
      size={size}
      color="yellow"
      onRate={useCallback(
        (e, d) => {
          e.preventDefault();
          if (context.editing) {
            throw Error('not implemented');
          } else {
            ItemActions.updateItem(
              data.id,
              data,
              { item_type: context.type, item: { rating: d.rating } },
              (d, mutated) => {
                if (mutated) {
                  setData(d);
                }
              }
            ).catch((err) => console.error(err));

            onRating?.(d.rating);
          }
        },
        [context.type, data, onRating]
      )}
      rating={data?.rating}
      defaultRating={defaultRating}
      maxRating={10}
    />
  );
}

export function NamesTable({
  data: initialData,
  children,
  dataPrimaryKey,
  dataKey,
}: {
  data?: PartialExcept<ServerGallery, 'id'>;
  dataKey: FieldPath;
  dataPrimaryKey: FieldPath;
  children?: React.ReactNode;
}) {
  const { data } = useUpdateDataState(initialData);

  const names =
    dataPrimaryKey && data?.[dataPrimaryKey]
      ? data?.[dataKey]?.filter?.((n) => n?.id !== data?.[dataPrimaryKey]?.id)
      : data?.[dataKey];

  return (
    <Table basic="very" compact="very" verticalAlign="middle" stackable>
      <Table.Body>
        <Table.Row>
          <Table.Cell colspan="2" textAlign="center">
            {children}
            <Label size="tiny" className="float-right">
              {t`ID`}
              <Label.Detail>{data?.id}</Label.Detail>
            </Label>
            <div>
              <Header size="medium">{data?.[dataPrimaryKey]?.name}</Header>
            </div>
          </Table.Cell>
        </Table.Row>
        {names?.map?.((v) => (
          <Table.Row key={v.id ?? v.name} verticalAlign="middle">
            <Table.Cell collapsing>
              <LanguageLabel color={undefined} basic={false} size="tiny">
                {v?.language?.name}
              </LanguageLabel>
            </Table.Cell>
            <Table.Cell>
              <Header size="tiny" className="sub-text">
                {v.name}
              </Header>
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table>
  );
}

export function NameTable({
  children,
  data: initialData,
}: {
  children?: React.ReactNode;
  data?: PartialExcept<ServerItemWithName, 'id'>;
}) {
  const { data } = useUpdateDataState(initialData);

  return (
    <Table basic="very" compact="very" verticalAlign="middle" stackable>
      <Table.Body>
        <Table.Row>
          <Table.Cell colspan="2" textAlign="center">
            {children}
            <Label size="tiny" className="float-right">
              {t`ID`}
              <Label.Detail>{data?.id}</Label.Detail>
            </Label>
            <div>
              <Header size="medium">{data?.name}</Header>
            </div>
          </Table.Cell>
        </Table.Row>
      </Table.Body>
    </Table>
  );
}

export function UrlList({
  data: initialData,
}: {
  data?: PartialExcept<ServerItemWithUrls, 'id'>;
}) {
  const { data } = useUpdateDataState(initialData);

  return (
    <List size="small" relaxed>
      {data?.urls?.map?.((u) => (
        <List.Item key={u?.id}>
          <List.Icon name="external share" />
          <List.Content>
            <a href={u.name} target="_blank" rel="noreferrer">
              {u.name}
            </a>
          </List.Content>
        </List.Item>
      ))}
    </List>
  );
}

export function TagLabel({
  data,
}: {
  data: PartialExcept<ServerNamespaceTag, 'id'>;
}) {
  return (
    <Label
      basic={data?.metatags?.favorite}
      color={data?.metatags?.favorite ? 'red' : undefined}>
      {data?.tag?.name}
    </Label>
  );
}

export function TagsTable({
  data: initialData,
}: {
  data?: PartialExcept<ServerItemTaggable, 'id'>;
}) {
  const properties = useRecoilValue(AppState.properties);

  const { data } = useUpdateDataState(initialData);

  const freeTags: ServerNamespaceTag[] = [];
  const tags = {} as Record<string, ServerNamespaceTag[]>;

  data?.tags?.forEach?.((t) => {
    // TODO: query this value from server
    if (t?.namespace?.name === properties.special_namespace) {
      freeTags.push(t);
    } else {
      const l = tags[t?.namespace?.name] ?? [];
      tags[t?.namespace?.name] = [...l, t];
    }
  });

  return (
    <Table
      basic="very"
      compact="very"
      verticalAlign="middle"
      size="small"
      stackable>
      <Table.Body>
        {!!freeTags.length && (
          <Table.Row>
            <Table.Cell colspan="2">
              {freeTags
                .sort((a, b) => a?.tag.name?.localeCompare?.(b?.tag.name))
                .map((x) => (
                  <TagLabel key={x?.id} data={x} />
                ))}
            </Table.Cell>
          </Table.Row>
        )}
        {Object.entries(tags)
          .sort((a, b) => a[0]?.localeCompare?.(b[0]))
          .map(([ns, t]) => (
            <Table.Row key={ns} verticalAlign="middle">
              <Table.Cell collapsing className="sub-text">
                {ns}
              </Table.Cell>
              <Table.Cell>
                <Label.Group>
                  {t
                    .sort((a, b) => a?.tag.name?.localeCompare?.(b?.tag.name))
                    .map((x) => (
                      <TagLabel key={x?.id} data={x} />
                    ))}
                </Label.Group>
              </Table.Cell>
            </Table.Row>
          ))}
      </Table.Body>
    </Table>
  );
}

export function InfoSegment({
  data: initialData,
  className,
  fluid,
  ...props
}: {
  fluid?: boolean;
  data?: PartialExcept<ServerGallery | ServerCollection, 'id'>;
} & React.ComponentProps<typeof Segment>) {
  const { data } = useUpdateDataState(initialData);

  return (
    <Segment tertiary {...props} className={classNames({ fluid }, className)}>
      {data?.info}
    </Segment>
  );
}
